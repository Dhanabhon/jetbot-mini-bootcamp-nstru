"""Module 2 panel: drive straight, measure the drift, and let the app work out the motor trim."""
from ..pid import mix_motors
from ..viz import VizState, draw_overlay
from .core import Panel, TimedDrive

LIMITS = {"test_speed": (0.2, 0.8), "seconds": (0.5, 4.0), "left_gain": (0.5, 1.0), "right_gain": (0.5, 1.0)}
MAX_DRIFT_CM = 50
STEP_PER_CM = 0.005  # gain removed from the faster wheel per cm of drift, same as the notebook


def adjust_trim(trim, drift_cm, step_per_cm=STEP_PER_CM):
    """Slow the faster wheel: drift right (+) means the left wheel is faster. Gains never drop below the limit."""
    change = abs(drift_cm) * step_per_cm
    low = LIMITS["left_gain"][0]
    if drift_cm > 0:
        return trim._replace(left_gain=round(max(low, trim.left_gain - change), 3))
    if drift_cm < 0:
        return trim._replace(right_gain=round(max(low, trim.right_gain - change), 3))
    return trim


def _clamp(key, value):
    low, high = LIMITS[key]
    return round(min(high, max(low, float(value))), 3)


class TrimPanel(Panel):
    name = "trim"
    title = "2 Trim"
    controls = """
<h2>ปรับให้รถวิ่งตรง (Module 2)</h2>
<ol class="hint">
  <li>แปะเทปเส้นตรง 1 เมตร วางรถให้ล้อหน้าอยู่ต้นเส้น หันตามเส้น</li>
  <li>กด <b>วิ่งทดสอบ</b> แล้ววัดว่าปลายทางเบี้ยวออกจากเส้นกี่ ซม.</li>
  <li>ใส่ระยะ (เบี้ยวขวาเป็นบวก ซ้ายเป็นลบ) กด <b>ปรับ trim</b> แล้ววิ่งซ้ำ จนเบี้ยวไม่เกิน 2 ซม.</li>
</ol>
<label><span>ความเร็วทดสอบ (ใช้ความเร็วที่จะแข่ง) <b id="trim_test_speed_v"></b></span>
  <input id="trim_test_speed" type="range" min="0.2" max="0.8" step="0.05"></label>
<label><span>วิ่งนาน (วินาที) <b id="trim_seconds_v"></b></span>
  <input id="trim_seconds" type="range" min="0.5" max="4" step="0.5"></label>
<div class="row2"><button class="go" id="trim_run">วิ่งทดสอบ</button><button class="halt" id="trim_stop">Stop (Space)</button></div>
<label><span>เบี้ยวไปกี่ ซม. (ขวา +, ซ้าย -)</span><input id="trim_drift" type="number" min="-50" max="50" step="0.5" value="0"></label>
<button class="blue" id="trim_adjust">ปรับ trim</button>
<label><span>left_gain <b id="trim_left_gain_v"></b></span>
  <input id="trim_left_gain" type="range" min="0.5" max="1" step="0.005"></label>
<label><span>right_gain <b id="trim_right_gain_v"></b></span>
  <input id="trim_right_gain" type="range" min="0.5" max="1" step="0.005"></label>
<div class="row2"><button id="trim_reset">เริ่มใหม่ 1.00 / 1.00</button><button class="save" id="trim_save">บันทึก</button></div>
"""
    script = """
panels.trim = {show(s) {
  for (const k of ["test_speed", "seconds", "left_gain", "right_gain"]) setRange("trim", k, s[k]);
  $("trim_run").disabled = s.running; $("trim_stop").disabled = !s.running;
}};
for (const k of ["test_speed", "seconds", "left_gain", "right_gain"]) range("trim", k);
$("trim_run").addEventListener("click", () => act("run"));
$("trim_stop").addEventListener("click", () => act("stop"));
$("trim_adjust").addEventListener("click", () => act("drift", {cm: Number($("trim_drift").value)}).then(() => { $("trim_drift").value = 0; }));
$("trim_reset").addEventListener("click", () => act("set", {left_gain: 1, right_gain: 1}));
$("trim_save").addEventListener("click", () => act("save"));
"""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.test_speed = _clamp("test_speed", ctx.params.get("trim_speed", 0.5))
        self.seconds = 2.0
        self.timed = TimedDrive()
        self.message = ""

    def state(self):
        with self._lock:
            return self._snapshot()

    def handle(self, action, data):
        with self._lock:
            if action == "/set":
                self._set(data)
            elif action == "/run":
                motors = mix_motors(self.test_speed, 0.0, self.ctx.trim)
                self.timed.start(motors, self.seconds, self.ctx.clock())
                self.message = "วิ่งทดสอบ {} วินาที L {:.2f} R {:.2f}".format(self.seconds, *motors)
            elif action == "/stop":
                self.timed.stop()
                self.message = "หยุดแล้ว"
            elif action == "/drift":
                cm = float(data.get("cm", 0))
                if abs(cm) > MAX_DRIFT_CM:
                    raise ValueError("drift must be within ±{} cm".format(MAX_DRIFT_CM))
                self.ctx.trim = adjust_trim(self.ctx.trim, cm)
                self.message = "trim ใหม่ left {} right {} กดวิ่งทดสอบอีกรอบ".format(*self.ctx.trim)
            elif action == "/save":
                return self._save()
            else:
                return None
            return self._snapshot()

    def halt(self, message):
        with self._lock:
            if self.timed.running(self.ctx.clock()):
                self.timed.stop()
                self.message = message

    def step(self, frame, now, fps):
        with self._lock:
            motors = self.timed.command(now)
        left, right = motors or (0.0, 0.0)
        return draw_overlay(frame, VizState(fsm_state="TRIM RUN" if motors else "TRIM", motor_left=left,
                                            motor_right=right, fps=fps)), motors

    def _snapshot(self):
        return {"test_speed": self.test_speed, "seconds": self.seconds, "left_gain": self.ctx.trim.left_gain,
                "right_gain": self.ctx.trim.right_gain, "running": self.timed.running(self.ctx.clock()),
                "message": self.message}

    def _set(self, data):
        changes = {}
        for key, value in data.items():
            if key not in LIMITS:
                raise ValueError("unknown setting: {}".format(key))
            changes[key] = _clamp(key, value)
        self.test_speed = changes.get("test_speed", self.test_speed)
        self.seconds = changes.get("seconds", self.seconds)
        gains = {k: changes[k] for k in ("left_gain", "right_gain") if k in changes}
        self.ctx.trim = self.ctx.trim._replace(**gains)  # every other tab drives with this trim right away

    def _save(self):
        trim = self.ctx.trim
        try:
            self.ctx.save(left_gain=trim.left_gain, right_gain=trim.right_gain, trim_speed=self.test_speed)
        except OSError as exc:  # e.g. the SD card went read-only
            self.message = "บันทึกไม่สำเร็จ: {}".format(exc)
            return dict(self._snapshot(), saved=False)
        self.message = "บันทึกแล้ว left_gain={} right_gain={}".format(*trim)
        return dict(self._snapshot(), saved=True)
