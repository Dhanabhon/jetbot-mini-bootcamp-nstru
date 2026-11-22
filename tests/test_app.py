"""The browser app: routing, safety stops, settings shared between tabs, and the Module 1, 2 and 6-7 panels."""
import csv
import importlib.util
import os

import numpy as np
import pytest

from jetbot_nstru.app import PANEL_TYPES
from jetbot_nstru.app.check import CheckPanel, battery_percent
from jetbot_nstru.app.core import HEARTBEAT_TIMEOUT, App, Context, TimedDrive, build_page, drive
from jetbot_nstru.app.mission import (LOG_COLUMNS, LOST_LINE_STOP, MissionPanel, compensate, estimate_bonus,
                                      motors_for, observe)
from jetbot_nstru.app.pid import PidPanel
from jetbot_nstru.app.trim import TrimPanel, adjust_trim
from jetbot_nstru.fsm import Command
from jetbot_nstru.pid import MotorTrim, mix_motors
from jetbot_nstru.signs import SignVoter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLUTIONS = os.path.join(ROOT, "notebooks", "solutions")
BLANK = np.full((240, 320, 3), 235, np.uint8)


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def make_ctx(params=None, save=lambda **kw: None, battery=lambda: 12.0):
    clock = Clock()
    return Context(params or {}, save=save, battery=battery, clock=clock), clock


def line_frame():
    frame = BLANK.copy()
    frame[:, 150:170] = 20  # black line down the middle
    return frame


# ---- core -------------------------------------------------------------------------------------------------


def test_context_reads_saved_values_and_caches_the_battery():
    reads = []
    ctx, clock = make_ctx({"left_gain": 0.97, "roi_top": 0.6, "kp": 0.8}, battery=lambda: reads.append(1) or 11.5)
    assert ctx.trim == MotorTrim(0.97, 1.0) and ctx.line.roi_top == 0.6
    assert ctx.pid["kp"] == 0.8 and ctx.pid["kd"] == 0.05
    assert ctx.battery() == 11.5 and ctx.battery() == 11.5 and len(reads) == 1  # cached
    clock.now += 3
    ctx.battery()
    assert len(reads) == 2


def test_battery_that_cannot_be_read_gives_none_and_the_reason():
    def broken():
        raise OSError("I2C bus 1 not found")

    ctx, _ = make_ctx(battery=broken)
    assert ctx.battery() is None and "I2C" in ctx.battery_error


def test_timed_drive_runs_until_its_deadline():
    timed = TimedDrive()
    assert timed.command(0.0) is None
    timed.start((0.3, 0.3), 1.0, now=10.0)
    assert timed.command(10.5) == (0.3, 0.3) and timed.command(11.0) is None
    timed.start((0.3, 0.3), 1.0, now=20.0)
    timed.stop()
    assert timed.command(20.1) is None


def test_drive_sends_motors_and_stops_only_once():
    calls = []

    class Robot:
        def set_motors(self, left, right):
            calls.append((left, right))

        def stop(self):
            calls.append("stop")

    robot = Robot()
    assert drive(robot, (0.2, 0.3), False) is True
    assert drive(robot, None, True) is False
    assert drive(robot, None, False) is False
    assert calls == [(0.2, 0.3), "stop"]


def make_app():
    ctx, clock = make_ctx()
    return App([CheckPanel(ctx), TrimPanel(ctx)], ctx, clock=clock), ctx, clock


def test_app_routes_requests_to_the_panel_on_screen():
    app, ctx, clock = make_app()
    reply = app.handle("/ping", {})
    assert reply["active"] == "check" and reply["battery"] == 12.0 and "fps" in reply["state"]
    with pytest.raises(ValueError):
        app.handle("/trim/run", {})  # a tab that is not on screen must not start the motors
    assert app.handle("/select", {"panel": "trim"})["active"] == "trim"
    assert app.handle("/trim/run", {})["running"] is True  # a panel action replies with that panel's state
    assert app.handle("/trim/nope", {}) is None and app.handle("/nope", {}) is None
    with pytest.raises(ValueError):
        app.handle("/select", {"panel": "nope"})


def test_switching_tab_and_halt_stop_the_motors():
    app, ctx, clock = make_app()
    app.handle("/select", {"panel": "trim"})
    app.handle("/trim/run", {})
    assert app.step(BLANK, clock.now, 30.0)[1] is not None
    app.handle("/select", {"panel": "check"})
    app.handle("/select", {"panel": "trim"})
    assert app.step(BLANK, clock.now, 30.0)[1] is None
    assert "เปลี่ยนหน้า" in app.handle("/ping", {})["state"]["message"]
    app.handle("/trim/run", {})
    app.handle("/halt", {})
    assert app.step(BLANK, clock.now, 30.0)[1] is None


