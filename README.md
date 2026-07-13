# LiDar — a budget DIY 360° 3D LiDAR scanner

A buildable, portable, USB-C-rechargeable 360° 3D scanner modeled on the
open-source [PiLiDAR](https://github.com/PiLiDAR/PiLiDAR) project: an
LDRobot 2D LiDAR spun on a stepper-driven turntable, orchestrated by a
Raspberry Pi 3 Model A+, exporting colored PLY point clouds. No camera, no panorama
stitching — just the scanning core, built to a real budget.

| | |
|---|---|
| **Cost** | $188 all-new, or $158 if you already own the Pi 3 A+ — see the budget note in [BOM.md](BOM.md) |
| **Compute** | Raspberry Pi 3 Model A+ (factory-soldered 40-pin header, dual-band Wi-Fi) |
| **Sourcing** | 100% Amazon, Prime-eligible — see [Parts.md](Parts.md) for the plain shopping list |
| **Build skill** | No soldering, no multimeter — breadboard + push-fit connectors throughout |
| **Sensor** | LDRobot LD19 (or LD06), 4500 samples/s, 0.02–12m range |
| **Runtime** | ≥2.5h worst-case, ~5.5h typical, on a single USB-C power bank charge — [proof](ARCHITECTURE.md#5-power-budget) |
| **Output** | Binary PLY point clouds, intensity-colored |
| **License** | [CC BY-NC-SA 4.0](LICENSE.md) (inherited from PiLiDAR) |

## Documentation

1. **[BOM.md](BOM.md)** — parts list, current prices, sourcing, and the
   no-solder/no-multimeter design constraints this build is built around
   (**[Parts.md](Parts.md)** has just the shopping list, no explanation)
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** — wiring/pinout, motion system,
   and the power budget proving the runtime requirement
3. **[`src/`](src/)** — Python: LiDAR serial capture, stepper control,
   point-cloud assembly, PLY export, calibration
4. **[PRINTS.md](PRINTS.md)** — 3D-printed parts, dimensions, and
   parametric OpenSCAD source in [`models/`](models/)
5. **[BUILD.md](BUILD.md)** — ordered assembly and test checklist, start
   to first scan

If you're building one of these, read them in that order. If you just want
to know whether this is worth building: it's a real, working scanner for
about the price of a mid-range LiDAR sensor alone, with the tradeoffs
(anisotropic resolution, a blind cone underneath, no RGB by default)
documented rather than glossed over — see ARCHITECTURE.md's limitations
section before committing to a parts order.

## Credit

This project adapts code, wiring conventions, and the overall scan
geometry from [PiLiDAR](https://github.com/PiLiDAR/PiLiDAR) and
[PiLiDAR-Hardware](https://github.com/PiLiDAR/PiLiDAR-Hardware) by Philip
Gutjahr, CC BY-NC-SA 4.0. See [LICENSE.md](LICENSE.md) for the full
attribution and what's original vs. adapted.
