import numpy as np
import pytest

from jetbot_nstru.line import LineConfig, detect_line
from jetbot_nstru.pid import PID, MotorTrim, battery_scale, mix_motors, speed_for_error

WHITE = (235, 235, 235)
BLACK = (20, 20, 20)
GREEN = (60, 170, 40)


def floor(height=240, width=320):
    return np.full((height, width, 3), WHITE, dtype=np.uint8)


def test_line_right_of_centre_gives_positive_error():
    frame = floor()
    frame[:, 200:220] = BLACK

    result = detect_line(frame)

    assert result.found
    assert 205 <= result.cx <= 215
    assert result.error == pytest.approx((210 - 160) / 160.0, abs=0.05)
    assert result.green_box is None


def test_no_line_reports_not_found_with_zero_error():
    result = detect_line(floor())

    assert not result.found
    assert result.cx is None
    assert result.error == 0.0


def test_line_above_roi_is_ignored():
    frame = floor()
    frame[:100, 150:170] = BLACK  # far floor, above roi_top=0.55

    assert not detect_line(frame).found


def test_green_marker_is_found_in_full_frame_coordinates():
    frame = floor()
    frame[:, 150:170] = BLACK
    frame[200:230, 140:180] = GREEN

    result = detect_line(frame)

    assert result.green_box == (140, 200, 40, 30)


def test_horizontal_line_has_high_width_ratio():
    frame = floor()
    frame[:, 150:170] = BLACK
    frame[190:205, :] = BLACK  # T junction across the ROI

    assert detect_line(frame).width_ratio > 0.9


def test_adaptive_threshold_also_finds_line():
    frame = floor()
    frame[:, 100:115] = BLACK

    result = detect_line(frame, LineConfig(use_adaptive=True))

    assert result.found
    assert result.error < 0


def test_pid_proportional_and_clamped():
    pid = PID(kp=0.5, output_limit=0.3)

    assert pid.update(0.4, dt=0.05) == pytest.approx(0.2)
    assert pid.update(1.0, dt=0.05) == pytest.approx(0.3)


def test_pid_derivative_skips_first_call_then_reacts():
    pid = PID(kp=0.0, kd=0.1)

    assert pid.update(0.5, dt=0.1) == 0.0
    assert pid.update(0.7, dt=0.1) == pytest.approx(0.1 * (0.2 / 0.1))


def test_pid_integral_is_limited():
    pid = PID(kp=0.0, ki=1.0, integral_limit=0.2)
    for _ in range(100):
        out = pid.update(1.0, dt=0.1)

    assert out == pytest.approx(0.2)


def test_pid_rejects_non_positive_dt():
    with pytest.raises(ValueError):
        PID(kp=1.0).update(0.1, dt=0)


def test_positive_steer_speeds_up_left_wheel_and_applies_trim():
    left, right = mix_motors(0.4, 0.1, MotorTrim(left_gain=1.0, right_gain=0.9))

    assert left == pytest.approx(0.5)
    assert right == pytest.approx(0.27)


def test_mix_motors_clamps_to_limit():
    assert mix_motors(0.9, 0.5, limit=1.0) == (1.0, pytest.approx(0.4))


def test_speed_slows_with_error():
    assert speed_for_error(0.0, 0.6, 0.3) == pytest.approx(0.6)
    assert speed_for_error(-0.5, 0.6, 0.3) == pytest.approx(0.45)
    assert speed_for_error(2.0, 0.6, 0.3) == pytest.approx(0.3)


def test_battery_scale_boosts_when_voltage_sags_and_is_bounded():
    assert battery_scale(11.0, 12.0) == pytest.approx(12.0 / 11.0)
    assert battery_scale(6.0, 12.0) == pytest.approx(1.25)
    with pytest.raises(ValueError):
        battery_scale(0, 12.0)
