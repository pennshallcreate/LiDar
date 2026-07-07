# Architecture

System design, wiring/pinout, and the power budget proving ≥15 minutes of
continuous scan runtime. Parts referenced here are defined in
[BOM.md](BOM.md); assembly order is in [BUILD.md](BUILD.md); printed-part
geometry is in [PRINTS.md](PRINTS.md).

## 1. System overview

Like PiLiDAR, this is a **2D LiDAR spun on two axes** rather than a native 3D
LiDAR: the sensor's own motor sweeps a vertical circle at ~10 Hz, and a
stepper-driven turntable slowly sweeps that vertical circle through 180° of
azimuth over the course of a scan. The two sweeps together cover a full
sphere.

```
                         ┌───────────────┐
                         │   LD19 LiDAR   │  spins its own beam
                         │  (vertical     │  in a vertical circle
                         │   plane)       │  @ ~10 Hz
                         └───────┬───────┘
                                 │ mast
                         ┌───────┴───────┐
                         │   platter      │  rotated by NEMA17/28BYJ-48
                         │ (lazy-susan    │  through 180° over the scan
                         │  bearing)      │
                         └───────┬───────┘
                                 │
        ┌────────────────────────────────────────────┐
        │  base: Pi Zero 2 W, A4988/ULN2003, boost    │
        │  converter (Recommended tier only), buttons │
        └────────────────────────────────────────────┘
                                 │
                         USB-C power bank
```

**Why 180°, not 360°, of turntable rotation:** one full revolution of the
LiDAR's own spin already sweeps a plane that passes through the mast axis —
i.e. it looks "forward" and "backward" (180° apart) *simultaneously*, once
per revolution. Stepping the turntable through a full 180° therefore already
sweeps that plane through every possible azimuth exactly once; going to 360°
would just re-scan the same sphere a second time. This is exactly the
geometry PiLiDAR uses (`SCAN_ANGLE: 180` in its config) and it halves scan
time for free.

