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
                         │   platter      │  rotated by a 28BYJ-48
                         │ (lazy-susan    │  through 180° over the scan
                         │  bearing)      │
                         └───────┬───────┘
                                 │
        ┌────────────────────────────────────────────┐
        │  base: Pi Zero 2 W, breadboard + ULN2003    │
        │  driver, buttons -- single 5V rail, no      │
        │  boost converter needed (§4.1)              │
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

All pin numbers are **BCM numbering**, all connections are push-fit Dupont
jumpers into the Pi Zero 2 **WH**'s pre-soldered header (no soldering
anywhere — see BOM.md) routed through a breadboard. This map is carried
over from PiLiDAR unchanged where the subsystem is unchanged (LiDAR
UART/PWM, buttons) — no reason to diverge from a proven pin assignment.

| Signal | Pi GPIO (BCM) | Physical pin | Notes |
|---|---|---|---|
| LiDAR UART RX | GPIO15 (RXD0) | 10 | mini-UART (`/dev/ttyS0`); LiDAR only transmits, so TX (GPIO14) is unused |
| LiDAR motor speed (PWM) | GPIO18 (PWM0) | 12 | hardware PWM, `rpi-hardware-pwm` |
| Scan-trigger button | GPIO17 | 11 | to GND, internal pull-up, falling-edge |
| Power button | GPIO3 | 5 | hardwired wake pin; `dtoverlay=gpio-shutdown` |
| ULN2003 IN1 | GPIO26 | 37 | default build's stepper driver — see §4.1 |
| ULN2003 IN2 | GPIO19 | 35 | |
| ULN2003 IN3 | GPIO5 | 29 | |
| ULN2003 IN4 | GPIO6 | 31 | |
| IMU SDA (optional) | GPIO22 | 15 | `i2c-gpio` bus 3 — GPIO2/3 (hw I2C) are unavailable, GPIO3 is the power button |
| IMU SCL (optional) | GPIO27 | 13 | `i2c-gpio` bus 3 |
| 5V (LiDAR VCC, ULN2003 VCC, Pi power in) | 5V pins | 2, 4 | single rail — see §4.1, no boost converter in the default build |
| GND (common) | GND | 6, 9, 14, 20, 25, 30, 34, 39 | tie LiDAR GND, ULN2003 GND, button GND all to Pi GND |

**If you upgrade to the optional NEMA17 + A4988 path** (§4.2 — needs a
multimeter, not part of the default build): it reuses GPIO26/19 as
DIR/STEP, adds GPIO5/6/13 as MS1/MS2/MS3, GPIO13 (physical pin 33) being
the only pin the default ULN2003 build leaves unused. It also adds its own
3.3V (driver logic VDD, pin 1 or 17) and a boost-converter GND to the
common ground.

## 4. Motion system

### 4.1 Default build: 28BYJ-48 + ULN2003 (no multimeter, no soldering)

