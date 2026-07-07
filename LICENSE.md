# License

This project is a derivative of [**PiLiDAR**](https://github.com/PiLiDAR/PiLiDAR)
and [**PiLiDAR-Hardware**](https://github.com/PiLiDAR/PiLiDAR-Hardware),
© Philip Gutjahr, licensed under **CC BY-NC-SA 4.0**. Several files under
`src/` are directly adapted from PiLiDAR's Python source (each such file
says so in its header comment); the overall hardware architecture
(GPIO pinout, LiDAR-on-turntable scan geometry, stepper-driven azimuth
sweep) is likewise adapted from PiLiDAR-Hardware's published design.
Per that license's ShareAlike term, this entire repository — software and
documentation alike — is released under the same terms.

## Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)

### This work: Copyright (c) 2026, based on PiLiDAR, Copyright (c) 2024 Philip Gutjahr

**You are free to**:
**Share** — copy and redistribute the material in any medium or format.
**Adapt** — remix, transform, and build upon the material.
The licensor cannot revoke these freedoms as long as you follow the license terms.

**Under the following terms:**

**Attribution** — You must give appropriate credit, provide a link to the license,
and indicate if changes were made. You may do so in any reasonable manner,
but not in any way that suggests the licensor endorses you or your use.

**NonCommercial** — You may not use the material for commercial purposes.

**ShareAlike** — If you remix, transform, or build upon the material,
you must distribute your contributions under the same license as the original.
No additional restrictions:
You may not apply legal terms or technological measures that legally restrict
others from doing anything the license permits.

For the full license text, visit: **[CC BY-NC-SA 4.0 License](https://creativecommons.org/licenses/by-nc-sa/4.0/)**.

-------------------------------------------------------------------------------

## Attribution notes for this repository specifically

- `src/lidar_driver.py`, `src/stepper_driver.py` (the `A4988` class),
  `src/config.py`, `src/imu_driver.py`, and `src/button_daemon.py` are
  adapted from PiLiDAR's Python source. `src/crc_table.json` reproduces
  the LD06/LD19 protocol's CRC8 lookup table as published in the sensor's
  own development manual.
- `src/stepper_driver.py`'s `ULN2003` class, `src/pointcloud.py`'s PLY
  writer and colormap, and `src/calibrate_pwm.py` / `calibrate_mechanical.py`
  are new code written for this project (the latter re-implements PiLiDAR's
  calibration *approach* without depending on Open3D/SciPy — see
  ARCHITECTURE.md).
- BOM.md, ARCHITECTURE.md, PRINTS.md, and BUILD.md are original
  documentation for this specific budget hardware variant, informed by
  PiLiDAR-Hardware's published designs but not copied from them file-for-file
  (different motor/bearing/mounting choices throughout — see BOM.md for why).

If you build on this repository, the same terms apply to your derivative:
credit both this repository and the upstream PiLiDAR project, keep it
non-commercial, and share alike.
