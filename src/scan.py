#!/usr/bin/env python3
"""
Main scan entry point: spins the turntable through its configured sweep
(180 deg by default -- see ARCHITECTURE.md section 1 for why that covers
a full sphere), capturing the LiDAR the whole time, then merges the
result into a colored point cloud and exports it as PLY.

Adapted from PiLiDAR.py (https://github.com/PiLiDAR/PiLiDAR),
(c) Philip Gutjahr, CC BY-NC-SA 4.0 -- the camera/panorama/HDR branches
are removed entirely (this is a LiDAR-only build, see BOM.md), and the
3D merge no longer depends on Open3D (see ARCHITECTURE.md section 2).

Usage:
    python3 scan.py [--scan-id NAME] [--angle 180] [--res 0.225] [--ascii]
"""

import argparse
import time

from config import Config
from lidar_driver import Lidar
from stepper_driver import Stepper
from pointcloud import get_scan_dict, save_raw_scan, merge_2D_points, intensity_to_rgb, save_ply


def run_scan(config):
    imu = None
    if config.get("ENABLE_IMU"):
        from imu_driver import MPU6050Wrapper
        imu = MPU6050Wrapper(config.get("IMU", "i2c_bus"), config.get("IMU", "device_address"), config.get("IMU", "frequency"))

    lidar = Lidar(config)
    stepper = Stepper(config)

    def step_callback():
        stepper.move_steps(config.steps if config.SCAN_ANGLE > 0 else -config.steps)
        lidar.z_angle = stepper.get_current_angle()

    print(f"Scanning {config.SCAN_ANGLE} deg @ {config.h_res:.4f} deg/step "
          f"({config.horizontal_steps} steps, ~{config.max_packages} packages)...")
    t0 = time.time()

    try:
        lidar.read_loop(callback=step_callback, max_packages=config.max_packages)
        stepper.move_to_angle(0)
    finally:
        lidar.close()
        stepper.close()
        if imu is not None:
            imu.close()

    elapsed = time.time() - t0
    print(f"Capture finished in {elapsed:.1f}s ({len(lidar.z_angles)} revolutions).")
    return lidar


def process_scan(config, lidar):
    raw_scan = get_scan_dict(lidar.z_angles, lidar.cartesian_list, scan_id=config.scan_id)
    save_raw_scan(config.raw_path, raw_scan)
    print(f"Raw scan saved: {config.raw_path}")

    position_offset = (0.0, config.get("3D", "Y_OFFSET"), config.get("3D", "Z_OFFSET"))
    angle_offset = config.get("LIDAR", "LIDAR_OFFSET_ANGLE")
    points = merge_2D_points(raw_scan, position_offset=position_offset, angle_offset=angle_offset)

    if len(points) == 0:
        print("[WARNING] merged point cloud is empty -- check LiDAR wiring/UART before re-scanning.")
        return

    scale = config.get("3D", "SCALE")
    colors = intensity_to_rgb(points[:, 3], mode=config.get("3D", "COLOR_MODE"))
    save_ply(config.pcd_path, points[:, :3] * scale, colors, ascii_mode=config.get("3D", "ASCII"))

    print(f"Wrote {len(points)} points to {config.pcd_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-id", default=None, help="scan folder name (default: timestamp)")
    parser.add_argument("--angle", type=float, default=None, help="override STEPPER.SCAN_ANGLE (degrees)")
    parser.add_argument("--res", type=float, default=None, help="override LIDAR.TARGET_RES (degrees/step)")
    parser.add_argument("--ascii", action="store_true", help="write ASCII PLY instead of binary")
    args = parser.parse_args()

    config = Config()
    config.init(scan_id=args.scan_id)

    if args.angle is not None:
        config.SCAN_ANGLE = args.angle
        config.set(args.angle, "STEPPER", "SCAN_ANGLE")
    if args.res is not None:
        config.update_target_res(args.res)
    if args.ascii:
        config.set(True, "3D", "ASCII")

    print(f"\n=== scan {config.scan_id} ===\n")
    lidar = run_scan(config)
    process_scan(config, lidar)
    print("\nDone.\n")
