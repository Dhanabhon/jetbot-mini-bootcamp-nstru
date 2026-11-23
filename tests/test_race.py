"""Race day panel: KEY1 on the robot starts and stops the run, tuning stays in the browser tabs."""
import csv
import importlib.util
import os

from jetbot_nstru.app.core import HEARTBEAT_TIMEOUT, App, build_page
from jetbot_nstru.app.pid import PidPanel
from jetbot_nstru.app.race import RACE_PANELS, KeyPresses, RacePanel

from test_app import BLANK, ROOT, line_frame, make_ctx


class FakeKey:
    def __init__(self):
        self.down = False

    def pressed(self):
        return self.down


def press(panel, key, now, frame=None):
    """Hold KEY1 for three frames, then let go, like a real press at 30 FPS."""
    frame = line_frame() if frame is None else frame
    key.down = True
    for i in range(3):
        panel.step(frame, now + i * 0.03, 30.0)
    key.down = False
    return panel.step(frame, now + 0.1, 30.0)


def make_race(tmp_path, key=None):
    ctx, clock = make_ctx({"reference_voltage": 12.0})
    beeps = []
    ctx._beep = lambda: beeps.append(clock.now) or True
    key = FakeKey() if key is None else key
    return RacePanel(ctx, key=key, log_path=str(tmp_path / "race_log.csv")), ctx, clock, key, beeps


def test_key_presses_count_once_per_press_and_ignore_bounce():
    presses = KeyPresses(debounce=0.5)
    levels = [(False, 0.0), (True, 0.1), (True, 0.13), (False, 0.2), (True, 0.25), (False, 0.3), (True, 0.7)]
    assert [presses.update(down, now) for down, now in levels] == [False, True, False, False, False, False, True]


def test_key1_starts_the_run_and_its_timer_then_stops_it(tmp_path):
    panel, ctx, clock, key, beeps = make_race(tmp_path)
    assert panel.step(line_frame(), clock.now, 30.0)[1] is None  # waits for KEY1
    assert "กด KEY1" in panel.state()["key"]
    press(panel, key, clock.now)
    state = panel.state()
    assert state["running"] is True and ctx.oled_text == "GO" and len(beeps) == 1
    assert panel.step(line_frame(), clock.now + 2.0, 30.0)[1] is not None
    assert panel.state()["elapsed"] >= 1.9  # timed from the press
    press(panel, key, clock.now + 3.0)
    state = panel.state()
    assert state["running"] is False and "KEY1" in state["message"] and len(beeps) == 2
    with open(str(tmp_path / "race_log.csv")) as handle:
        assert len(list(csv.reader(handle))) == 2  # header + this run


def test_a_key1_run_keeps_going_without_the_browser(tmp_path):
    panel, ctx, clock, key, _ = make_race(tmp_path)
    app = App([panel, PidPanel(ctx)], ctx, clock=clock)
    clock.now += HEARTBEAT_TIMEOUT + 5  # nobody has the page open
    press(app, key, clock.now)
    clock.now += 1.0
    assert app.step(line_frame(), clock.now, 30.0)[1] is not None
    press(app, key, clock.now + 0.5)
    assert app.step(line_frame(), clock.now + 1.0, 30.0)[1] is None


def test_a_run_started_from_the_page_still_stops_when_the_page_goes_quiet(tmp_path):
    panel, ctx, clock, key, _ = make_race(tmp_path)
    app = App([panel, PidPanel(ctx)], ctx, clock=clock)
    app.handle("/mission/start", {})
    assert app.step(line_frame(), clock.now, 30.0)[1] is not None
    clock.now += HEARTBEAT_TIMEOUT + 0.1
    assert app.step(line_frame(), clock.now, 30.0)[1] is None
    assert panel.state()["running"] is False


def test_the_other_safety_stops_still_end_a_key1_run(tmp_path):
    panel, ctx, clock, key, _ = make_race(tmp_path)
    press(panel, key, clock.now)
    panel.halt("หยุดแล้ว")  # Space or Stop on the page
    assert panel.state()["running"] is False
    press(panel, key, clock.now + 1.0, frame=BLANK)  # starts again, but there is no line
    assert panel.step(BLANK, clock.now + 4.0, 30.0)[1] is None
    assert "ไม่เห็นเส้น" in panel.state()["message"]


def test_without_a_key_the_page_start_button_still_works(tmp_path):
    ctx, clock = make_ctx()
    panel = RacePanel(ctx, key=False, log_path=str(tmp_path / "log.csv"))
    assert "ไม่พบปุ่ม KEY1" in panel.state()["key"]
    assert panel.handle("/start", {})["running"] is True


def test_race_page_and_script(tmp_path):
    ctx, _ = make_ctx()
    panels = [cls(ctx, key=False) if cls is RacePanel else cls(ctx) for cls in RACE_PANELS]
    page = build_page("วันแข่ง", panels).decode("utf-8")
    assert panels[0].name == "mission" and 'id="mission_key"' in page  # first tab, so KEY1 works with no page open
    spec = importlib.util.spec_from_file_location("jetbot_race", os.path.join(ROOT, "jetbot_race.py"))
    spec.loader.exec_module(importlib.util.module_from_spec(spec))  # imports cleanly without a robot
