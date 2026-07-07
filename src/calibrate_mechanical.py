"""
Mechanical-offset calibration helper.

The turntable/mast assembly is never machined perfectly: the LiDAR's
optical center sits some small distance from the true rotation axis, and
the mast may lean a fraction of a degree. `config.json`'s `3D.Y_OFFSET`,
`3D.Z_OFFSET` (mm) and `LIDAR.LIDAR_OFFSET_ANGLE` (degrees) correct for
this -- see ARCHITECTURE.md and PRINTS.md.

There's no automatic solver here (PiLiDAR doesn't have one either -- its
own offsets are hand-fitted constants). This script just runs a fast,
low-resolution scan of a nearby flat wall/corner so you can iterate
quickly: run it, open the PLY in MeshLab/CloudCompare, check that walls
are flat and perpendicular, adjust the three constants in config.json,
re-run. Full procedure in BUILD.md's calibration checklist.

Usage:
    python3 calibrate_mechanical.py [--angle 90] [--res 1.0]
"""

import argparse

from config import Config
from lidar_driver import Lidar
from stepper_driver import Stepper
from pointcloud import get_scan_dict, merge_2D_points, intensity_to_rgb, save_ply, save_raw_scan


def quick_scan(config, scan_angle, target_res):
    config.set(scan_angle, "STEPPER", "SCAN_ANGLE")
    config.SCAN_ANGLE = scan_angle
    config.update_target_res(target_res)

    lidar = Lidar(config)
    stepper = Stepper(config)

    def step_callback():
        stepper.move_steps(config.steps if config.SCAN_ANGLE > 0 else -config.steps)
        lidar.z_angle = stepper.get_current_angle()

    try:
        print(f"Quick scan: {scan_angle} deg @ {target_res} deg/step "
              f"(~{config.max_packages} packages)...")
        lidar.read_loop(callback=step_callback, max_packages=config.max_packages)
        stepper.move_to_angle(0)
    finally:
        lidar.close()
        stepper.close()

    return lidar


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--angle", type=float, default=90, help="turntable sweep in degrees (default: 90, a quick quarter-turn)")
    parser.add_argument("--res", type=float, default=1.0, help="azimuth resolution in degrees/step (default: 1.0, coarse+fast for iteration)")
    args = parser.parse_args()

    config = Config()
    config.init(scan_id="_calibrate_mechanical")

    lidar = quick_scan(config, args.angle, args.res)

    raw_scan = get_scan_dict(lidar.z_angles, lidar.cartesian_list, scan_id=config.scan_id)
    save_raw_scan(config.raw_path, raw_scan)

    y_offset = config.get("3D", "Y_OFFSET")
    z_offset = config.get("3D", "Z_OFFSET")
    angle_offset = config.get("LIDAR", "LIDAR_OFFSET_ANGLE")
    points = merge_2D_points(raw_scan, position_offset=(0, y_offset, z_offset), angle_offset=angle_offset)
    colors = intensity_to_rgb(points[:, 3], mode=config.get("3D", "COLOR_MODE"))
    save_ply(config.pcd_path, points[:, :3] * config.get("3D", "SCALE"), colors,
             ascii_mode=config.get("3D", "ASCII"))

    print(f"\nWrote {len(points)} points to {config.pcd_path}")
    print(f"Current offsets: Y_OFFSET={y_offset} Z_OFFSET={z_offset} LIDAR_OFFSET_ANGLE={angle_offset}")
    print("Open the PLY in MeshLab/CloudCompare, check flatness/verticality of a known wall,")
    print("adjust the three values above in config.json, and re-run.")
