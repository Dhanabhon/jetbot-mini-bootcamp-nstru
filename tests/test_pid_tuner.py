"""The browser PID tuner for Module 4: input clamping, run/stop safety checks, saving and the control step."""
import numpy as np
import pytest

from jetbot_nstru.app import pid as tuner
from jetbot_nstru.app.core import Context, build_page
from jetbot_nstru.line import LineResult
from jetbot_nstru.pid import PID


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def make_driver(save=lambda **kw: None):
    clock = Clock()
    return tuner.Driver(dict(tuner.DEFAULTS), save=save, clock=clock), clock


def line(found, error=0.0):
    return LineResult(found, 160 if found else None, 200 if found else None, error, 0.1, None,
                      (0, 132, 320, 108), np.zeros((108, 320), np.uint8))


def test_settings_are_clamped_and_min_speed_stays_below_max():
    settings = tuner.update_settings(tuner.DEFAULTS, {"kp": "5", "kd": -1, "max_speed": 0.3})
    assert settings["kp"] == 2.0 and settings["kd"] == 0.0
    assert settings["min_speed"] == 0.25 and settings["max_speed"] == 0.3
    assert tuner.update_settings(settings, {"min_speed": 0.5})["min_speed"] == 0.3


@pytest.mark.parametrize("data", [{"ki": 1}, {"kp": "fast"}, {"kp": None}])
def test_bad_input_is_rejected(data):
    with pytest.raises((ValueError, TypeError)):
        tuner.update_settings(tuner.DEFAULTS, data)


def test_starts_stopped_and_start_stop_switch_driving():
    driver, clock = make_driver()
    assert driver.tick(clock.now, True)[1] is False
    assert driver.handle("/start", {})["running"] is True
    assert driver.tick(clock.now, True)[1] is True
    assert driver.handle("/stop", {})["running"] is False
    assert driver.handle("/nope", {}) is None


def test_stops_when_the_page_stops_pinging():
    driver, clock = make_driver()
    driver.handle("/start", {})
    clock.now += tuner.HEARTBEAT_TIMEOUT - 0.1
    driver.handle("/ping", {})
    clock.now += tuner.HEARTBEAT_TIMEOUT - 0.1
    assert driver.tick(clock.now, True)[1] is True  # pings keep it alive
    clock.now += 0.2
    assert driver.tick(clock.now, True)[1] is False
    assert "ขาดการเชื่อมต่อ" in driver.state()["message"]


def test_stops_when_the_line_stays_lost():
    driver, clock = make_driver()
    driver.handle("/start", {})
    driver.tick(clock.now, False)
    clock.now += 1.0
    driver.handle("/ping", {})
    assert driver.tick(clock.now, True)[1] is True  # seeing the line again resets the timer
    driver.tick(clock.now, False)
    clock.now += 1.0
    driver.handle("/ping", {})
    assert driver.tick(clock.now, False)[1] is True
    clock.now += tuner.LOST_LINE_STOP
    driver.handle("/ping", {})
    assert driver.tick(clock.now, False)[1] is False


def test_save_writes_the_notebook_keys_and_reports_failures():
    saved = {}
    driver, _ = make_driver(save=lambda **kw: saved.update(kw))
    assert driver.handle("/save", {})["saved"] is True
    assert saved == tuner.DEFAULTS

    def read_only(**kw):
        raise OSError(30, "Read-only file system")

    reply = make_driver(save=read_only)[0].handle("/save", {})
    assert reply["saved"] is False and "Read-only" in reply["message"]


def test_control_matches_the_notebook():
    pid = PID(kp=0.5, kd=0.1)
    steer, speed = tuner.steer_and_speed(line(True, 0.4), pid, tuner.DEFAULTS, 0.0, 0.05)
    assert steer == pytest.approx(0.2)
    assert speed == pytest.approx(0.45 - 0.2 * 0.4)
    assert tuner.steer_and_speed(line(False), pid, tuner.DEFAULTS, 0.2, 0.05) == (0.2, 0.25)  # keep steering when lost


def test_page_has_start_stop_and_heartbeat():
    page = build_page("PID", [tuner.PidPanel(Context({}))]).decode("utf-8")
    assert 'id="pid_start"' in page and 'id="pid_stop"' in page and "<nav" not in page  # one tab, no tab bar
    assert '"/ping"' in page and 'fetch("/halt", {method: "POST", keepalive: true' in page
