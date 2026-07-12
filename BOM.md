# Bill of Materials

This scanner is a budget-hardware remix of [PiLiDAR](https://github.com/PiLiDAR/PiLiDAR)
(Raspberry Pi + LDRobot 2D LiDAR + stepper turntable → 3D point cloud). The HQ
camera / panorama-texturing half of PiLiDAR is dropped entirely — this is a
LiDAR-only scanner that exports intensity-shaded PLY point clouds.

**Builder constraints this BOM is designed around: no soldering, no
multimeter, budget cap $175, every part on Amazon.** Every connection below
is push-fit (breadboard + Dupont jumpers + plug-in connectors) and nothing
requires measuring a voltage or current to set up — see
[the no-solder/no-multimeter design section](#design-for-no-soldering-and-no-multimeter)
for what that changed from a typical stepper-driven build. See
[Parts.md](Parts.md) for just the shopping list with no explanation.

## TL;DR

| | |
|---|---|
| **Total** | **$173** (of a $175 cap — see [buffer note](#whats-the-2-of-headroom-for)) |
| Sourcing | 100% Amazon, Prime-eligible |
| Turntable drive | 28BYJ-48 + ULN2003 — plug-in connector, no current-limit tuning, no multimeter |
| Wiring | Solderless breadboard + Dupont jumpers throughout |
| Battery runtime, worst case / typical | see [ARCHITECTURE.md § Power budget](ARCHITECTURE.md#5-power-budget) |

## Design for no soldering and no multimeter

The stepper-driven-turntable design pattern most DIY LiDAR scanners
(including PiLiDAR itself) use is built around a NEMA17 + A4988 driver,
which needs two things this BOM specifically avoids:

1. **A4988's current limit is set with a trimpot, measured with a
   multimeter** (a wrong-by-a-lot setting can overheat the driver or
   stall the motor). No multimeter, no safe way to set it.
2. **NEMA17 needs 9-12V**, which means a boost converter between the 5V
   battery and the driver — another component whose output voltage you
   trim and verify with a multimeter before it's safe to connect to
   anything.

Both are gone from this build. Instead:

- **Motor: 28BYJ-48 + ULN2003**, not NEMA17 + A4988. The ULN2003 board
  just switches 4 GPIO signals to the motor coils directly — there's no
  current limit to set, nothing to measure, nothing to trim. It runs
  natively at 5V, so **the boost converter disappears too** — everything
  in this build (Pi, LiDAR, motor) runs off one 5V rail. This does trade
  away some torque/speed margin vs. a NEMA17 — see
  [ARCHITECTURE.md § 4](ARCHITECTURE.md#4-motion-system) for why that's a
  fine tradeoff at this load, and how to upgrade later if you ever do pick
  up a multimeter.
- **Wiring: a solderless breadboard + Dupont jumper wires**, not perfboard.
  The Pi Zero 2 **WH**'s pre-soldered header pins take push-on female
  Dupont wires directly — no soldering iron touches anything in this
  build. The LiDAR module's cable and the ULN2003-to-28BYJ48 connector are
  both pre-terminated plug-in connectors out of the box (see the LiDAR
  line item below for the one thing to double check when it arrives).
- **No voltage/current measurement anywhere in the build.** BUILD.md's
  power-on checklist is entirely "does it visibly move / does it print a
  reading" checks, not multimeter readings.

## Everything on Amazon

Every part below is sourced on Amazon, Prime-eligible — the whole BOM
should ship free in 1-2 days, likely in one or two boxes. This trades
away the cheaper overseas LiDAR sourcing (~$67 via a China-based reseller
like sunsky-online, 1-3 week shipping, no easy returns) for Prime speed
and Amazon's return policy — worth it on its own for the LiDAR
specifically, since a DOA sensor is much harder to diagnose without a
multimeter, and much easier to just exchange.

## Parts list — $173

| Part | Price | Source | Notes |
|---|---|---|---|
| **LDRobot LD19 LiDAR** ("D300" kit: sensor + cable) | **$90** | [Amazon: WayPonDEV FHL-LD19](https://www.amazon.com/DTOF-D300-Distance-Obstacle-Education/dp/B0B1V8D36H) (also sold as [Waveshare D300](https://www.amazon.com/Waveshare-DTOF-LIDAR-LD19-Omni-Directional/dp/B0B3RWKJ1P) — compare current prices, these fluctuate more than most Amazon listings, seen $90-170) | 4500 samples/s, 0.02–12 m, 5V UART+PWM. **Check the product photos before ordering**: you want a cable ending in loose/Dupont-style female connector pins (the standard way these wire to a Pi, no tool needed). If yours instead ends in a bare-wire or unfamiliar connector, search Amazon for a small "JST to Dupont adapter cable" (~$7) — not included in the total above since most listings don't need it. LD06 is a drop-in alternative the code already supports. |
| **Raspberry Pi Zero 2 WH** (pre-soldered header — important, this is what makes the "no soldering" claim work) | **$15** | [Amazon](https://www.amazon.com/Raspberry-Pi-Zero-2-WH/dp/B0DB2JBD9C) | Quad-core Cortex-A53, 40-pin GPIO, Wi-Fi for headless scan pull-off. Do not buy the header-less "W" — you'd need to solder the header on yourself. |
| **microSD card, 32 GB, A1/A2** | **$6** | [Amazon](https://www.amazon.com/SanDisk-32GB-MicroSDHC-Memory-Card/dp/B003WGJYCY) | 16 GB would work too; 32 GB cards are cheap enough to just default to. |
| **4" square lazy-susan turntable bearing** (2-pack) | **$9** | [Amazon: 2-pack](https://www.amazon.com/Turntable-Bearings-Hardware-Rotating-Bearing/dp/B09R1S2JNB), or [single](https://www.amazon.com/Square-Inch-Susan-Turntable-Bearing/dp/B017OYZAFE), or [8-pack](https://www.amazon.com/Hardware-Rotating-Bearing-Capacity-Turntable/dp/B08CY2P8KZ) | Carries the platter's radial/thrust load — screws only, no soldering. **This is a commodity part**: any "4 inch square lazy susan turntable bearing" listing works (they're all the same ~4"/102mm zinc-plated stamped-steel design), so if the linked ones are out of stock, [search Amazon](https://www.amazon.com/s?k=4+inch+square+lazy+susan+turntable+bearing) and pick any in-stock 4" square one. Exact mounting-hole positions vary by brand, which is why the printed plates use slots + transfer-marking (PRINTS.md, BUILD.md) instead of assuming a hole pattern. |
| **28BYJ-48 + ULN2003 stepper kit** (2-set) | **$9** | [Amazon](https://www.amazon.com/KOOKYE-28BYJ-48-Stepper-ULN2003-Arduino/dp/B019TOJRC4) | Motor's cable plugs directly into the ULN2003 board's onboard socket — no crimping, no soldering. Runs natively at 5V, no current limit to set. 2-set = a spare. |
| **USB-C PD power bank, 10,000 mAh** | **$18** | [Amazon](https://www.amazon.com/Anker-Portable-Charger-Charging-Battery/dp/B0CZ9M6X8Q) | Single 5V rail powers the Pi directly; the Pi's own 5V GPIO pins in turn power the LiDAR and motor (standard practice, see ARCHITECTURE.md) — no boost converter needed anywhere in this build. |
| **Half-size solderless breadboard** (2-pack) | **$7** | [Amazon](https://www.amazon.com/s?k=half+size+solderless+breadboard+2+pack) | Central wiring hub. Half-size (not full-size) specifically because it fits the base plate's electronics zone alongside the bearing — see PRINTS.md. |
| **Tactile push-button modules** (pin-header breakout, pack) | **$6** | [Amazon](https://www.amazon.com/s?k=tactile+push+button+module+breakout+3pin) | Small PCB with the switch already on it — pushes into the breadboard or connects via Dupont wire, unlike a bare panel-mount switch which typically wants solder or crimp terminals. Need 2: scan-trigger + power. |
| **Dupont jumper wire kit** (M-M / M-F / F-F, assorted lengths) | **$7** | [Amazon](https://www.amazon.com/s?k=dupont+jumper+wire+kit+mm+mf+ff) | All signal wiring in this build is one of these three cable types. Get the multi-pack, you'll use more than you expect. |
| **M3 fastener assortment** (screws, standoffs, nuts) | **$6** | [Amazon](https://www.amazon.com/s?k=m3+screw+standoff+nut+assortment+kit) | Mechanical assembly only — a screwdriver, not a soldering iron. |

<sub>Treat every price in this document as "verified as of 2026-07-07,
reverify before ordering" — ±5–10% week-to-week retail variance is normal
for most of these parts, but the LiDAR specifically has swung $90-170
across resellers in the same search session, so compare listings before
buying it in particular. Shipping is free on all parts with Prime.</sub>

### What's the $2 of headroom for?

Not much — $173 against a $175 cap leaves only $2 of slack, almost all of
which went into paying the Amazon/Prime premium on the LiDAR (~$23 more
than the cheapest overseas sourcing). If the LiDAR listing you find is
priced above the $90 used here, something else in this list has to come
down to compensate — the [cost-reduction levers](#further-cost-reduction-levers-not-reflected-in-the-173-total)
below are the places with room to give.

### Assumed already on hand (not in the $173 total — check before ordering)

The parts table above is the complete set of wires and electronics *for
the scanner itself* — every electrical connection is either a Dupont
jumper from the kit or a plug-in cable included with its part. It assumes
you already own these common items; check before ordering and add any
you're missing:

- **A micro-USB cable** to power the Pi from the power bank. The Pi Zero
  2 W's power port is **micro-USB, not USB-C**, and the power bank won't
  necessarily include that cable. Nearly every household has one from an
  older phone or gadget; if not, ~$5–6
  ([Amazon](https://www.amazon.com/s?k=usb+a+to+micro+usb+cable)).
- **A way to get the microSD card into your computer** for the one-time
  OS flash — an SD slot (the SanDisk card usually ships with a full-size
  SD adapter) or a ~$7 USB reader
  ([Amazon](https://www.amazon.com/s?k=usb+sd+card+reader)).
- **Zip ties and a hook-and-loop strap or bungee** (wire routing along
  the mast, battery mounting — BUILD.md's tools list).
- Phillips screwdriver and a small hex/Allen key.

## Optional upgrades (not included in the $173 total)

Out of scope per the brief ("HQ camera / RGB coloring is optional — drop
it to hit budget") but documented as fork points since the code has hooks
for them.

| Upgrade | Adds | Cost | What it buys |
|---|---|---|---|
| **IMU (GY-521 / MPU6050)** | +$7 ([Amazon](https://www.amazon.com/HiLetgo-MPU-6050-Accelerometer-Gyroscope-Converter/dp/B078SS8NQV)) | I2C tilt sensor, pin-header — same solderless Dupont-wire connection as everything else here | Auto-levels the point cloud if the tripod/ground isn't perfectly level. `src/imu_driver.py` supports it; set `ENABLE_IMU: true` in `config.json`. |
| **Basic RGB coloring** | +$20–30 (Pi Camera Module 3, [Amazon](https://www.amazon.com/s?k=raspberry+pi+camera+module+3)) | Per-step photo, angular color lookup | PiLiDAR's full build uses a $60 HQ camera + M12 lens + Hugin panorama stitching. Out of scope here; a cheap Pi Camera Module taking one photo per stepper stop gets *rough* RGB instead of intensity-grayscale. Not implemented in `src/` — noted as a fork point. |
| **NEMA17 + A4988 motor upgrade** | net +$10ish, **requires acquiring a multimeter** | More torque/speed margin (~10× holding torque) | The "standard" DIY-scanner drive train this BOM deliberately avoids — see the design section above. `src/stepper_driver.py`'s `A4988` class and `models/motor_hub_nema17.scad` already support this if you ever pick up a multimeter; [ARCHITECTURE.md § 4.2](ARCHITECTURE.md#42-optional-upgrade-nema17--a4988-needs-a-multimeter) and BUILD.md's appendix have the setup steps. Not recommended as a first build without one. |
| **STL-27L sensor instead of LD19** | +$90–95 | 21,600 samples/s vs 4,500 (~5×), same 12 m range | Meaningfully denser clouds, but the sensor alone costs more than half this entire build. Only makes sense if you've abandoned the budget constraint entirely. |

## Further cost-reduction levers (not reflected in the $173 total)

If the LiDAR listing you find runs above $90 and you need to claw back
some budget:

- **Skip the spare 28BYJ-48/ULN2003 set**: −$4 or so. Fine if you're
  confident in your wiring.
- **16 GB instead of 32 GB microSD**: −$1 to −$2.
- **Shop around between the two Amazon LiDAR listings above** (and any
  other "D300"/"FHL-LD19" listings you find) — this single line item has
  the widest price spread of anything in the BOM, so a few minutes of
  comparing could easily be worth more than every other lever combined.