def test_motors_stop_when_the_page_goes_quiet():
    app, ctx, clock = make_app()
    app.handle("/select", {"panel": "trim"})
    app.handle("/trim/set", {"seconds": 4})
    app.handle("/trim/run", {})
    clock.now += HEARTBEAT_TIMEOUT - 0.1
    assert app.step(BLANK, clock.now, 30.0)[1] is not None
    clock.now += 0.2
    assert app.step(BLANK, clock.now, 30.0)[1] is None
    assert "ขาดการเชื่อมต่อ" in app.panels["trim"].state()["message"]


def test_page_has_a_tab_and_section_per_panel():
    ctx, _ = make_ctx()
    panels = [cls(ctx) for cls in PANEL_TYPES.values()]
    page = build_page("JetBot", panels).decode("utf-8")
    for panel in panels:
        assert 'data-panel="{}"'.format(panel.name) in page and panel.title in page
    assert page.count("<section") == len(panels) and "<nav" in page
    assert '"/halt"' in page and "keepalive: true" in page  # Space and closing the tab stop the robot


@pytest.mark.parametrize("name", sorted(f for f in os.listdir(SOLUTIONS) if f.endswith(".py")))
def test_every_module_script_opens_known_tabs(name):
    spec = importlib.util.spec_from_file_location("script", os.path.join(SOLUTIONS, name))
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    assert script.PANELS and all(panel in PANEL_TYPES for panel in script.PANELS)
    assert all(panel in script.PANELS for panel in getattr(script, "OPTIONS", {}))


# ---- Module 1 ---------------------------------------------------------------------------------------------


def test_battery_percent_matches_the_notebook():
    assert battery_percent(12.6) == 100 and battery_percent(10.0) == 0
    assert battery_percent(11.55) == pytest.approx(50, abs=0.01)


def test_check_panel_drives_for_one_second_and_reports_missing_parts():
    ctx, clock = make_ctx()
    panel = CheckPanel(ctx)
    assert "ไม่พบ" in panel.handle("/oled", {"text": "HI"})["message"]
    assert "buzzer" in panel.handle("/beep", {})["message"]
    assert panel.handle("/drive", {})["driving"] is True
    assert panel.step(BLANK, clock.now + 0.5, 30.0)[1] == (0.3, 0.3)
    assert panel.step(BLANK, clock.now + 1.1, 30.0)[1] is None
    assert panel.state()["fps"] == 30.0 and panel.state()["percent"] == pytest.approx(71.43, abs=0.01)


# ---- Module 2 ---------------------------------------------------------------------------------------------


def test_adjust_trim_matches_the_notebook_and_stays_in_range():
    assert adjust_trim(MotorTrim(), 4) == MotorTrim(0.98, 1.0)
    assert adjust_trim(MotorTrim(), -2) == MotorTrim(1.0, 0.99)
    assert adjust_trim(MotorTrim(), 0) == MotorTrim()
    assert adjust_trim(MotorTrim(0.52, 1.0), 40).left_gain == 0.5


def test_trim_panel_runs_straight_and_shares_the_new_trim():
    saved = {}
    ctx, clock = make_ctx({"trim_speed": 0.4}, save=lambda **kw: saved.update(kw))
    panel = TrimPanel(ctx)
    panel.handle("/drift", {"cm": 6})
    assert ctx.trim == MotorTrim(0.97, 1.0)  # PID and mission tabs use it without saving
    panel.handle("/run", {})
    assert panel.step(BLANK, clock.now + 1.0, 30.0)[1] == mix_motors(0.4, 0.0, ctx.trim)
    assert panel.step(BLANK, clock.now + 2.1, 30.0)[1] is None
    assert panel.handle("/save", {})["saved"] is True
    assert saved == {"left_gain": 0.97, "right_gain": 1.0, "trim_speed": 0.4}
    with pytest.raises(ValueError):
        panel.handle("/drift", {"cm": 500})
    with pytest.raises(ValueError):
        panel.handle("/set", {"kp": 1})


def test_trim_save_failure_is_reported_not_raised():
    def read_only(**kw):
        raise OSError(30, "Read-only file system")

    ctx, _ = make_ctx(save=read_only)
    reply = TrimPanel(ctx).handle("/save", {})
    assert reply["saved"] is False and "Read-only" in reply["message"]


# ---- Module 4 shares settings -----------------------------------------------------------------------------


