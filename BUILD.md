# Build Guide

Ordered assembly and test checklist for the default build: 28BYJ-48/ULN2003
motor, breadboard wiring, **no soldering and no multimeter required
anywhere in this document.** Read [BOM.md](BOM.md) (parts),
[ARCHITECTURE.md](ARCHITECTURE.md) (wiring/pinout/power) and
[PRINTS.md](PRINTS.md) (printed parts) first — this doc assumes you have
all the parts in hand and the printed parts already printed.

If you later pick up a multimeter and want to upgrade to the NEMA17 +
A4988 drive train for more torque/speed margin, that's a separate
appendix at the end of this doc, not part of the steps below.

## Tools you'll need

- Phillips screwdriver (M3 hardware)
- Small hex/Allen key matching your motor hub's set screw
- Zip ties (wire routing along the mast), hook-and-loop strap or bungee
  (battery)
- A computer with an SD card reader + [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- Phone/laptop to view the exported PLY (MeshLab, CloudCompare, or any
  point-cloud viewer) for the calibration and final-scan checks

Notably absent: soldering iron, multimeter. Every electrical connection in
this build is a push-fit Dupont wire or a plug-in connector — see BOM.md's
design section for why.

---

## Phase 1 — Print & prepare parts

- [ ] Print all 6 parts from [`models/`](models/) per [PRINTS.md](PRINTS.md)'s
      settings table (you only need `motor_hub_uln2003.scad`, not
      `motor_hub_nema17.scad`, unless you're doing the appendix upgrade)
- [ ] Test-fit the lazy-susan bearing against the base plate and platter's
      slot pattern *before* attaching anything else — the slots are
      deliberately tolerant of exact hole spacing, but confirm your screws
      actually land in material, not thin air
- [ ] Deburr the center bore and all M3 holes (a 3.5-4mm drill bit twisted
      by hand through each hole removes first-layer elephant's-foot
      without a drill press)
- [ ] If using a 1/4"-20 heat-set insert for the tripod mount: these
      normally install with a soldering iron on low heat, which this build
      otherwise avoids entirely. If you don't have one, skip the insert —
      thread a screw directly into the printed boss instead (works fine in
      PETG/PLA for occasional tripod mounting; it just won't take
      re-threading forever), or leave the tripod mount unused and scan
      from a flat surface.

## Phase 2 — Mechanical assembly

- [ ] Screw the lazy-susan bearing's fixed leaf to the base plate (through
      the slots)
- [ ] Screw the bearing's rotating leaf to the platter
- [ ] Set the 28BYJ-48 aside for now — wire it in Phase 3 before final
      mounting, its connector is much easier to reach before the platter
      is on top of it
- [ ] Press the motor hub (`motor_hub_uln2003.scad`) onto the motor's
      output shaft, snug the set screw onto the shaft's flat (or the
      pressed-on coupler — check which your kit has, PRINTS.md § 6) —
      don't fully tighten yet, you'll want to adjust hub height once the
      motor is mounted
- [ ] Mount the motor to the base plate's underside (2 screws), shaft
      pointing up through the center bore
- [ ] Bolt the hub to the platter's underside (3 screws), lower the
      platter onto the bearing, and adjust the motor's position/hub height
      so the shaft engages the hub without binding or side-loading the
      bearing — this is a "loose torque coupling," the bearing carries the
      weight, not the motor shaft (ARCHITECTURE.md § 4.1)
- [ ] Now fully tighten the hub set screw
- [ ] Confirm the motor body clears the ground with the base plate's feet
      resting on a flat surface
- [ ] Bolt the mast's bottom flange to the platter
- [ ] Bolt the LiDAR mount bracket to the mast's top flange
- [ ] Bolt the LD06/LD19 to the bracket (double-check the 3-hole spacing
      matches your unit first — PRINTS.md flags this as unverified)
- [ ] **Sanity-check sensor orientation now, before wiring**: the sensor's
      spin axis should be horizontal (its flat mounting face vertical, its
      round housing facing outward) — see ARCHITECTURE.md § 1's diagram.
      A sensor mounted flat like in a robot vacuum will not produce a
      usable scan.

