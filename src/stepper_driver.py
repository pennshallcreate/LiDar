"""
Turntable stepper control. Two driver classes sharing one interface
(move_steps / move_angle / move_to_angle / get_current_angle / close) so
scan.py doesn't care which motor tier is installed -- see
ARCHITECTURE.md section 4 for the wiring of each.

`Stepper(config)` is a factory that returns the right class based on
config.json's STEPPER.DRIVER field ("A4988" or "ULN2003").

The A4988 class is adapted from PiLiDAR's lib/a4988_driver.py
(https://github.com/PiLiDAR/PiLiDAR), (c) Philip Gutjahr, CC BY-NC-SA 4.0.
The ULN2003 class is new (28BYJ-48 half-step sequencing is standard,
publicly-documented hardware behavior, not project-specific code).
"""

from time import sleep

import RPi.GPIO as GPIO


def Stepper(config):
    driver = config.get("STEPPER", "DRIVER")
    if driver == "A4988":
        return A4988(config.get("STEPPER", "pins", "DIR_PIN"),
                     config.get("STEPPER", "pins", "STEP_PIN"),
                     config.get("STEPPER", "pins", "MS_PINS"),
                     delay=config.get("STEPPER", "STEP_DELAY"),
                     step_angle=config.get("STEPPER", "STEP_ANGLE"),
                     microsteps=config.get("STEPPER", "MICROSTEPS"),
                     gear_ratio=config.get("STEPPER", "GEAR_RATIO"))
    if driver == "ULN2003":
        return ULN2003(config.get("STEPPER", "uln2003_pins"),
                        delay=config.get("STEPPER", "STEP_DELAY"),
                        steps_per_rev=config.get("STEPPER", "ULN2003_STEPS_PER_REV"),
                        gear_ratio=config.get("STEPPER", "GEAR_RATIO"))
    raise ValueError(f"Unknown STEPPER.DRIVER: {driver!r} (expected 'A4988' or 'ULN2003')")


class A4988:
    """NEMA17 via an A4988 microstepping driver (Recommended tier)."""

    def __init__(self, dir_pin, step_pin, ms_pins,
                 delay=0.0005, step_angle=1.8, microsteps=16,
                 gear_ratio=1.0, verbose=False):
        GPIO.setwarnings(verbose)
        GPIO.setmode(GPIO.BCM)

        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.ms_pins = ms_pins
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        for pin in self.ms_pins:
            GPIO.setup(pin, GPIO.OUT)

        self.current_steps = 0
        self.step_angle = step_angle or (360 / 200)
        self.microsteps = microsteps
        self.gear_ratio = gear_ratio
        self.delay = delay

        step_modes = {1: (False, False, False),
                      2: (True, False, False),
                      4: (False, True, False),
                      8: (True, True, False),
                      16: (True, True, True)}
        if self.microsteps not in step_modes:
            raise ValueError(f"Unsupported microstep count: {microsteps} (A4988 supports 1/2/4/8/16)")
        for pin, state in zip(self.ms_pins, step_modes[self.microsteps]):
            GPIO.output(pin, state)

    def set_direction(self, direction):
        GPIO.output(self.dir_pin, direction)

    def get_steps_for_angle(self, angle):
        return int((angle / self.step_angle) * self.microsteps * self.gear_ratio)

    def get_angle_for_steps(self, steps):
        return (steps / (self.microsteps * self.gear_ratio)) * self.step_angle

    def step(self):
        GPIO.output(self.step_pin, True)
        sleep(0.0001)
        GPIO.output(self.step_pin, False)
        sleep(self.delay)

    def move_steps(self, steps):
        direction = steps < 0  # clockwise is positive
        steps = abs(int(steps))
        self.set_direction(direction)
        for _ in range(steps):
            self.step()
        self.current_steps += -steps if direction else steps

    def move_angle(self, angle):
        steps = self.get_steps_for_angle(abs(angle))
        self.move_steps(steps if angle >= 0 else -steps)
        return steps

    def move_to_angle(self, target_angle, mod=True):
        if mod:
            target_angle %= 360
        angle_difference = target_angle - self.get_current_angle()
        if angle_difference > 180:
            angle_difference -= 360
        elif angle_difference < -180:
            angle_difference += 360
        self.move_steps(self.get_steps_for_angle(angle_difference))

    def get_current_angle(self, mod=True):
        angle = self.current_steps / (self.microsteps * self.gear_ratio) * self.step_angle
        return angle % 360 if mod else angle

    def close(self):
        GPIO.cleanup(self.ms_pins)
        GPIO.cleanup(self.dir_pin)
        GPIO.cleanup(self.step_pin)


