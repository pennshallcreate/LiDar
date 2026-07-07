"""
Serial driver for the LDRobot LD06 / LD19 2D LiDAR: reads the UART packet
stream, validates each packet's CRC8, decodes angle/distance/intensity,
converts to Cartesian, and buffers one LiDAR revolution at a time.

Adapted from PiLiDAR's lib/lidar_driver.py
(https://github.com/PiLiDAR/PiLiDAR), (c) Philip Gutjahr, CC BY-NC-SA 4.0
-- trimmed to drop the visualization hook and the Windows/MCU serial
branches (this build only ever talks to /dev/ttyS0 or a USB-serial
adapter on Linux).

Packet layout (48 bytes total, big-endian multi-byte fields), per the
LD06/LD19 development manual:
  byte 0      : start byte, always 0x54
  byte 1      : data-length byte (low 5 bits = 12 points/packet)
  bytes 2-3   : rotational speed (deg/s)
  bytes 4-5   : start angle (0.01 deg units)
  bytes 6-41  : 12 points x (2 bytes distance_mm, 1 byte intensity)
  bytes 42-43 : end angle (0.01 deg units)
  bytes 44-45 : timestamp (ms, wraps at 30000)
  byte 46     : CRC8 checksum over bytes 0-45
"""

import numpy as np
import serial

from platform_utils import init_serial


