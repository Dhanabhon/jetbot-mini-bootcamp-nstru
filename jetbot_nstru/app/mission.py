"""Modules 6–7 panel: run the whole mission (line + signs + FSM), log every run and estimate the bonus.

"Watch only" runs the FSM without the motors: carry the robot along the track by hand and see what it would do.
"""
import csv
import os
import time

from .. import fsm
from ..fsm import DONE, FOLLOW, PARK_APPROACH, STOP_WAIT, MissionConfig, MissionState, Observation
from ..line import detect_line
from ..params import REPO_ROOT
from ..pid import PID, battery_scale, mix_motors, speed_for_error
from ..signs import SignConfig, SignVoter, detect_sign
from ..viz import VizState, draw_overlay
from .core import Panel

LOG_PATH = os.path.join(REPO_ROOT, "race_log.csv")  # git ignores it
LOG_COLUMNS = ("time", "elapsed", "finished", "voltage", "bonus", "kp", "kd", "max_speed")  # same as Module 7
TIME_LIMIT = 90.0  # rules: 90 s per run
LOST_LINE_STOP = 2.0  # s with no line while following before the run is stopped
LIMITS = {"cross_time": (0.1, 1.0), "turn_speed": (0.2, 0.6), "cooldown": (0.3, 3.0)}
SIGN_NAMES = ("LEFT", "RIGHT", "STRAIGHT", "STOP", "PARKING")
SHOWN_EVENTS = 8


def observe(frame, line_cfg, voter, sign_cfg=SignConfig()):
    """Everything the FSM needs from one frame, plus the raw results for drawing."""
    line_result = detect_line(frame, line_cfg)
    sign = detect_sign(frame, sign_cfg)
    confirmed = voter.update(sign.label if sign else None)
    green_bottom = None
    if line_result.green_box is not None:
        _, y, _, h = line_result.green_box
        green_bottom = (y + h) / float(frame.shape[0])
    observation = Observation(line_result.found, line_result.error, line_result.width_ratio, green_bottom, confirmed)
    return observation, line_result, sign


def motors_for(command, steer, speed, trim):
    """(left, right) for an FSM command, or None to stop."""
    if command.kind == "follow":
        return mix_motors(speed, steer, trim)
    if command.kind == "drive":
        return command.left * trim.left_gain, command.right * trim.right_gain
    return None


def compensate(speed, voltage, reference_voltage):
    """Scale a speed so a sagging battery drives like it did when tuned. No reading, no change."""
    if voltage is None:
        return speed
    return speed * battery_scale(voltage, reference_voltage)


def bonus_parts(events):
    """What the run did that earns a bonus: signs shown on the OLED, STOP waits, and whether it parked."""
    signs = stops = 0
    parked = False
    previous_mode = None
    for _, mode, display in events:
        signs += display in SIGN_NAMES
        parked = parked or display == "PARKED"
        stops += mode == STOP_WAIT and previous_mode != STOP_WAIT
        previous_mode = mode
    return {"signs": signs, "stops": stops, "parked": parked}


def estimate_bonus(events):
    """Seconds of bonus the run probably earned: sign shown 2 s each, STOP_WAIT 2 s, PARKED 3 s."""
    parts = bonus_parts(events)
    return 2.0 * parts["signs"] + 2.0 * parts["stops"] + 3.0 * parts["parked"]


def append_log(path, row):
    """Add one run to the CSV log, writing the header when the file is new."""
    new_file = not os.path.exists(path)
    with open(path, "a", newline="") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(LOG_COLUMNS)
        writer.writerow([row[column] for column in LOG_COLUMNS])


def _clamp(key, value):
    low, high = LIMITS[key]
    return round(min(high, max(low, float(value))), 3)