class ULN2003:
    """28BYJ-48 geared stepper via a ULN2003 darlington driver board
    (Budget tier). Uses the standard 8-phase half-step sequence."""

    HALF_STEP_SEQUENCE = (
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (0, 1, 0, 0),
        (0, 1, 1, 0),
        (0, 0, 1, 0),
        (0, 0, 1, 1),
        (0, 0, 0, 1),
        (1, 0, 0, 1),
    )

    def __init__(self, pins, delay=0.0015, steps_per_rev=4096, gear_ratio=1.0, verbose=False):
        GPIO.setwarnings(verbose)
        GPIO.setmode(GPIO.BCM)

        self.pins = pins
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)

        self.delay = delay  # 28BYJ-48 is slow -- needs a longer inter-step delay than a NEMA17
        self.steps_per_rev = steps_per_rev
        self.gear_ratio = gear_ratio
        self.microsteps = 1  # kept for interface parity with A4988 (steps_per_rev already includes gearing)
        self.step_angle = 360 / steps_per_rev

        self.current_steps = 0
        self._phase = 0

    def get_steps_for_angle(self, angle):
        return int((angle / 360) * self.steps_per_rev * self.gear_ratio)

    def get_angle_for_steps(self, steps):
        return (steps / (self.steps_per_rev * self.gear_ratio)) * 360

    def _write_phase(self, phase_index):
        for pin, state in zip(self.pins, self.HALF_STEP_SEQUENCE[phase_index % 8]):
            GPIO.output(pin, bool(state))

    def move_steps(self, steps):
        direction = 1 if steps >= 0 else -1
        for _ in range(abs(int(steps))):
            self._phase += direction
            self._write_phase(self._phase)
            sleep(self.delay)
        self.current_steps += steps
        # de-energize coils between moves to save power and avoid overheating
        for pin in self.pins:
            GPIO.output(pin, False)

    def move_angle(self, angle):
        steps = self.get_steps_for_angle(abs(angle))
        self.move_steps(steps if angle >= 0 else -steps)
        return steps

    def move_to_angle(self, target_angle, mod=True):
        if mod:
            target_angle %= 360
        angle_difference = target_angle - self.get_current_angle()
        if angle_difference > 180:
            angle_difference -= 360
        elif angle_difference < -180:
            angle_difference += 360
        self.move_steps(self.get_steps_for_angle(angle_difference))

    def get_current_angle(self, mod=True):
        angle = self.current_steps / (self.steps_per_rev * self.gear_ratio) * 360
        return angle % 360 if mod else angle

    def close(self):
        GPIO.cleanup(self.pins)


if __name__ == "__main__":
    from config import Config

    config = Config()
    config.init(scan_id="_bench")

    stepper = Stepper(config)
    try:
        print(f"driver: {config.get('STEPPER', 'DRIVER')}, steps/move: {config.steps}, h_res: {config.h_res:.4f} deg")
        stepper.move_angle(10)
        print("current angle:", round(stepper.get_current_angle(), 2))
        stepper.move_angle(-10)
        print("current angle:", round(stepper.get_current_angle(), 2))
    finally:
        stepper.close()
