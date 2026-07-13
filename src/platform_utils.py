"""
Platform helpers: serial port + PWM initialization for the Raspberry Pi.

Adapted from PiLiDAR (https://github.com/PiLiDAR/PiLiDAR), (c) Philip
Gutjahr, CC BY-NC-SA 4.0 -- trimmed to the Raspberry-Pi-only path (no
Windows/MCU branches) since this project targets a single fixed platform.
"""

import os
import sys


def get_platform():
    if sys.platform.startswith("win32"):
        return "Windows"
    if sys.platform.startswith("darwin"):
        return "Mac"
    machine = os.uname().machine
    if "aarch64" in machine or "armv7" in machine:
        return "RaspberryPi"
    return "Linux"


def init_serial(port="/dev/ttyS0", baudrate=230400):
    """Works for the GPIO UART (/dev/ttyS0) or a USB-serial adapter
    (/dev/ttyUSB0) used for bench testing -- same call either way."""
    import serial
    return serial.Serial(port=port, baudrate=baudrate, timeout=1.0,
                          bytesize=8, parity="N", stopbits=1)


class SoftPWM:
    """RPi.GPIO software-PWM fallback with the same start/change_duty_cycle/stop
    interface as rpi_hardware_pwm.HardwarePWM, used if the hardware PWM
    overlay (dtoverlay=pwm-2chan) isn't enabled or the library isn't
    installed. Less jitter-free than real hardware PWM, but keeps the
    LiDAR motor-speed control working out of the box."""

    def __init__(self, pin, frequency=30000):
        import RPi.GPIO as GPIO
        self._gpio = GPIO
        self._gpio.setup(pin, GPIO.OUT)
        self._pwm = GPIO.PWM(pin, frequency)
        self._started = False

    def start(self, duty_cycle_percent):
        self._pwm.start(duty_cycle_percent)
        self._started = True

    def change_duty_cycle(self, duty_cycle_percent):
        if not self._started:
            self.start(duty_cycle_percent)
        else:
            self._pwm.ChangeDutyCycle(duty_cycle_percent)

    def stop(self):
        self._pwm.stop()


def init_pwm_Pi(pwm_channel=0, pin=18, frequency=30000):
    """channel 0 -> GPIO18 (PWM0), channel 1 -> GPIO19 (PWM1).
    Tries hardware PWM first (needs `dtoverlay=pwm-2chan`), falls back to
    software PWM on the same pin otherwise."""
    try:
        from rpi_hardware_pwm import HardwarePWM
        return HardwarePWM(pwm_channel=pwm_channel, hz=frequency, chip=0)
    except Exception as exc:
        print(f"[WARNING] hardware PWM unavailable ({exc}), falling back to software PWM on GPIO{pin}.")
        return SoftPWM(pin, frequency=frequency)