def test_pid_panel_drives_with_the_shared_trim_and_settings():
    ctx, clock = make_ctx()
    ctx.trim = MotorTrim(0.9, 1.0)
    panel = PidPanel(ctx)
    panel.handle("/set", {"kp": 1.2})
    assert ctx.pid["kp"] == 1.2  # the mission tab drives with it
    assert panel.step(line_frame(), clock.now, 30.0)[1] is None  # starts stopped
    panel.handle("/start", {})
    left, right = panel.step(line_frame(), clock.now, 30.0)[1]
    assert left == pytest.approx(right * 0.9, abs=0.05)  # line straight ahead: only the trim differs


# ---- Modules 6-7 ------------------------------------------------------------------------------------------


def test_compensate_and_bonus_match_the_notebook():
    assert compensate(0.4, None, 12.0) == 0.4
    assert compensate(0.4, 12.0, 12.0) == pytest.approx(0.4)
    assert compensate(0.4, 10.8, 12.0) > 0.4
    assert compensate(0.4, 6.0, 12.0) == pytest.approx(0.4 * 1.25)
    sample = [(1.2, "FOLLOW", "STOP"), (2.0, "STOP_WAIT", None), (5.2, "CROSS", None),
              (8.0, "FOLLOW", "PARKING"), (9.5, "PARK_APPROACH", None), (11.0, "DONE", "PARKED")]
    assert estimate_bonus(sample) == 9 and estimate_bonus([]) == 0


def test_observe_and_motors_for_match_the_notebook():
    frame = line_frame()
    frame[200:236, 140:180] = (60, 170, 40)  # green marker
    obs, _, _ = observe(frame, Context({}).line, SignVoter())
    assert obs.line_found and obs.sign is None and obs.green_bottom == pytest.approx(236 / 240.0)
    trim = MotorTrim(0.9, 1.0)
    assert motors_for(Command("follow"), 0.0, 0.4, trim) == mix_motors(0.4, 0.0, trim)
    assert motors_for(Command("drive", -0.3, 0.3), 0.0, 0.4, trim) == pytest.approx((-0.27, 0.3))
    assert motors_for(Command("stop"), 0.0, 0.4, trim) is None


def make_mission(tmp_path, **kw):
    ctx, clock = make_ctx({"reference_voltage": 12.0})
    return MissionPanel(ctx, log_path=str(tmp_path / "race_log.csv"), **kw), ctx, clock


def test_mission_run_drives_logs_and_estimates_the_bonus(tmp_path):
    panel, ctx, clock = make_mission(tmp_path)
    assert panel.step(line_frame(), clock.now, 30.0)[1] is None  # not running yet
    assert panel.handle("/start", {})["running"] is True
    for i in range(5):
        assert panel.step(line_frame(), clock.now + i * 0.1, 30.0)[1] is not None
    panel.halt("หยุดแล้ว")
    state = panel.state()
    assert state["running"] is False and state["result"]["finished"] is False and state["level"] == "bad"
    with open(str(tmp_path / "race_log.csv")) as handle:
        rows = list(csv.reader(handle))
    assert tuple(rows[0]) == tuple(LOG_COLUMNS) and len(rows) == 2 and rows[1][2] == "False"


def test_watch_only_never_drives_and_is_not_logged(tmp_path):
    panel, ctx, clock = make_mission(tmp_path, watch_only=True)
    panel.handle("/start", {})
    assert panel.step(line_frame(), clock.now, 30.0)[1] is None
    assert panel.state()["mode"] == "FOLLOW"
    with pytest.raises(ValueError):
        panel.handle("/set", {"watch_only": False})  # not while running
    panel.handle("/stop", {})
    assert not os.path.exists(str(tmp_path / "race_log.csv"))


def test_mission_stops_when_the_line_stays_lost(tmp_path):
    panel, ctx, clock = make_mission(tmp_path)
    panel.handle("/start", {})
    panel.step(BLANK, clock.now, 30.0)
    assert panel.step(BLANK, clock.now + LOST_LINE_STOP + 0.1, 30.0)[1] is None
    assert "ไม่เห็นเส้น" in panel.state()["message"]


def test_mission_settings_validate_and_save_with_the_battery_reference(tmp_path):
    saved = {}
    panel, ctx, _ = make_mission(tmp_path)
    ctx.save = lambda **kw: saved.update(kw)
    ctx._read_battery = lambda: 11.4
    assert panel.handle("/set", {"cross_time": 5, "compensate": False})["cross_time"] == 1.0
    for bad in ({"compensate": "yes"}, {"kp": 1}):
        with pytest.raises((ValueError, TypeError)):
            panel.handle("/set", bad)
    assert panel.handle("/save", {})["saved"] is True
    assert saved == {"cross_time": 1.0, "turn_speed": 0.35, "cooldown": 1.0, "reference_voltage": 11.4}
