"""
Optional IMU support (GY-521 / MPU6050) for auto-leveling the point cloud
when the tripod/ground isn't perfectly level. Not required for the base
build -- see BOM.md's optional-upgrades section. Enable with
`ENABLE_IMU: true` in config.json (also requires wiring the i2c-gpio bus,
see ARCHITECTURE.md).

Adapted from PiLiDAR's lib/imu_driver.py
(https://github.com/PiLiDAR/PiLiDAR), (c) Philip Gutjahr, CC BY-NC-SA 4.0.

Requires the `mpu6050-raspberrypi` (or compatible `mpu6050`) package,
listed as an optional extra in requirements.txt.
"""

import math
import threading
import time


class MPU6050Wrapper:
    def __init__(self, i2c_bus=3, device_address=0x68, freq=50):
        from mpu6050 import mpu6050 as MPU6050  # imported lazily: optional dependency

        self.mpu = MPU6050(device_address, bus=i2c_bus)
        self.freq = freq

        self._latest = {"accel": (0.0, 0.0, 0.0), "gyro": (0.0, 0.0, 0.0)}
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def _poll_loop(self):
        period = 1.0 / self.freq
        while self._running:
            try:
                accel = self.mpu.get_accel_data()
                gyro = self.mpu.get_gyro_data()
                self._latest = {
                    "accel": (accel["x"], accel["y"], accel["z"]),
                    "gyro": (gyro["x"], gyro["y"], gyro["z"]),
                }
            except OSError:
                pass  # transient I2C hiccup -- keep the last good reading
            time.sleep(period)

    def get_tilt_deg(self):
        """Static tilt of the mast (roll, pitch) from the gravity vector
        seen in the accelerometer, in degrees. Useful as a one-shot
        "is the tripod level" check before a scan, or to feed a leveling
        correction into merge_2D_points' angle_offset."""
        ax, ay, az = self._latest["accel"]
        roll = math.degrees(math.atan2(ay, az))
        pitch = math.degrees(math.atan2(-ax, math.sqrt(ay ** 2 + az ** 2)))
        return roll, pitch

    def close(self):
        self._running = False
        self._thread.join(timeout=1.0)


if __name__ == "__main__":
    from config import Config

    config = Config()
    imu = MPU6050Wrapper(config.get("IMU", "i2c_bus"), config.get("IMU", "device_address"), config.get("IMU", "frequency"))
    try:
        time.sleep(0.5)
        roll, pitch = imu.get_tilt_deg()
        print(f"roll: {roll:.2f} deg, pitch: {pitch:.2f} deg -- should both be ~0 deg if level")
    finally:
        imu.close()