class Lidar:
    def __init__(self, config):
        self.sampling_rate = config.get("LIDAR", config.DEVICE, "SAMPLING_RATE")
        self.offset = config.get("LIDAR", config.DEVICE, "OFFSET")
        self.crc_table = config.crc_table
        self.verbose = False

        self.start_byte = config.get("LIDAR", "protocol", "start_byte")
        self.dlength_byte = config.get("LIDAR", "protocol", "dlength_byte")
        self.dlength = config.get("LIDAR", "protocol", "dlength")           # 12 points/packet
        self.package_len = config.get("LIDAR", "protocol", "package_len")  # 47 bytes after start+dlength byte... see read()
        self.deg2rad = np.pi / 180

        self.serial_connection = init_serial(port=config.PORT, baudrate=config.BAUDRATE)

        self.byte_array = bytearray()
        self.dtype = np.float32

        self.out_len = config.get("LIDAR", config.DEVICE, "OUT_LEN")  # packages per buffered revolution

        # preallocated per-packet scratch
        self.timestamp = 0
        self.speed = 0.0
        self.angle_package = np.zeros(self.dlength)
        self.distance_package = np.zeros(self.dlength)
        self.luminance_package = np.zeros(self.dlength)

        # preallocated per-revolution output
        self.out_i = 0
        self.points_2d = np.empty((self.out_len * self.dlength, 3), dtype=self.dtype)  # [x, y, intensity]

        self.z_angle = None          # set externally by the stepper each revolution
        self.z_angles = []           # recorded azimuth angle per revolution
        self.cartesian_list = []     # recorded points_2d snapshot per revolution

        # motor-speed PWM (LD06/LD19 have a "MOTOCTL" pin for closed-loop-ish speed control)
        pwm_cfg = config.get("LIDAR", "PWM")
        if pwm_cfg.get("ENABLE"):
            from platform_utils import init_pwm_Pi
            self.pwm = init_pwm_Pi(pwm_channel=pwm_cfg["CHANNEL"], frequency=pwm_cfg["FREQ"])
            self.pwm_coeffs = config.get("LIDAR", config.DEVICE, "PWM_COEFFS")
            self.target_speed = config.get("LIDAR", "TARGET_SPEED")
            self.pwm_dc = self.pwm_from_speed(self.target_speed)
            self.pwm.start(self.pwm_dc * 100)
        else:
            self.pwm = None

    def update_pwm_dc(self, pwm_dc):
        self.pwm_dc = max(0.0, min(1.0, pwm_dc))
        self.pwm.change_duty_cycle(self.pwm_dc * 100)
        return self.pwm_dc

    def update_speed(self, target_speed):
        self.target_speed = target_speed
        return self.update_pwm_dc(self.pwm_from_speed(target_speed))

    def speed_from_pwm(self, pwm):
        m, b = self.pwm_coeffs
        return m * pwm + b

    def pwm_from_speed(self, speed):
        m, b = self.pwm_coeffs
        return (speed - b) / m

    def close(self):
        if self.pwm is not None:
            self.pwm.stop()
        self.serial_connection.close()

    def read_loop(self, callback=None, max_packages=None):
        """Read packets until max_packages is hit (or forever if None).
        Every `out_len` packages, calls `callback()` (expected to advance
        the turntable one step and update self.z_angle), then snapshots
        the buffered revolution into cartesian_list/z_angles."""
        loop_count = 0
        while self.serial_connection.is_open and (max_packages is None or loop_count <= max_packages):
            try:
                if self.out_i == self.out_len:
                    if callback is not None:
                        callback()
                    self.z_angles.append(self.z_angle)
                    self.cartesian_list.append(np.copy(self.points_2d))
                    self.out_i = 0

                self._read_packet()
            except serial.SerialException:
                print("[ERROR] SerialException, stopping read loop.")
                break

            self.out_i += 1
            loop_count += 1

    def _read_packet(self):
        while self.serial_connection.is_open:
            data_byte = self.serial_connection.read()
            if data_byte == self.start_byte:
                next_byte = self.serial_connection.read()
                if next_byte == self.dlength_byte:
                    self.byte_array = self.serial_connection.read(self.package_len - 2)
                    self.byte_array = self.start_byte + self.dlength_byte + self.byte_array
                    break
                continue

        if len(self.byte_array) != self.package_len:
            if self.verbose:
                print("[WARNING] incomplete package:", self.byte_array)
            self.byte_array = bytearray()
            return

        if not self._check_crc8(self.byte_array):
            if self.verbose:
                print("[WARNING] CRC mismatch, dropping package")
            self.byte_array = bytearray()
            return

        self._decode(self.byte_array)
        x, y = self.polar2cartesian(self.angle_package, self.distance_package, self.offset)
        points_package = np.column_stack((x, y, self.luminance_package)).astype(self.dtype)

        self.points_2d[self.out_i * self.dlength:(self.out_i + 1) * self.dlength] = points_package
        self.byte_array = bytearray()

    def _decode(self, byte_array):
        self.speed = int.from_bytes(byte_array[2:4][::-1], "big") / 360  # rev/s
        fsa = float(int.from_bytes(byte_array[4:6][::-1], "big")) / 100  # start angle, deg
        lsa = float(int.from_bytes(byte_array[42:44][::-1], "big")) / 100  # end angle, deg
        self.timestamp = int.from_bytes(byte_array[44:46][::-1], "big")

        angle_step = ((lsa - fsa) if lsa - fsa > 0 else (lsa + 360 - fsa)) / (self.dlength - 1)

        for i, byte_i in enumerate(range(0, 3 * self.dlength, 3)):
            self.angle_package[i] = ((angle_step * i + fsa) % 360) * self.deg2rad
            self.distance_package[i] = int.from_bytes(byte_array[6 + byte_i:8 + byte_i][::-1], "big")  # mm
            self.luminance_package[i] = byte_array[8 + byte_i]

    @staticmethod
    def polar2cartesian(angles, distances, offset):
        angles = np.asarray(angles) + offset
        x = distances * -np.cos(angles)
        y = distances * np.sin(angles)
        return x, y

    def _check_crc8(self, data):
        payload, crc = data[:-1], data[-1]
        calc = 0
        for byte in payload:
            calc = self.crc_table[(calc ^ byte) & 0xFF]
        return calc == crc


if __name__ == "__main__":
    # quick bench test: prints live rotation speed for a few seconds
    import time
    from config import Config

    config = Config()
    config.init(scan_id="_bench")
    lidar = Lidar(config)

    print("Reading for 3s (Ctrl+C to stop early)...")
    t0 = time.time()
    try:
        while time.time() - t0 < 3:
            lidar._read_packet()
            if lidar.timestamp % 500 < 5:
                print(f"speed: {lidar.speed:.2f} rev/s")
    finally:
        lidar.close()
