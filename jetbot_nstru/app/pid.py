"""Module 4 panel: follow the line with PID and change Kp, Kd and speeds while the robot drives."""
import threading
import time

from ..line import detect_line
from ..pid import PID, mix_motors, speed_for_error
from ..viz import VizState, draw_overlay, with_mask
from .core import PID_DEFAULTS, Panel

LIMITS = {"kp": (0.0, 2.0), "kd": (0.0, 0.5), "max_speed": (0.10, 0.80), "min_speed": (0.0, 0.60)}
DEFAULTS = PID_DEFAULTS
HEARTBEAT_TIMEOUT = 1.5  # s without a ping from the page before the motors stop
LOST_LINE_STOP = 2.0  # s of no line before the motors stop


def update_settings(settings, data):
    """New settings with the browser's values clamped to LIMITS; min_speed never exceeds max_speed."""
    merged = dict(settings)
    for key, value in data.items():
        if key not in LIMITS:
            raise ValueError("unknown setting: {}".format(key))
        low, high = LIMITS[key]
        merged[key] = round(min(high, max(low, float(value))), 3)
    merged["min_speed"] = min(merged["min_speed"], merged["max_speed"])
    return merged


class Driver:
    """Settings and the run/stop switch, shared between the web server thread and the drive loop."""

    def __init__(self, settings, save, clock=time.monotonic):
        self.settings = settings
        self.running = False
        self.message = ""
        self._save = save
        self._clock = clock
        self._last_ping = clock()
        self._lost_since = None
        self._lock = threading.Lock()

    def state(self):
        return dict(self.settings, running=self.running, message=self.message)

    def handle(self, path, data):
        """Every request also counts as a heartbeat."""
        with self._lock:
            self._last_ping = self._clock()
            if path == "/set":
                self.settings = update_settings(self.settings, data)
            elif path == "/start":
                self.running, self.message, self._lost_since = True, "", None
            elif path == "/stop":
                self._halt("หยุดแล้ว")
            elif path == "/save":
                return self._save_settings()
            elif path != "/ping":
                return None
            return self.state()

    def tick(self, now, line_found):
        """Called once per frame. Returns (settings, should_drive) after the safety checks."""
        with self._lock:
            if self.running and now - self._last_ping > HEARTBEAT_TIMEOUT:
                self._halt("หยุดเพราะหน้าเว็บขาดการเชื่อมต่อ")
            if line_found:
                self._lost_since = None
            elif self.running:
                self._lost_since = now if self._lost_since is None else self._lost_since
                if now - self._lost_since > LOST_LINE_STOP:
                    self._halt("หยุดเพราะไม่เห็นเส้นนานเกิน {:.0f} วินาที".format(LOST_LINE_STOP))
            return dict(self.settings), self.running

    def halt(self, message):
        with self._lock:
            if self.running:
                self._halt(message)

    def _halt(self, message):
        self.running = False
        self.message = message

    def _save_settings(self):
        reply = self.state()
        try:
            self._save(**self.settings)
        except OSError as exc:  # e.g. the SD card went read-only
            reply.update(saved=False, message="บันทึกไม่สำเร็จ: {}".format(exc))
        else:
            reply.update(saved=True, message="บันทึกแล้ว " + "  ".join(
                "{}={}".format(k, self.settings[k]) for k in sorted(LIMITS)))
        return reply


def steer_and_speed(result, pid, settings, steer, dt):
    """Same control as the notebook: PID on the line error, slow down in curves, keep the last steer when lost."""
    if not result.found:
        return steer, settings["min_speed"]
    steer = pid.update(result.error, dt)
    return steer, speed_for_error(result.error, settings["max_speed"], settings["min_speed"])


