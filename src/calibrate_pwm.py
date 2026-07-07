"""
LiDAR motor-speed calibration: sweeps the PWM duty cycle driving the
LD06/LD19's MOTOCTL pin, records the sensor's own reported rotation speed
at each step, and fits a linear speed = m*pwm + b model -- the same
PWM_COEFFS used by lidar_driver.py's Lidar.update_speed().

Adapted from PiLiDAR's lib/curve_fitting.py
(https://github.com/PiLiDAR/PiLiDAR), (c) Philip Gutjahr, CC BY-NC-SA 4.0
-- re-fit with numpy.polyfit instead of scipy.optimize.curve_fit (a linear
fit doesn't need scipy's general-purpose nonlinear solver, and dropping
scipy keeps the onboard dependency list smaller -- see ARCHITECTURE.md
section 2).

Run this once after assembly (BUILD.md calibration step), then paste the
printed (m, b) into config.json's LIDAR.<DEVICE>.PWM_COEFFS.

Usage:
    python3 calibrate_pwm.py
"""

import time

import numpy as np

from config import Config
from lidar_driver import Lidar


def sample_pwm_sweep(lidar, pwm_range=(0.5, 0.15), decrement=0.01, settle_s=0.6, samples_per_point=30):
    """Step the PWM duty cycle down from pwm_range[0] to pwm_range[1],
    letting the motor settle at each step before recording its reported
    speed (averaged over a few packets to smooth jitter)."""
    measurements = []
    pwm_dc = lidar.update_pwm_dc(pwm_range[0])
    time.sleep(1.5)  # LD06/LD19 need a moment to spin up before speed control is reliable

    while pwm_dc >= pwm_range[1]:
        time.sleep(settle_s)
        speeds = []
        for _ in range(samples_per_point):
            lidar._read_packet()
            speeds.append(lidar.speed)
        avg_speed = float(np.mean(speeds))
        measurements.append((round(pwm_dc, 4), round(avg_speed, 4)))
        print(f"  pwm={pwm_dc:.3f} -> speed={avg_speed:.3f} rev/s")
        pwm_dc = lidar.update_pwm_dc(pwm_dc - decrement)

    return measurements


def fit_linear(measurements):
    pwm, speed = zip(*measurements)
    m, b = np.polyfit(np.array(pwm), np.array(speed), deg=1)
    return float(m), float(b)


if __name__ == "__main__":
    config = Config()
    config.init(scan_id="_calibrate_pwm")
    lidar = Lidar(config)

    try:
        print("Sweeping PWM duty cycle, recording LD06/LD19-reported speed...")
        measurements = sample_pwm_sweep(lidar)
        m, b = fit_linear(measurements)
        print()
        print(f"Fitted: speed = {m:.4f} * pwm + {b:.4f}")
        print()
        print(f'Paste into config.json -> LIDAR.{config.DEVICE}.PWM_COEFFS: [{m:.4f}, {b:.4f}]')
    finally:
        lidar.close()