## Phase 3 — Wiring (all push-fit, no soldering)

Follow [ARCHITECTURE.md's pinout table](ARCHITECTURE.md#3-gpio-pinout)
exactly. Everything below is a female Dupont wire pushed onto a Pi header
pin at one end and either a breadboard row or a component's own pin/socket
at the other — nothing here is soldered or crimped.

- [ ] Seat the breadboard(s) in the base plate's open electronics area
      (adhesive backing or a strip of hook-and-loop tape — see PRINTS.md)
- [ ] Wire the LiDAR's cable: check the connector end first (see BOM.md's
      LiDAR row) — if it's Dupont-style female sockets, push them straight
      onto male jumper wires or Pi header pins; if not, use the JST-to-Dupont
      adapter cable. UART TX → Pi GPIO15 (RX), PWM/MOTOCTL → Pi GPIO18,
      GND → Pi GND, VCC → Pi 5V. **Do not cross TX/RX** — the sensor only
      transmits, so its TX goes to the Pi's RX; there is no wire from any
      Pi TX pin to the sensor.
- [ ] Wire the ULN2003 board: IN1-IN4 → GPIO26/19/5/6, VCC → 5V, GND → GND
      (all from the same rail as the Pi — ARCHITECTURE.md § 4.1's single-rail
      design, nothing to trim or measure)
- [ ] Plug the 28BYJ-48's cable into the ULN2003 board's onboard socket —
      it's keyed, it only goes in one way
- [ ] Push the two button modules' pins into the breadboard, wire one
      between GPIO17 and GND (scan-trigger) and the other between GPIO3
      and GND (power) — both use the Pi's internal pull-ups, no resistor
      needed
- [ ] Optional IMU: SDA→GPIO22, SCL→GPIO27, VCC→3.3V, GND→GND
- [ ] Route all wiring along the mast with zip ties, leaving enough slack
      at the platter/base joint for the full 180° sweep without snagging
- [ ] Zip-tie/strap the power bank to the base plate's strap slots
- [ ] Double-check every connection against the pinout table by eye before
      powering on — this is the "no multimeter" build's substitute for a
      continuity check. Look for: any wire on the wrong pin, any loose
      push-fit connection, and that nothing is bridging two adjacent
      breadboard rows that shouldn't be connected.

## Phase 4 — Software setup

- [ ] Flash Raspberry Pi OS Lite (64-bit, Bookworm or later) to the
      microSD with Raspberry Pi Imager; in the imager's advanced options,
      set hostname, enable SSH, and set your Wi-Fi credentials so you can
      reach it headless
- [ ] Boot the Pi, SSH in, then `sudo raspi-config` or edit
      `/boot/firmware/config.txt` directly to add:
      ```
      dtoverlay=gpio-shutdown
      dtoverlay=pwm-2chan
      ```
      (the first makes GPIO3 a wake/shutdown button per BOM.md's power
      button; the second enables hardware PWM on GPIO18/19 for the LiDAR
      motor-speed control — `src/platform_utils.py` falls back to software
      PWM automatically if you skip this, just with more jitter)
- [ ] If using the optional IMU, also add:
      ```
      dtparam=i2c_arm=off
      dtoverlay=i2c-gpio,bus=3,i2c_gpio_delay_us=1,i2c_gpio_sda=22,i2c_gpio_scl=27
      ```
- [ ] Grant serial port permissions permanently via udev rule (avoids the
      "chmod every boot" hack):
      ```
      sudo sh -c 'echo KERNEL==\"ttyS0\",GROUP=\"dialout\",MODE=\"0660\" > /etc/udev/rules.d/50-ttyS0.rules'
      sudo usermod -a -G dialout $USER
      sudo udevadm control --reload-rules
      sudo reboot
      ```
- [ ] Remove the RPi.GPIO sysfs backend and install the lgpio-backed
      replacement (Bookworm removed the old interface — see
      ARCHITECTURE.md/`src/requirements.txt`):
      ```
      sudo apt remove -y python3-rpi.gpio
      sudo apt update
      ```
