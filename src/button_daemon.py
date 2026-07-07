"""
Scan-trigger button daemon: listens on the scan button's GPIO pin and
launches scan.py as a subprocess on each press, ignoring presses while a
scan is already running. Meant to run as a systemd service so the
scanner is a one-button-press appliance -- see BUILD.md for the service
unit file and enable/start commands.

Adapted from PiLiDAR's gpio_interrupt.py
(https://github.com/PiLiDAR/PiLiDAR), (c) Philip Gutjahr, CC BY-NC-SA 4.0.
"""

import subprocess
import time
import os

import RPi.GPIO as GPIO

from config import Config

SCAN_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan.py")

_process = None


def _start_callback(_channel):
    global _process
    if _process is not None and _process.poll() is None:
        print("Scan already running, ignoring button press.")
        return

    _process = subprocess.Popen(["nice", "-n", "-10", "python3", SCAN_SCRIPT])
    print("Scan started, pid:", _process.pid)


if __name__ == "__main__":
    config = Config()
    scan_pin = config.get("BUTTONS", "SCAN_PIN")

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(scan_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(scan_pin, GPIO.FALLING, callback=_start_callback, bouncetime=200)

    print(f"Waiting for scan button on GPIO{scan_pin}...")
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        GPIO.cleanup()