class MissionPanel(Panel):
    name = "mission"
    title = "6–7 ภารกิจ"
    controls = """
<h2>วิ่งภารกิจเต็ม (Module 6–7)</h2>
<div class="row2"><button class="go" id="mission_start">Start</button><button class="halt" id="mission_stop">Stop (Space)</button></div>
<p class="big" id="mission_time" aria-label="เวลาที่วิ่ง">0.0 s</p>
<table>
  <tr><td>state</td><td><b id="mission_mode">-</b></td></tr>
  <tr><td>ป้ายที่อ่านไว้</td><td><b id="mission_pending">-</b></td></tr>
</table>
<label class="row"><input type="checkbox" id="mission_watch_only"> ดูอย่างเดียว ไม่สั่งมอเตอร์</label>
<label class="row"><input type="checkbox" id="mission_compensate"> ชดเชยแบตเตอรี่ (เทียบกับแรงดันตอนบันทึก)</label>
<label><span>cross_time: วิ่งตรงเข้าจุดตัดก่อนเลี้ยว (s) <b id="mission_cross_time_v"></b></span>
  <input id="mission_cross_time" type="range" min="0.1" max="1" step="0.05"></label>
<label><span>turn_speed: ความเร็วตอนหมุนตัว <b id="mission_turn_speed_v"></b></span>
  <input id="mission_turn_speed" type="range" min="0.2" max="0.6" step="0.01"></label>
<label><span>cooldown: ไม่สนจุดเขียวหลังทำงานเสร็จ (s) <b id="mission_cooldown_v"></b></span>
  <input id="mission_cooldown" type="range" min="0.3" max="3" step="0.1"></label>
<h3>เหตุการณ์รอบนี้</h3>
<pre class="hint" id="mission_events">ยังไม่มี</pre>
<p class="hint">trim, เส้น และ PID ใช้ค่าจากแท็บ 2–4 (หรือ my_params.json) · ทุกรอบที่ไม่ใช่ดูอย่างเดียวบันทึกต่อท้าย race_log.csv</p>
<button class="save" id="mission_save">บันทึก (แรงดันแบตตอนนี้เป็นค่าอ้างอิง)</button>
"""
    script = """
panels.mission = {show(s) {
  for (const k of ["cross_time", "turn_speed", "cooldown"]) setRange("mission", k, s[k]);
  $("mission_start").disabled = s.running; $("mission_stop").disabled = !s.running;
  $("mission_time").textContent = s.elapsed.toFixed(1) + " s";
  $("mission_mode").textContent = s.mode; $("mission_pending").textContent = s.pending || "-";
  $("mission_watch_only").checked = s.watch_only; $("mission_watch_only").disabled = s.running;
  $("mission_compensate").checked = s.compensate;
  $("mission_events").textContent = s.events.length ? s.events.join("\\n") : "ยังไม่มี";
}};
for (const k of ["cross_time", "turn_speed", "cooldown"]) range("mission", k);
for (const k of ["watch_only", "compensate"]) $("mission_" + k).addEventListener("change", e => act("set", {[k]: e.target.checked}));
$("mission_start").addEventListener("click", () => { say(""); act("start"); });
$("mission_stop").addEventListener("click", () => act("stop"));
$("mission_save").addEventListener("click", () => act("save"));
"""

    def __init__(self, ctx, watch_only=False, log_path=LOG_PATH):
        super().__init__(ctx)
        defaults = MissionConfig()
        self.settings = {k: _clamp(k, ctx.params.get(k, getattr(defaults, k))) for k in LIMITS}
        self.watch_only = watch_only
        self.compensate = True
        self.log_path = log_path
        self.voter = SignVoter(window=7, min_votes=4)
        self.running = False
        self.message, self.level = "", ""
        self.result = None  # summary of the last finished run
        self._new_run()

    # ---- server thread -------------------------------------------------------------------------------------

    def state(self):
        with self._lock:
            return self._snapshot()

    def handle(self, action, data):
        with self._lock:
            if action == "/set":
                self._set(data)
            elif action == "/start":
                self._start()
            elif action == "/stop":
                if self.running:
                    self._finish("หยุดแล้ว", finished=False)
            elif action == "/save":
                return self._save()
            else:
                return None
            return self._snapshot()

    def halt(self, message):
        with self._lock:
            if self.running:
                self._finish(message, finished=False)

    # ---- camera loop ---------------------------------------------------------------------------------------

    def step(self, frame, now, fps):
        observation, line_result, sign = observe(frame, self.ctx.line, self.voter)
        command, motors = None, None
        with self._lock:
            if self.running:
                command, motors = self._advance(observation, line_result, now)
            running, mode, pending, elapsed = self.running, self.run_state.mode, self.run_state.pending, self.elapsed
        if command is not None and command.display is not None:
            self.ctx.show(command.display)
        if command is not None and command.beep:
            self.ctx.beep()
        left, right = motors or (0.0, 0.0)
        status = "{} {} {:.1f}s".format(mode, pending or "", elapsed) if running else "READY " + mode
        picture = draw_overlay(frame, VizState(fsm_state=status, line_roi=line_result.roi_box, cx=line_result.cx,
                                               cy=line_result.cy, sign=sign, steer=self.steer, motor_left=left,
                                               motor_right=right, fps=fps))
        return picture, motors

    def _advance(self, observation, line_result, now):
        """One FSM step under the lock. Returns (command, motors); motors are None when watching only."""
        if self.started is None:
            self.started = self._last = now
        dt, self._last = max(now - self._last, 1e-3), now
        self.elapsed = now - self.started
        previous = self.run_state.mode
        self.run_state, command = fsm.step(self.run_state, observation, now, self.cfg)
        mode = self.run_state.mode
        if mode not in (FOLLOW, PARK_APPROACH):
            self.pid.reset()  # no turning error left over in the PID
        elif line_result.found:
            self.steer = self.pid.update(line_result.error, dt)
        motors = motors_for(command, self.steer, speed_for_error(observation.error, *self.speeds), self.ctx.trim)
        if mode != previous or command.display is not None:
            self.events.append((round(self.elapsed, 2), mode, command.display))

        if mode == FOLLOW and not line_result.found:
            self.lost_since = now if self.lost_since is None else self.lost_since
        else:
            self.lost_since = None
        if mode == DONE:
            self._finish("จบภารกิจ", finished=True)
        elif self.elapsed >= TIME_LIMIT:
            self._finish("หมดเวลา {:.0f} วินาที".format(TIME_LIMIT), finished=False)
        elif not self.watch_only and self.lost_since is not None and now - self.lost_since > LOST_LINE_STOP:
            self._finish("หยุดเพราะไม่เห็นเส้นนานเกิน {:.0f} วินาที".format(LOST_LINE_STOP), finished=False)
        return command, None if (self.watch_only or not self.running) else motors

    # ---- helpers (call with the lock held) -----------------------------------------------------------------

    def _new_run(self):
        self.run_state = MissionState()
        self.events = []
        self.started = self._last = self.lost_since = None
        self.elapsed, self.steer, self.voltage = 0.0, 0.0, None
        self.pid, self.cfg, self.speeds = None, None, None

    def _start(self):
        if self.running:
            return
        self._new_run()
        reference = self.ctx.params.get("reference_voltage", 12.0)
        self.voltage = self.ctx.battery() if self.compensate else None
        pid = self.ctx.pid
        self.speeds = (compensate(pid["max_speed"], self.voltage, reference),
                       compensate(pid["min_speed"], self.voltage, reference))
        base = MissionConfig(**self.settings)
        self.cfg = base._replace(cross_speed=compensate(base.cross_speed, self.voltage, reference),
                                 turn_speed=compensate(base.turn_speed, self.voltage, reference))
        self.pid = PID(kp=pid["kp"], kd=pid["kd"])
        self.voter.reset()
        self.running = True
        self.message = "ดูอย่างเดียว: ถือรถเดินตามสนาม" if self.watch_only else ""
        self.level = ""
        self.ctx.show("GO")

    def _finish(self, message, finished):
        self.running = False
        bonus = estimate_bonus(self.events)
        self.result = {"elapsed": round(self.elapsed, 2), "finished": finished, "bonus": bonus,
                       "net": round(self.elapsed - bonus, 2), "voltage": self.voltage}
        self.message = "{} ใน {:.2f} วินาที โบนัสประมาณ {:.0f} วินาที Net Time ประมาณ {:.2f} (ยังไม่รวม penalty)".format(
            message, self.elapsed, bonus, self.elapsed - bonus)
        self.level = "ok" if finished else "bad"
        if self.watch_only or self.started is None:
            return
        pid = self.ctx.pid
        row = dict(time=time.strftime("%H:%M:%S"), elapsed=round(self.elapsed, 2), finished=finished,
                   voltage=self.voltage, bonus=bonus, kp=pid["kp"], kd=pid["kd"], max_speed=pid["max_speed"])
        try:
            append_log(self.log_path, row)
        except OSError as exc:  # e.g. the SD card went read-only; the run result still shows on the page
            self.message += " · บันทึก log ไม่ได้: {}".format(exc)

    def _set(self, data):
        for key, value in data.items():
            if key in ("watch_only", "compensate"):
                if not isinstance(value, bool):
                    raise TypeError("{} must be true or false".format(key))
                if key == "watch_only" and self.running:
                    raise ValueError("หยุดรถก่อนเปลี่ยนโหมดดูอย่างเดียว")
                setattr(self, key, value)
            elif key in LIMITS:
                self.settings = dict(self.settings, **{key: _clamp(key, value)})  # used from the next Start
            else:
                raise ValueError("unknown setting: {}".format(key))

    def _save(self):
        volts = self.ctx.battery()
        reference = volts if volts is not None else self.ctx.params.get("reference_voltage", 12.0)
        try:
            self.ctx.save(reference_voltage=reference, **self.settings)
        except OSError as exc:  # e.g. the SD card went read-only
            self.message, self.level = "บันทึกไม่สำเร็จ: {}".format(exc), "bad"
            return dict(self._snapshot(), saved=False)
        self.ctx.params["reference_voltage"] = reference
        self.message = "บันทึกแล้ว {} reference_voltage={}".format(
            "  ".join("{}={}".format(k, v) for k, v in sorted(self.settings.items())), reference)
        self.level = "ok"
        return dict(self._snapshot(), saved=True)

    def _snapshot(self):
        events = ["{:5.1f}s  {:14s} {}".format(t, mode, display or "") for t, mode, display in self.events[-SHOWN_EVENTS:]]
        return dict(self.settings, running=self.running, watch_only=self.watch_only, compensate=self.compensate,
                    mode=self.run_state.mode, pending=self.run_state.pending, elapsed=round(self.elapsed, 1),
                    events=events, result=self.result, message=self.message, level=self.level,
                    bonus=bonus_parts(self.events))
