# Bill of Materials

This scanner is a budget-hardware remix of [PiLiDAR](https://github.com/PiLiDAR/PiLiDAR)
(Raspberry Pi + LDRobot 2D LiDAR + stepper turntable → 3D point cloud). The HQ
camera / panorama-texturing half of PiLiDAR is dropped entirely — this is a
LiDAR-only scanner that exports intensity-shaded PLY point clouds.

## TL;DR

| | Recommended build | Budget build |
|---|---|---|
| **Total** | **$150** | **$135** |
| Turntable drive | NEMA17 + A4988 (geared, more torque margin) | 28BYJ‑48 + ULN2003 (no boost converter needed) |
| Battery runtime, worst case / typical | 72 min / ≈3h55m (10,000 mAh) | 105 min / ≈3h25m (5,000 mAh) |
| Both clear the 15-min requirement (worst case) by | **4.8×** | **7.0×** |

Full derivation in [ARCHITECTURE.md § Power budget](ARCHITECTURE.md#5-power-budget).

## Assumption: ≤$100 is not achievable — here's why

The task's target is ≤$100, cap $150. After pricing every part against current
listings (checked 2026-07-07), **≤$100 is not reachable** for a build that
actually meets the stated quality bar (LD06/LD19-class sensor, stepper-driven
full 360°, USB-C rechargeable, portable), for one simple reason:

> The LiDAR sensor alone costs **$65–70** from the cheapest credible source, and
> a Pi + stepper/turntable + rechargeable power system that isn't a fire
> hazard or a paperweight costs another **$65–85** even at the leanest
> component choices. That floor is already $130–155 before any margin.

This isn't a "nice-to-have quality upgrade costs extra" situation (which is
the case the ≤$100 vs $100–150 tiering in the brief anticipates) — it's that
the cheapest *reliable* version of this exact spec already lands in the
$130–155 band. So instead of an artificial ≤$100 tier that would require
cutting something essential (the sensor, the battery, or the motor), this
BOM gives you:

- **Budget build ($135)** — every corner that can be cut without hurting
  reliability or the 15-minute runtime requirement, cut.
- **Recommended build ($150, at the cap)** — the PiLiDAR-faithful motor
  choice (NEMA17/A4988, matching the reference project) and more runtime/duty
  cycle margin.

Both hit the full spec (sensor class, resolution, PLY export, ≥15 min
runtime). The difference is mechanical margin and how faithfully the drive
train follows PiLiDAR's own reference design, not scan quality per se — see
[Quality difference](#quality-difference-recommended-vs-budget) below.

If you can tolerate a used/pulled sensor from eBay (robot-vacuum repair
parts, condition unverified) the LiDAR line can drop to ~$30–45, which would
pull the Budget build to ~$93–113 ($135 − the $67 sourced-LiDAR line + a
$25–45 used one). That's a real option; it's called out
under [cost-reduction levers](#further-cost-reduction-levers-not-in-the-totals-above)
rather than baked into the default BOM because "condition unknown, no
warranty, connector sometimes needs rework" isn't something this document can
verify or reproduce for you.

## Sourcing rule

Per the brief, the **LiDAR is sourced wherever it's cheapest** (it is *not*
counted against the "majority on Amazon" rule). **Every other part below is on
Amazon** — that's the one, explicitly-allowed exception, flagged here and
nowhere else.

---

## Shared parts (identical in both builds) — $114

| Part | Price (approx.) | Source | Notes |
|---|---|---|---|
| **LDRobot LD19 LiDAR** ("D300" dev-kit: sensor + adapter PCB + cable) | **$67** | [sunsky-online](https://www.sunsky-online.com/p/DIY0289/Waveshare-D300-Developer-Kit-DTOF-Laser-Ranging-Sensor-360-Omni-Directional-Lidar-UART-Bus.htm) | 4500 samples/s, 0.02–12 m, 5 V UART+PWM. Also sold as [Amazon: Waveshare D300](https://www.amazon.com/Waveshare-DTOF-LIDAR-LD19-Omni-Directional/dp/B0B3RWKJ1P) or [Amazon: WayPonDEV FHL-LD19](https://www.amazon.com/DTOF-D300-Distance-Obstacle-Education/dp/B0B1V8D36H) for **$90–170** if you want one-stop Amazon checkout instead — same part, Amazon resellers mark these up heavily. LD06 (see [ARCHITECTURE.md](ARCHITECTURE.md)) is a drop-in alternative the code already supports. STL-27L (~$160, [DFRobot](https://www.dfrobot.com/product-2726.html)) is a real quality upgrade (21,600 samples/s vs 4,500) but its price alone blows the $150 cap, so it's out of scope here. |
| **Raspberry Pi Zero 2 WH** (pre-soldered header) | **$15** | [Amazon](https://www.amazon.com/Raspberry-Pi-Zero-2-WH/dp/B0DB2JBD9C) | Official MSRP is $15 for the header-less **W**; the **WH** adds pre-soldered GPIO pins for about the same money on a good day — check both listings. Quad-core Cortex-A53, 40-pin GPIO, Wi-Fi for headless scan pull-off. |
| **microSD card, 32 GB, A1/A2** | **$6** | [Amazon](https://www.amazon.com/SanDisk-32GB-MicroSDHC-Memory-Card/dp/B003WGJYCY) | 16 GB is plenty for the OS + hundreds of scans (each PLY is a few MB), 32 GB cards are cheap enough to just default to. |
| **4" lazy-susan turntable bearing** (2-pack) | **$9** | [Amazon](https://www.amazon.com/FKG-Inch-Susan-Bearing-Turntable/dp/B08B137XQL) | Carries the platter's radial/thrust load so the motor shaft only has to transmit torque, not hold the mast up. |
| **Momentary push-buttons** (5-pack) | **$4** | [Amazon](https://www.amazon.com/s?k=momentary+push+button+switch+5mm) | Need 2: scan-trigger + power. |
| **Hookup wire + Dupont jumpers** | **$5** | [Amazon](https://www.amazon.com/s?k=dupont+jumper+wire+kit+22awg) | Motor/driver/battery wiring. |
| **M3 fastener assortment** (screws, standoffs, nuts) | **$5** | [Amazon](https://www.amazon.com/s?k=m3+screw+standoff+nut+assortment+kit) | Buy once, re-use forever. |
| **Small perfboard / terminal-block strip** | **$3** | [Amazon](https://www.amazon.com/s?k=perfboard+terminal+block+strip) | Tidy hub for the button/motor/battery wiring. |

## Tier-specific parts

| Part | Recommended | Budget |
|---|---|---|
| **Turntable motor** | NEMA17 stepper, $9 ([Amazon](https://www.amazon.com/SIMAX3D-Nema17-Stepper-Motor/dp/B09XX98FKM)) + A4988 driver 2-pack, $7 ([Amazon](https://www.amazon.com/HiLetgo-Stepstick-Stepper-Printer-Compatible/dp/B07BND65C8)) + MT3608 boost converter (5V→12V for the motor rail), $4 ([Amazon](https://www.amazon.com/MT3608-Converter-Adjustable-Voltage-Regulator/dp/B0BGLGL9RV)) = **$20** | 28BYJ-48 + ULN2003 geared stepper, 2-set kit, **$9** ([Amazon](https://www.amazon.com/KOOKYE-28BYJ-48-Stepper-ULN2003-Arduino/dp/B019TOJRC4)) — runs natively off 5 V, no boost converter needed |
| **USB-C PD power bank** | 10,000 mAh, **$16** ([Amazon](https://www.amazon.com/Anker-Portable-Charger-Charging-Battery/dp/B0CZ9M6X8Q)) | 5,000 mAh, **$12** ([Amazon](https://www.amazon.com/s?k=5000mah+usb-c+pd+power+bank+slim)) |
| **Tier subtotal** | **$36** | **$21** |
| **Grand total (shared $114 + tier)** | **$150** | **$135** |

<sub>Treat every price in this document as "verified as of 2026-07-07,
reverify before ordering" — ±5–10% week-to-week retail variance is normal
for these parts. Prices exclude tax and shipping. The LiDAR ships from
overseas — pick a free/slow shipping option unless you're in a hurry.</sub>

---

## Quality difference: Recommended vs. Budget

Both builds meet the hard requirements (sensor class, resolution, PLY
export, ≥15 min runtime, portability). The difference is margin, not
capability:

1. **Torque/reliability margin.** A NEMA17 bipolar stepper has roughly
   10× the holding torque of a 28BYJ-48, geared down further by A4988
   microstepping. It's overkill for spinning a ~300–500 g printed mast, which
   is the point — it means print-quality variance, a slightly heavier future
   payload (e.g. an added camera), or a stiffer/higher-friction bearing than
   assumed will never stall the motor. The 28BYJ-48 works fine at this load
   (it's a common choice for light DIY turntables) but has less headroom if
   your printed parts come out heavier or your bearing is stiffer than
   expected.
2. **Runtime margin, not runtime compliance.** See
   [ARCHITECTURE.md § Power budget](ARCHITECTURE.md#5-power-budget) — even
   under deliberately pessimistic assumptions, the Budget tier's 5,000 mAh
   bank clears the 15-minute requirement by 7.0×. The Recommended tier's
   bigger bank buys more scans per charge in the field (a full afternoon of
   scanning vs. a couple of hours at the typical-case draw), not "the Budget
   build might not make it" — both tiers clear the hard requirement
   comfortably.
3. **Spare A4988.** The 2-pack means a burnt-out driver (the most common
   stepper-wiring failure — happens if you hot-plug the motor connector)
   doesn't strand the whole build. The 28BYJ-48/ULN2003 kit is bought as a
   2-set for the same reason.

Neither difference affects point-cloud density, range, or PLY output — those
are governed by the LiDAR sensor and scan resolution setting, which are
identical in both builds.

---

## Optional upgrades (not included in either total above)

These are explicitly out of scope per the brief ("HQ camera / RGB coloring is
optional — drop it to hit budget") but are documented here as upgrade paths
since the code has hooks for both.

| Upgrade | Adds | Cost | What it buys |
|---|---|---|---|
| **IMU (GY-521 / MPU6050)** | +$7 ([Amazon](https://www.amazon.com/HiLetgo-MPU-6050-Accelerometer-Gyroscope-Converter/dp/B078SS8NQV)) | I2C tilt sensor | Auto-levels the point cloud if the tripod/ground isn't perfectly level. `src/imu_driver.py` supports it; set `ENABLE_IMU: true` in `config.json`. |
| **Basic RGB coloring** | +$20–30 (Pi Camera Module 3, [Amazon](https://www.amazon.com/s?k=raspberry+pi+camera+module+3)) | Per-step photo, angular color lookup | PiLiDAR's full build uses a $60 HQ camera + M12 lens + Hugin panorama stitching for photoreal texture. That's out of budget here. A cheap Pi Camera Module taking one photo per stepper stop (the same idea PiLiDAR's own code has commented out as a debug feature) and coloring points by nearest-angle photo gets you *rough* RGB instead of intensity-grayscale, without the stitching pipeline. Not implemented in `src/` — noted as a fork point. |
| **STL-27L sensor instead of LD19** | +$90–95 | 21,600 samples/s vs 4,500 (~5×), same 12 m range | Meaningfully denser clouds, but the sensor alone costs more than this entire Budget build. Only makes sense if you've abandoned the budget constraint entirely. |

## Further cost-reduction levers (not in the totals above)

If you want to push toward $93–113 (see above) and can accept the tradeoffs:

- **Used/pulled LD06/LD19 module from eBay** (harvested from a broken robot
  vacuum): ~$25–45. These are the exact same sensors OEM'd into many
  robot-vacuum models. Condition, connector, and firmware version are not
  guaranteed — verify the UART protocol matches (230400 baud / 12
  points-per-packet framing, see [ARCHITECTURE.md](ARCHITECTURE.md)) before
  committing to the build around it.
- **Skip the spare A4988 / 28BYJ-48 set**: −$4 to −$7. Fine if you're
  confident in your wiring.
- **16 GB instead of 32 GB microSD**: −$1 to −$2. Negligible but free money.
- **3D-print your own M3 heat-set-insert alternative** (nut traps in the
  print instead of buying inserts): already assumed above, no separate line
  item for inserts.
