"""PID steering and motor mixing (Modules 2 and 4).

Sign convention: error > 0 means the line is right of centre, so the robot must turn right,
which means the left wheel goes faster. steer > 0 therefore speeds up the left wheel.
"""
from typing import NamedTuple, Optional, Tuple


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class PID:
    """Textbook PID with output clamp and integral anti-windup."""

    def __init__(self, kp: float, ki: float = 0.0, kd: float = 0.0, output_limit: float = 1.0,
                 integral_limit: Optional[float] = None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit
        self.integral_limit = integral_limit if integral_limit is not None else output_limit
        self.reset()

    def reset(self) -> None:
        self._integral = 0.0
        self._previous_error = None  # type: Optional[float]

    def update(self, error: float, dt: float) -> float:
        if dt <= 0:
            raise ValueError("dt must be positive, got {}".format(dt))
        self._integral = clamp(self._integral + error * dt, -self.integral_limit, self.integral_limit)
        # first call has no history, so the derivative term would be a spike
        derivative = 0.0 if self._previous_error is None else (error - self._previous_error) / dt
        self._previous_error = error
        output = self.kp * error + self.ki * self._integral + self.kd * derivative
        return clamp(output, -self.output_limit, self.output_limit)


class MotorTrim(NamedTuple):
    """Per-wheel gain from Module 2 so the robot drives straight at equal commands."""

    left_gain: float = 1.0
    right_gain: float = 1.0


def mix_motors(base_speed: float, steer: float, trim: MotorTrim = MotorTrim(),
               limit: float = 1.0) -> Tuple[float, float]:
    """Turn a forward speed and a steering amount into (left, right) motor values."""
    left = (base_speed + steer) * trim.left_gain
    right = (base_speed - steer) * trim.right_gain
    return clamp(left, -limit, limit), clamp(right, -limit, limit)


def speed_for_error(error: float, max_speed: float, min_speed: float) -> float:
    """Full speed on straights, slowing linearly to min_speed as |error| approaches 1."""
    return max_speed - (max_speed - min_speed) * min(1.0, abs(error))


def battery_scale(voltage: float, reference_voltage: float, low: float = 0.85, high: float = 1.25) -> float:
    """Multiply speeds by this to behave like the battery was at reference_voltage.

    Motor speed is roughly proportional to voltage, so a sagging battery needs a larger command.
    """
    if voltage <= 0:
        raise ValueError("voltage must be positive, got {}".format(voltage))
    return clamp(reference_voltage / voltage, low, high)