- [ ] Clone this repo onto the Pi, then:
      ```
      cd LiDar/src
      python3 -m venv venv --system-site-packages
      source venv/bin/activate
      pip install -r requirements.txt
      ```
- [ ] Check `src/config.json`: `STEPPER.DRIVER` should already be
      `"ULN2003"` (the default) and `LIDAR.DEVICE` should match your sensor
      (`"LD19"` or `"LD06"`)
- [ ] Install the scan-button daemon as a systemd service:
      ```
      sudo tee /etc/systemd/system/lidar-scanner.service <<'EOF'
      [Unit]
      Description=LiDAR Scanner Button Daemon
      After=network.target

      [Service]
      Type=simple
      User=pi
      WorkingDirectory=/home/pi/LiDar/src
      Environment=LG_WD=/tmp
      ExecStart=/home/pi/LiDar/src/venv/bin/python3 /home/pi/LiDar/src/button_daemon.py
      Restart=on-failure

      [Install]
      WantedBy=multi-user.target
      EOF
      sudo systemctl daemon-reload
      sudo systemctl enable --now lidar-scanner.service
      sudo systemctl status lidar-scanner.service
      ```
      (adjust the `pi`/`/home/pi` paths if your username or clone location
      differ)

## Phase 5 — Power-on checks (before the first real scan)

Do these *in order* — each one only makes sense if the previous one
passed. None of these need a multimeter; they're all "does it visibly do
the right thing" checks.

- [ ] Power the Pi alone (motor and LiDAR still unplugged from their
      signal pins, only Pi 5V connected) — confirm it boots and you can
      SSH in
- [ ] Plug in the LiDAR only. Run `python3 src/lidar_driver.py` — you
      should see it print a rotation speed reading within a couple
      seconds. If nothing happens: check the UART wiring isn't
      crossed, check `ls -l /dev/ttyS0` shows `dialout` group access, check
      `dtoverlay=pwm-2chan` is actually in `/boot/firmware/config.txt`
- [ ] Plug in the motor/ULN2003 only. Run `python3 src/stepper_driver.py`
      — the turntable should visibly rotate a few degrees and back. If it
      doesn't move at all: recheck the IN1-IN4 wiring order and that the
      motor's connector is fully seated in the ULN2003 socket. If it
      vibrates or judders instead of turning smoothly: two of the IN1-IN4
      wires are likely swapped — swap any adjacent pair and retry.
- [ ] Press the scan button once with both connected. Confirm
      `systemctl status lidar-scanner` shows it launched `scan.py`, and
      that a new folder appears under `src/scans/`.

## Phase 6 — Calibration

- [ ] **PWM speed calibration** (only if you enabled hardware PWM — skip
      if you never enabled `pwm-2chan`, or if your board already spins at
      a reasonable default rate): run `python3 src/calibrate_pwm.py`,
      paste the printed `PWM_COEFFS` into `config.json`
- [ ] **Mechanical offset calibration**: run
      `python3 src/calibrate_mechanical.py --angle 90 --res 1.0` pointed at
      a real corner of a room (two walls meeting at 90°, ideally with a
      visible floor/wall line). Open the resulting PLY. If the walls look
      doubled, curved, or non-perpendicular:
      - measure your actual sensor offset from the mast axis (the physical
        dimension the `lidar_mount.scad` bracket sets, PRINTS.md § 4) and
        update `Y_OFFSET`/`Z_OFFSET` in `config.json`
      - if the walls are straight but not perpendicular, adjust
        `LIDAR_OFFSET_ANGLE` in small (~0.5°) steps
      - re-run and re-check until walls read flat and square. This is the
        same hand-fitting process PiLiDAR's own reference build uses —
        there's no shortcut, but it only needs doing once per assembled
        unit.

## Phase 7 — First full scan + acceptance checklist