class PidPanel(Panel):
    name = "pid"
    title = "4 PID"
    controls = """
<h2>จูน PID (Module 4)</h2>
<div class="row2"><button class="go" id="pid_start">Start</button><button class="halt" id="pid_stop">Stop (Space)</button></div>
<p class="big" id="pid_timer" aria-label="เวลาที่วิ่ง">0.0 s</p>
<label><span>Kp: เลี้ยวแรงตาม error <b id="pid_kp_v"></b></span>
  <input id="pid_kp" type="range" min="0" max="2" step="0.01"></label>
<label><span>Kd: ลดการส่าย <b id="pid_kd_v"></b></span>
  <input id="pid_kd" type="range" min="0" max="0.5" step="0.005"></label>
<label><span>max_speed: ความเร็วทางตรง <b id="pid_max_speed_v"></b></span>
  <input id="pid_max_speed" type="range" min="0.1" max="0.8" step="0.01"></label>
<label><span>min_speed: ความเร็วในโค้ง <b id="pid_min_speed_v"></b></span>
  <input id="pid_min_speed" type="range" min="0" max="0.6" step="0.01"></label>
<p class="hint">รถส่ายไปมา ลด Kp หรือเพิ่ม Kd · เข้าโค้งไม่ทัน เพิ่ม Kp หรือลด min_speed</p>
<button class="save" id="pid_save">บันทึกลง my_params.json</button>
"""
    script = """
let startedAt = null, lastRun = 0;
panels.pid = {show(s) {
  for (const k of ["kp", "kd", "max_speed", "min_speed"]) setRange("pid", k, s[k]);
  $("pid_start").disabled = s.running; $("pid_stop").disabled = !s.running;
  if (s.running && startedAt === null) startedAt = performance.now();
  if (!s.running && startedAt !== null) { lastRun = performance.now() - startedAt; startedAt = null; }  // keep the lap time
}};
for (const k of ["kp", "kd", "max_speed", "min_speed"]) range("pid", k);
$("pid_start").addEventListener("click", () => { say(""); act("start"); });
$("pid_stop").addEventListener("click", () => act("stop"));
$("pid_save").addEventListener("click", () => act("save"));
setInterval(() => {
  $("pid_timer").textContent = ((startedAt !== null ? performance.now() - startedAt : lastRun) / 1000).toFixed(1) + " s";
}, 100);
"""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.driver = Driver(update_settings(DEFAULTS, {k: ctx.pid[k] for k in LIMITS}), save=ctx.save, clock=ctx.clock)
        self.pid = PID(kp=ctx.pid["kp"], kd=ctx.pid["kd"])
        self.steer, self.moving, self._last = 0.0, False, None

    def state(self):
        reply = self.driver.handle("/ping", {})  # the page's ping is the driver's heartbeat too
        reply["level"] = "bad" if reply["message"].startswith("หยุดเพราะ") else ""
        return reply

    def handle(self, action, data):
        reply = self.driver.handle(action, data)
        self.ctx.pid = dict(self.driver.settings)  # the mission tab drives with these gains
        return reply

    def halt(self, message):
        self.driver.halt(message)

    def step(self, frame, now, fps):
        dt = max(now - self._last, 1e-3) if self._last is not None else 0.033
        self._last = now
        result = detect_line(frame, self.ctx.line)
        settings, drive = self.driver.tick(now, result.found)
        self.pid.kp, self.pid.kd = settings["kp"], settings["kd"]
        motors = None
        if drive:
            if not self.moving:
                self.pid.reset()
                self.steer = 0.0
            self.steer, speed = steer_and_speed(result, self.pid, settings, self.steer, dt)
            motors = mix_motors(speed, self.steer, self.ctx.trim)
        self.moving = drive
        left, right = motors or (0.0, 0.0)
        state = VizState(fsm_state="RUN" if drive else "STOP", line_roi=result.roi_box, cx=result.cx, cy=result.cy,
                         steer=self.steer, motor_left=left, motor_right=right, fps=fps)
        return with_mask(draw_overlay(frame, state), result.mask), motors