This is the build BUILD.md walks through. The ULN2003 board just switches
4 GPIO outputs to the motor's 4 coils in sequence (`src/stepper_driver.py`'s
`ULN2003` class) — there's no current limit to set and nothing to measure,
unlike a bipolar driver. It runs natively at 5V, so **the whole build is a
single 5V rail**: battery → Pi → (Pi's own 5V GPIO pins) → LiDAR + ULN2003.
No boost converter anywhere.

- **Direct drive, no gearbox.** Same reasoning as PiLiDAR's geared design,
  simplified: the 28BYJ-48's own internal ~64:1 gearbox already gives
  ~4096 steps/rev = 0.088°/step at its output shaft — finer than the
  LiDAR's native ~0.8° vertical resolution — and has enough torque for a
  few-hundred-gram printed mast without any additional external gearing.
  See [PRINTS.md](PRINTS.md) for the mechanical layout.
- **The lazy-susan bearing carries the load, not the motor shaft** — the
  platter sits on the hardware bearing; the motor connects via a printed
  hub that only has to transmit torque, keeping side-load off the motor's
  small internal bearings.
- **The motor's cable plugs directly into the ULN2003 board's onboard
  socket** — no crimping, no soldering, it's sold as a matched pair.
- **Torque/speed margin is real but smaller than a NEMA17's** (roughly
  1/10th the holding torque) — see [BOM.md](BOM.md#optional-upgrades-not-included-in-the-157-total)
  for when that matters and the NEMA17 upgrade path below.

### 4.2 Optional upgrade: NEMA17 + A4988 (needs a multimeter)

Not part of the default build — described here for when/if you pick up a
multimeter and want more torque/speed margin. `src/stepper_driver.py`'s
`A4988` class and `models/motor_hub_nema17.scad` already support it; set
`STEPPER.DRIVER` to `"A4988"` in `config.json` to switch.

- **Direct drive, no gearbox.** At 16× microstepping a NEMA17 alone gives
  3200 microsteps/rev = 0.1125°/step, finer than the LiDAR's native ~0.8°
  resolution, with roughly 10× the torque this load needs even ungeared —
  no need for PiLiDAR's 3D-printed planetary reduction.
- **Microstep truth table** (MS1/MS2/MS3 → resolution), standard A4988:

  | MS1 | MS2 | MS3 | Microsteps |
  |---|---|---|---|
  | Low | Low | Low | 1 (full step) |
  | High | Low | Low | 2 |
  | Low | High | Low | 4 |
  | High | High | Low | 8 |
  | High | High | High | 16 ← used |

- **Current limit (Vref) — this is the step that needs a multimeter.** Set
  the driver's onboard trimpot for **0.5 A/phase** — comfortable torque
  margin for this load without wasting battery power as heat. Formula for
  the common 0.05 Ω sense-resistor A4988 breakout (verify your board's
  sense resistor against its silkscreen/datasheet before trusting this
  number): `I_limit = V_ref × 2.5`, so `V_ref = I_limit / 2.5 = 0.2 V`.
  Measure with a multimeter between the trimpot wiper and GND, motor
  **disconnected**, before wiring it up. Get this wrong and you either
  stall the motor (limit too low) or overheat the driver (limit too high) —
  this is precisely the failure mode the default ULN2003 build has no
  equivalent of.
- **SLEEP/RESET/ENABLE.** Bridge `SLEEP` to `RESET` with a short jumper
  directly on the driver board, tie that joined pair to the driver's logic
  `VDD` (3.3V), and tie `ENABLE` (active-low) straight to `GND`.
- **VMOT (motor power) — the other multimeter step.** 12V from a boost
  converter (e.g. MT3608, 5V→12V), trimmed with its onboard pot and
  **verified with a multimeter before connecting the driver** — cheap
  boost modules can ship set to their maximum (sometimes 28V+). **Never
  run VMOT below ~8V** — the A4988's internal charge pump needs it, and
  the driver can behave unreliably below that, which is why this path
  needs a boost converter at all rather than feeding the driver straight
  off the 5V battery rail.

## 5. Power budget

**Requirement: ≥15 minutes of continuous operation with the LiDAR, stepper,
and Pi all active simultaneously (the actual worst case during a scan).**

This is for the default build: Pi + LiDAR + 28BYJ-48/ULN2003, all off one
5V rail, 10,000 mAh power bank (BOM.md). No boost converter in the loop —
one less conversion-efficiency loss to account for.

### Worst-case bound (the proof)

Deliberately pessimistic on every number, so this is a floor, not an
expectation:

| Load | Draw |
|---|---|
| Pi Zero 2 W (CPU+Wi-Fi, published worst case) | 0.50 A @ 5V = 2.50 W |
| LD19 LiDAR (datasheet current, upper end) | 0.45 A @ 5V = 2.25 W |
| 28BYJ-48/ULN2003 (datasheet worst-case combined coil current) | 0.40 A @ 5V = 2.00 W |
| **Total draw** | **6.75 W** (≈1.35 A @ 5V) |

| | |
|---|---|
| Nominal energy (10 Ah × 3.7 V) | 37.0 Wh |
| × 80% (aged-battery/cold derating) | 29.6 Wh |
| × 80% (USB boost conversion, low end — this is the power bank's own internal 3.7V-cell-to-5V-output conversion, not an external boost converter) | **23.68 Wh usable** |
| ÷ worst-case draw | 23.68 / 6.75 W |
| **Runtime floor** | **210.5 min (3h 31m)** |
| **Margin over the 15-min requirement** | **14.0×** |

### Typical case (practical expectation)

Real (lighter) stepper draw, fresh battery, mixed CPU/Wi-Fi load:

| | |
|---|---|
| Total typical draw | ≈4.75 W |
| Usable energy (100% capacity × 88% conversion) | 32.6 Wh |
| **Typical runtime** | **≈6h 51m** |

In practice, expect a full day of scanning (dozens of individual scans at
~1.5–2 min each, see §6) per charge, not a single 15-minute window — the
14× worst-case margin is that generous mostly because dropping the boost
converter (§4.1) removed both a conversion-efficiency loss and a
several-watt load at the same time.

### If you add the optional NEMA17 + A4988 upgrade (§4.2)

That path reintroduces a boost converter and a heavier motor load — budget
roughly 12-15W for the stepper+driver+boost stage (current-limited to
0.5A/phase, ~80% boost efficiency) instead of the 2W above. Total draw
becomes ≈17-20W worst case, which against the same 23.68Wh usable energy
still clears the 15-minute requirement (≈70-85 min floor, 4.7-5.7× margin)
— just with noticeably less margin than the default build, and only worth
doing once you have the multimeter that path requires anyway.

## 6. Scan duration (informational, not a hard requirement)

At the default resolution (`TARGET_RES: 0.225`, which the 28BYJ-48's 4096
steps/rev turns into 682 steps of ~0.264°/step over the 180° sweep) the
LiDAR itself is the pacing element: 4500 samples/s ÷ 12 samples/package =
375 packages/s, and the scan needs
`682 steps × ~38 packages/step ≈ 25,900 packages`, i.e. **≈69 seconds** per
full 360°×180° scan. Tunable via `TARGET_RES` in `config.json`, exactly
like PiLiDAR. (The optional NEMA17 upgrade's finer 3200 steps/rev would
give ~0.1125°/step and a correspondingly longer scan at the same
`TARGET_RES` — `python3 config.py` prints the actual numbers for whatever
`config.json` currently has configured.)

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