- [ ] Run `python3 src/scan.py` (or press the physical button) in a room
      with some clutter/furniture (flat empty rooms are a bad first test —
      you can't tell noise from a genuinely flat wall)
- [ ] Confirm the scan completes without a `[WARNING] merged point cloud
      is empty` message and without the process dying partway through
- [ ] Confirm `scans/<timestamp>/<timestamp>.ply` exists and its file size
      is more than a few KB (an empty/near-empty PLY is a red flag, not a
      quiet room)
- [ ] Open the PLY in MeshLab/CloudCompare/any viewer:
  - [ ] Walls and furniture are recognizable, not a shapeless blob
  - [ ] The colored (intensity-gradient) point cloud shows visible
        structure, not uniform noise
  - [ ] No obvious double-imaging (the same wall showing up twice, offset
        — usually a mechanical-offset calibration issue, back to Phase 6)
- [ ] Time a full scan and confirm it's in the ballpark of
      [ARCHITECTURE.md § 6](ARCHITECTURE.md#6-scan-duration-informational-not-a-hard-requirement)'s
      ~69 second estimate at default settings — a scan taking 5-10x longer
      usually means the LiDAR's actual rotation speed is off from
      `TARGET_SPEED`, back to the PWM calibration
- [ ] Battery runtime spot-check: fully charge the power bank, run 3-4
      back-to-back scans with only a few seconds between them, confirm the
      bank isn't reporting a critically-low charge — this is a sanity
      check on [ARCHITECTURE.md's power budget](ARCHITECTURE.md#5-power-budget),
      not a substitute for it

## Troubleshooting quick reference

| Symptom | Likely cause |
|---|---|
| `RuntimeError: Failed to add edge detection` on button daemon start | Old `RPi.GPIO` sysfs backend still installed — see Phase 4's `apt remove python3-rpi.gpio` step |
| LiDAR never syncs / constant CRC warnings | Wrong baud rate in `config.json` for your device, or a bad/loose UART connection |
| Motor vibrates/judders but doesn't turn | Two of the IN1-IN4 wires are swapped — check the order against ARCHITECTURE.md's pinout table |
| Motor turns but skips steps under load | 28BYJ-48 is near its torque limit — check nothing is binding in the bearing/hub coupling before assuming the motor is faulty |
| Scan runs but PLY is empty | Check `lidar.z_angles` isn't empty in a manual `scan.py` run — usually means the stepper callback never fired, i.e. `max_packages` was reached before one full `out_len` revolution completed (a resolution/config mismatch) |
| Point cloud is a flat line or plane, not 3D | Sensor is mounted with its spin axis vertical instead of horizontal — recheck Phase 2's orientation sanity check |
| Everything works but drifts/leans after a few scans | PLA mast creep under load — see PRINTS.md's material recommendation, reprint the mast in PETG |

---

## Appendix: upgrading to NEMA17 + A4988 (needs a multimeter)

Only do this once you have a multimeter — the whole point of the default
build above is that you don't need one. See
[ARCHITECTURE.md § 4.2](ARCHITECTURE.md#42-optional-upgrade-nema17--a4988-needs-a-multimeter)
for the full wiring/tuning detail; this is just how it slots into the
phases above:

- **Phase 1**: print `motor_hub_nema17.scad` instead of (or in addition
  to) `motor_hub_uln2003.scad`
- **Phase 2**: same mechanical steps, but the NEMA17 mounts with 4 screws
  instead of 2
- **Phase 3**: wire the A4988 instead of the ULN2003 (DIR→GPIO26,
  STEP→GPIO19, MS1/MS2/MS3→GPIO5/6/13, logic VDD→3.3V), bridge SLEEP to
  RESET, tie ENABLE to GND. Add a boost converter: power it alone first
  and **trim its output to 12.0V with a multimeter** before connecting it
  to anything. With the motor still disconnected, power the A4988 and
  **set its current-limit trimpot for 0.5V at Vref**, verified with the
  multimeter. Only then connect the NEMA17's coil wires.
- **Phase 4**: set `STEPPER.DRIVER` to `"A4988"` in `config.json`
- **Phase 5**: the stepper power-on check becomes "if it doesn't move,
  recheck SLEEP/RESET and ENABLE-to-GND wiring; if it skips/stalls, your
  Vref current limit is likely too low"