**Resolution:** vertical (elevation) resolution is fixed by the LiDAR's own
sampling rate and spin speed (4500 samples/s ÷ ~10 rev/s ≈ 450 points/rev ≈
0.8°/point, native). Azimuth resolution is set by how finely the turntable
steps — see [§4](#4-motion-system) — and is comfortably finer than 0.8°, so
elevation, not azimuth, is the resolution bottleneck, same as the reference
project.

## 2. Compute: Raspberry Pi Zero 2 W

A Pi 4 (PiLiDAR's choice) is massive overkill for a LiDAR-only build with no
camera/panorama/meshing pipeline running on-device — that pipeline is the
part PiLiDAR uses the extra RAM/CPU for, and it's exactly the part we've cut.
What's left (read UART, toggle GPIO, buffer numpy arrays, write a PLY file)
comfortably fits the Zero 2 W's quad-core Cortex-A53 and 512 MB RAM, at
roughly a third of the Pi 4's price and power draw. The 40-pin header,
hardware PWM, and mini-UART are all identical to the Pi 4 for our purposes,
so PiLiDAR's GPIO-level driver code ports over almost unchanged (see
`src/`).

**Deliberate simplification vs. PiLiDAR:** the onboard code never imports
Open3D. Point-cloud assembly is plain NumPy (coordinate transforms over a
few hundred thousand points — seconds, not minutes, on this CPU) and PLY
export is a ~30-line manual binary writer (`src/pointcloud.py`). Open3D is a
large, native-compiled dependency; avoiding it on a 512 MB board sidesteps a
real memory/build-time risk for zero loss of the required output (binary
PLY). If you want Open3D-powered visualization, ICP registration, or Poisson
meshing, PiLiDAR already documents that workflow well — run it on a laptop
against the PLY this device produces, exactly as PiLiDAR itself recommends
doing for the slow steps ("Poisson Surface Meshing... recommended to run on
PC").

## 3. GPIO pinout

All pin numbers are **BCM numbering**. This map is carried over from PiLiDAR
unchanged where the subsystem is unchanged (LiDAR UART/PWM, stepper
DIR/STEP/microstep, buttons) — no reason to diverge from a proven pin
assignment.

| Signal | Pi GPIO (BCM) | Physical pin | Notes |
|---|---|---|---|
| LiDAR UART RX | GPIO15 (RXD0) | 10 | mini-UART (`/dev/ttyS0`); LiDAR only transmits, so TX (GPIO14) is unused |
| LiDAR motor speed (PWM) | GPIO18 (PWM0) | 12 | hardware PWM, `rpi-hardware-pwm` |
| Scan-trigger button | GPIO17 | 11 | to GND, internal pull-up, falling-edge |
| Power button | GPIO3 | 5 | hardwired wake pin; `dtoverlay=gpio-shutdown` |
| Stepper DIR | GPIO26 | 37 | A4988 / ULN2003-IN1 |
| Stepper STEP | GPIO19 | 35 | A4988 STEP (28BYJ-48 tier: see §4.2, needs 4 GPIO instead) |
| Stepper microstep MS1 | GPIO5 | 29 | A4988 only — no microstep pins on ULN2003 tier |
| Stepper microstep MS2 | GPIO6 | 31 | A4988 only |
| Stepper microstep MS3 | GPIO13 | 33 | A4988 only |
| IMU SDA (optional) | GPIO22 | 15 | `i2c-gpio` bus 3 — GPIO2/3 (hw I2C) are unavailable, GPIO3 is the power button |
| IMU SCL (optional) | GPIO27 | 13 | `i2c-gpio` bus 3 |
| 5V (LiDAR VCC, Pi power in) | 5V pins | 2, 4 | |
| 3.3V (A4988 logic VDD) | 3V3 | 1, 17 | |
| GND (common) | GND | 6, 9, 14, 20, 25, 30, 34, 39 | tie LiDAR GND, driver GND, boost converter GND, button GND all to Pi GND |

## 4. Motion system

### 4.1 Recommended tier: NEMA17 + A4988

- **Direct drive, no gearbox.** PiLiDAR uses a 3D-printed planetary
  reduction (~3.71:1) between motor and turntable. We skip it: at 16×
  microstepping a NEMA17 alone gives 3200 microsteps/rev = 0.1125°/step,
  already finer than the LiDAR's native ~0.8° vertical resolution, and the
  motor has roughly 10× the torque this load (a few-hundred-gram printed
  mast) needs even ungeared. Removing the gearbox removes a finicky
  multi-part print and a cost line, at no resolution cost. See
  [PRINTS.md](PRINTS.md) for the tradeoff discussion.
- **The lazy-susan bearing carries the load, not the motor shaft.** The
  platter sits on the hardware bearing; the motor connects via a printed hub
  that only has to transmit torque. This keeps side-load off the motor's
  small internal bearings.
- **Microstep truth table** (MS1/MS2/MS3 → resolution), standard A4988:

  | MS1 | MS2 | MS3 | Microsteps |
  |---|---|---|---|
  | Low | Low | Low | 1 (full step) |
  | High | Low | Low | 2 |
  | Low | High | Low | 4 |
  | High | High | Low | 8 |
  | High | High | High | 16 ← used |

- **Current limit (Vref).** Set the driver's onboard trimpot for **0.5 A/phase**
  — comfortable torque margin for this load without wasting battery power as
  heat. Formula for the common 0.05 Ω sense-resistor A4988 breakout (verify
  your board's sense resistor against its silkscreen/datasheet before
  trusting this number): `I_limit = V_ref × 2.5`, so `V_ref = I_limit / 2.5 =
  0.2 V`. Measure with a multimeter between the trimpot wiper and GND, motor
  **disconnected**, before wiring it up.
- **SLEEP/RESET/ENABLE.** We never need to put the driver to sleep or reset
  it from software, so wire it to always be active: bridge `SLEEP` to
  `RESET` with a short jumper directly on the driver board, tie that joined
  pair to the driver's logic `VDD` (3.3V), and tie `ENABLE` (active-low)
  straight to `GND`.
- **VMOT (motor power):** 12 V from the MT3608 boost converter, trimmed with
  its onboard pot (measure with a multimeter before connecting the driver —
  cheap boost modules can overshoot their marked voltage). **Never run VMOT
  below ~8 V** — the A4988's internal charge pump needs it, and the driver
  can behave unreliably (missed steps, or nothing at all) below that,
  which is exactly why we boost 5V→12V rather than feeding the driver
  straight off the battery rail.

### 4.2 Budget tier: 28BYJ-48 + ULN2003

Runs natively off the 5V rail — no boost converter, no Vref tuning, no
sleep/reset jumpering. Trades away: A4988-style microstep pin selection (the
ULN2003 board just takes 4 direct GPIO outputs, one per motor coil, sequenced
in software — see `src/stepper_driver.py`, which auto-detects which driver
class to instantiate from `config.json`), and roughly 10× the torque margin
of the NEMA17 (see [BOM.md](BOM.md#quality-difference-recommended-vs-budget)
for why that margin matters or doesn't for your specific build).

| Signal | Pi GPIO (BCM) |
|---|---|
| ULN2003 IN1 | GPIO26 |
| ULN2003 IN2 | GPIO19 |
| ULN2003 IN3 | GPIO5 |
| ULN2003 IN4 | GPIO6 |

## 5. Power budget

**Requirement: ≥15 minutes of continuous operation with the LiDAR, stepper,
and Pi all active simultaneously (the actual worst case during a scan).**

### Worst-case bound (the proof)

Deliberately pessimistic on every number, so this is a floor, not an
expectation:

| Load | Recommended tier | Budget tier |
|---|---|---|
| Pi Zero 2 W (CPU+Wi-Fi, published worst case) | 0.50 A @ 5V = 2.50 W | 2.50 W |
| LD19 LiDAR (datasheet current, upper end) | 0.45 A @ 5V = 2.25 W | 2.25 W |
| Stepper + driver, current-limited¹ | 1.0 A @ 12V = 12 W → ÷0.8 boost eff. = **15.0 W** | 0.4 A @ 5V = **2.0 W** (no boost) |
| **Total draw** | **19.75 W** (≈3.95 A @ 5V) | **6.75 W** (≈1.35 A @ 5V) |

<sup>¹ Modeled as *both* motor phases simultaneously at the A4988's 0.5 A/phase
current-limit setpoint — physically the two phases are in quadrature so real
combined current never actually reaches 1.0 A, but treating it as if it did
gives a deliberately-loose, safe upper bound. The 28BYJ-48/ULN2003 figure is
its datasheet worst-case combined coil current.</sup>

| | Recommended (10,000 mAh) | Budget (5,000 mAh) |
|---|---|---|
| Nominal energy (Ah × 3.7 V) | 37.0 Wh | 18.5 Wh |
| × 80% (aged-battery/cold derating) | 29.6 Wh | 14.8 Wh |
| × 80% (USB boost conversion, low end) | **23.68 Wh usable** | **11.84 Wh usable** |
| ÷ worst-case draw | 23.68 / 19.75 W | 11.84 / 6.75 W |
| **Runtime floor** | **71.9 min** | **105.2 min** |
| **Margin over the 15-min requirement** | **4.8×** | **7.0×** |

Both tiers clear the requirement with several times over margin, *even under
deliberately pessimistic assumptions*. (Interesting wrinkle: the Budget
tier's floor is actually higher, because it skips the boost converter's
conversion loss — it trades motor torque margin for power-system
simplicity/efficiency. See BOM.md for the full tradeoff.)

### Typical case (practical expectation)

Real Vref-limited stepper draw, fresh battery, mixed CPU/Wi-Fi load:

| | Recommended | Budget |
|---|---|---|
| Total typical draw | ≈8.3 W | ≈4.75 W |
| Usable energy (100% capacity × 88% conversion) | 32.6 Wh | 16.3 Wh |
| **Typical runtime** | **≈3h 55m** | **≈3h 25m** |

In practice, expect a full afternoon of scanning (8–10 individual scans at
~1.5–2 min each, see §6) per charge, not a single 15-minute window.

## 6. Scan duration (informational, not a hard requirement)

At the default resolution (0.225°/microstep azimuth step, 800 steps over the
180° sweep) the LiDAR itself is the pacing element: 4500 samples/s ÷ 12
samples/package = 375 packages/s, and the scan needs
`800 steps × ~38 packages/step ≈ 30,400 packages`, i.e. **≈81 seconds** per
full 360°×180° scan. Tunable via `TARGET_RES` in `config.json`, exactly like
PiLiDAR.

## 7. Data flow

```
LD19 (UART, 230400 baud) ──▶ lidar_driver.py ──▶ raw scan buffer (numpy, per-revolution)
                                                          │
stepper_driver.py ◀── scan.py orchestrates ──────────────┤
   (steps once per revolution, records current angle)     │
                                                          ▼
                                          pointcloud.py: revolve each
                                          2D revolution by its recorded
                                          azimuth angle → merged XYZI
                                                          │
                                                          ▼
                                        intensity → viridis colormap
                                                          │
                                                          ▼
                                            binary PLY written to
                                            /scans/<timestamp>/scan.ply
```

Raw per-revolution data is also pickled to disk (`<timestamp>_lidar.pkl`,
same format as PiLiDAR) before merging, so a scan is never lost to a
crash in the merge/export step and can be re-processed later with different
offsets.

## 8. Known limitations (inherent to this scan geometry, not this budget)

- **Blind cone directly below the device.** The base/platter physically
  blocks the LiDAR's view of the ground directly underneath it — identical
  limitation to PiLiDAR and to every mast-mounted spinning-LiDAR scanner.
  Elevate the scanner (tripod, see [BUILD.md](BUILD.md)) if you need
  near-field floor coverage.
- **Anisotropic resolution.** Azimuth resolution (fine, stepper-controlled)
  and elevation resolution (coarser, fixed by the LiDAR's own spin speed)
  are not equal — same as PiLiDAR. This is a property of the "2D LiDAR on
  two axes" approach, not something a bigger budget fixes without a
  different sensor architecture entirely (e.g. a solid-state 3D LiDAR, which
  is a different price class altogether).
- **No RGB by default.** See BOM.md's optional-upgrades section.
