# src/

Onboard Python for the scanner (runs on the Pi itself, headless). Hardware
context is in [../ARCHITECTURE.md](../ARCHITECTURE.md); assembly and the
first-scan checklist is in [../BUILD.md](../BUILD.md) -- start there if
you're setting one of these up. This file is just a map of the code.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Edit `config.json` first: set `STEPPER.DRIVER` to `"A4988"` or `"ULN2003"`
to match your build tier (BOM.md), and `LIDAR.DEVICE` to `"LD19"` or
`"LD06"`.

## Files

| File | Role |
|---|---|
| `config.json` / `config.py` | Central config: device selection, pins, scan geometry, offsets. Everything else reads from here. |
| `crc_table.json` | CRC8 lookup table for the LD06/LD19 UART protocol. |
| `lidar_driver.py` | Serial capture: reads packets, checks CRC8, decodes angle/distance/intensity, controls motor-speed PWM. |
| `stepper_driver.py` | Turntable motor control -- `A4988` (NEMA17) and `ULN2003` (28BYJ-48) classes behind one interface; `Stepper(config)` picks the right one. |
| `pointcloud.py` | 2D-per-revolution -> merged 3D point cloud, intensity colorization, binary/ASCII PLY export. Pure NumPy, no Open3D (see ARCHITECTURE.md § 2). |
| `scan.py` | Main entry point: runs a full scan and writes the PLY. `python3 scan.py --help` for options. |
| `calibrate_pwm.py` | One-time motor speed-vs-PWM calibration (produces `PWM_COEFFS` for config.json). |
| `calibrate_mechanical.py` | Fast, low-res scan for iterating on the mechanical offset constants (`Y_OFFSET`/`Z_OFFSET`/`LIDAR_OFFSET_ANGLE`). |
| `imu_driver.py` | Optional MPU6050 tilt sensor, only used if `ENABLE_IMU: true`. |
| `button_daemon.py` | Scan-trigger button listener, meant to run as a systemd service (BUILD.md). |
| `platform_utils.py` / `file_utils.py` | Small shared helpers (serial/PWM init, directory helpers). |

## Running a scan manually

```bash
python3 scan.py
```

Output goes to `scans/<timestamp>/`: the raw per-revolution pickle
(`*_lidar.pkl`) and the exported point cloud (`*.ply`).

## Attribution

Several files here are adapted from [PiLiDAR](https://github.com/PiLiDAR/PiLiDAR)
(c) Philip Gutjahr, licensed CC BY-NC-SA 4.0 -- see the per-file header
comments for which ones, and [../LICENSE.md](../LICENSE.md) for the full
license text this repository is released under as a result.
