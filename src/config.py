"""
Config loader: reads config.json, resolves the selected LiDAR/stepper
device blocks, and derives the stepper-step / package-count math needed
for a scan.

Adapted from PiLiDAR's lib/config.py (https://github.com/PiLiDAR/PiLiDAR),
(c) Philip Gutjahr, CC BY-NC-SA 4.0 -- trimmed to drop the
camera/panorama/mesh/registration/filtering sections that don't apply to
this LiDAR-only build.
"""

import json
import os
import datetime
from typing import Optional

from file_utils import make_dir
from platform_utils import get_platform


class Config:
    def __init__(self, file_path: str = "config.json", scans_root: Optional[str] = None):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))

        with open(os.path.join(self.base_dir, file_path), "r") as f:
            self.dict = json.load(f)

        if scans_root is not None:
            self.set(scans_root, "SCANS_ROOT")
        self.scans_root = os.path.join(self.base_dir, self.get("SCANS_ROOT"))

        # resolve protocol hex strings and CRC table once
        protocol = self.dict["LIDAR"]["protocol"]
        self.set(bytes.fromhex(protocol["start_byte"]), "LIDAR", "protocol", "start_byte")
        self.set(bytes.fromhex(protocol["dlength_byte"]), "LIDAR", "protocol", "dlength_byte")

        crc_path = os.path.join(self.base_dir, protocol["CRC_PATH"])
        with open(crc_path, "r") as f:
            crc_hex = json.load(f)["CRC_TABLE"]
        self.crc_table = [int(h, 16) for h in crc_hex]
        self.set(self.crc_table, "LIDAR", "protocol", "CRC_TABLE")

        self.platform = get_platform()
        self.set_device(self.get("LIDAR", "DEVICE"))

        # stepper geometry
        self.STEPPER_DRIVER = self.get("STEPPER", "DRIVER")
        self.STEPPER_RES = self.get("STEPPER", "STEPPER_RES")
        self.MICROSTEPS = self.get("STEPPER", "MICROSTEPS")
        self.SCAN_ANGLE = self.get("STEPPER", "SCAN_ANGLE")

        self.set(360 / self.STEPPER_RES, "STEPPER", "STEP_ANGLE")
        self.gear_ratio = self.evaluate_formula(str(self.get("STEPPER", "GEAR_RATIO")))
        self.set(self.gear_ratio, "STEPPER", "GEAR_RATIO")

        self.target_res = self.evaluate_formula(str(self.get("LIDAR", "TARGET_RES")))
        self.update_target_res(self.target_res)

    def init(self, scan_id: Optional[str] = None):
        self.scan_id = scan_id or datetime.datetime.now().strftime("%y%m%d-%H%M")

        self.scan_dir = os.path.join(self.scans_root, self.scan_id)
        self.raw_path = os.path.join(self.scan_dir, f"{self.scan_id}{self.get('LIDAR', 'RAW_NAME')}")
        self.pcd_path = os.path.join(self.scan_dir, f"{self.scan_id}.{self.get('3D', 'EXT')}")
        make_dir(self.scan_dir)
        return self.scan_id

    def set_device(self, device: str):
        self.DEVICE = device
        self.TARGET_SPEED = self.get("LIDAR", "TARGET_SPEED")
        self.SAMPLING_RATE = self.get("LIDAR", device, "SAMPLING_RATE")
        self.BAUDRATE = self.get("LIDAR", device, "BAUDRATE")
        self.PORT = self.get("LIDAR", device, "PORT")

        if self.platform == "RaspberryPi":
            print("Platform: Raspberry Pi")

    def get(self, *args):
        value = self.dict
        for key in args:
            value = value[key]
        return value

    def set(self, value, *args):
        d = self.dict
        for key in args[:-1]:
            d = d.setdefault(key, {})
        d[args[-1]] = value

    def update_target_res(self, target_res):
        """Derive microstep count per move and package-per-revolution
        count from the desired azimuth resolution (degrees/step).

        Steps-per-revolution depends on which stepper driver is
        configured -- ULN2003's 28BYJ-48 has a fixed ~4096 steps/rev from
        its internal gearbox, unrelated to A4988's STEPPER_RES*MICROSTEPS
        microstepping math. Using the wrong one silently under- or
        over-drives the turntable relative to what TARGET_RES/SCAN_ANGLE
        claim -- e.g. a 180 deg scan would actually stop ~30 deg short."""
        self.target_res = target_res
        self.set(self.target_res, "LIDAR", "TARGET_RES")

        if self.STEPPER_DRIVER == "ULN2003":
            steps_per_revolution = self.get("STEPPER", "ULN2003_STEPS_PER_REV")
        else:
            steps_per_revolution = self.STEPPER_RES * self.MICROSTEPS
        self.microsteps_per_revolution = steps_per_revolution * self.gear_ratio
        self.steps = max(1, int(round(self.microsteps_per_revolution * self.target_res / 360)))
        self.h_res = 360 * self.steps / self.microsteps_per_revolution
        self.horizontal_steps = int(abs(self.SCAN_ANGLE) / self.h_res)
        self.packages_per_revolution = round(self.SAMPLING_RATE / (12 * self.TARGET_SPEED))
        self.max_packages = self.horizontal_steps * self.packages_per_revolution

    @staticmethod
    def evaluate_formula(formula: str):
        # config.json values like "1 + 38/14" (gear ratios) or "0.225" (resolution).
        # config.json is a local trusted file the device owner edits, not
        # untrusted input, so eval() here is the same tradeoff PiLiDAR itself
        # makes -- convenience for expressing simple ratios/fractions.
        allowed = "0123456789.+-*/() "
        if not all(c in allowed for c in formula):
            raise ValueError(f"Unexpected character in config formula: {formula!r}")
        return eval(formula, {"__builtins__": {}}, {})


if __name__ == "__main__":
    config = Config()
    scan_id = config.init()
    print("scan_id:", scan_id)
    print("steps/move:", config.steps, " h_res:", round(config.h_res, 4),
          " horizontal_steps:", config.horizontal_steps,
          " packages/rev:", config.packages_per_revolution,
          " max_packages:", config.max_packages)
