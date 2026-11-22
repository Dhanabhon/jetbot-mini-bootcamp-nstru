"""Module 1 panel: check the robot before anything else (battery, camera, buzzer, OLED, a short drive)."""
from ..viz import VizState, draw_overlay
from .core import Panel, TimedDrive

EMPTY_V = 10.5  # 3S Li-ion, 3.5 V per cell
FULL_V = 12.6
TEST_DRIVE = (0.3, 0.3)  # slow, both wheels forward, like the notebook's first trial
TEST_SECONDS = 1.0
MAX_OLED_TEXT = 40


def battery_percent(voltage):
    """Straight line from EMPTY_V = 0 % to FULL_V = 100 %, clamped to 0..100."""
    percent = (voltage - EMPTY_V) / (FULL_V - EMPTY_V) * 100
    return max(0.0, min(100.0, percent))


class CheckPanel(Panel):
    name = "check"
    title = "1 ตรวจเครื่อง"
    controls = """
<h2>ตรวจเครื่อง (Module 1)</h2>
<table>
  <tr><td>แบตเตอรี่</td><td><b id="check_batt">-</b></td></tr>
  <tr><td>กล้อง</td><td><b id="check_fps">-</b></td></tr>
  <tr><td>จอ OLED</td><td><b id="check_oled">-</b></td></tr>
</table>
<p class="hint">แบตเต็ม 12.6 V ควรชาร์จเมื่อต่ำกว่า 11.1 V และห้ามใช้ต่อเมื่อต่ำกว่า 10.5 V</p>
<div class="row2"><button class="blue" id="check_beep">เสียง beep</button><button class="go" id="check_drive">เดินหน้า 1 วินาที</button></div>
<label><span>ข้อความบนจอ OLED (ภาษาอังกฤษ)</span><input id="check_text" type="text" maxlength="40" value="NSTRU"></label>
<button class="blue" id="check_show">แสดงบนจอ</button>
<p class="hint">วางรถบนพื้นก่อนกดเดินหน้า ไม่ใช่บนโต๊ะ</p>
"""
    script = """
panels.check = {show(s) {
  $("check_batt").textContent = s.battery == null ? "อ่านไม่ได้ " + s.battery_error : s.battery.toFixed(2) + " V (" + s.percent.toFixed(0) + "%)";
  $("check_fps").textContent = s.fps == null ? "ยังไม่มีภาพ" : s.fps.toFixed(1) + " เฟรมต่อวินาที";
  $("check_oled").textContent = s.oled ? "พร้อม" : "ไม่พบ";
  $("check_drive").disabled = s.driving;
}};
$("check_beep").addEventListener("click", () => act("beep"));
$("check_drive").addEventListener("click", () => act("drive"));
$("check_show").addEventListener("click", () => act("oled", {text: $("check_text").value}));
"""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.timed = TimedDrive()
        self.fps = None
        self.message = ""

    def state(self):
        volts = self.ctx.battery()
        with self._lock:
            return {"battery": volts, "percent": battery_percent(volts) if volts is not None else None,
                    "battery_error": self.ctx.battery_error, "fps": self.fps, "oled": self.ctx.oled is not None,
                    "driving": self.timed.running(self.ctx.clock()), "message": self.message}

    def handle(self, action, data):
        if action == "/beep":
            self._say("ส่งเสียงแล้ว" if self.ctx.beep() else "หา buzzer ไม่เจอ (ดู log ใน Terminal)")
        elif action == "/oled":
            text = str(data.get("text", ""))[:MAX_OLED_TEXT]
            if self.ctx.oled is None:
                self._say("ไม่พบจอ OLED")
            else:
                self.ctx.show(text, big=len(text) <= 8)
                self._say("แสดง '{}' แล้ว ถ้าข้อความหายไปเอง ให้หยุดโปรแกรมแสดงสถานะก่อน".format(text))
        elif action == "/drive":
            with self._lock:
                self.timed.start(TEST_DRIVE, TEST_SECONDS, self.ctx.clock())
                self.message = "เดินหน้า {} วินาที".format(TEST_SECONDS)
        else:
            return None
        return self.state()

    def halt(self, message):
        with self._lock:
            if self.timed.running(self.ctx.clock()):
                self.timed.stop()
                self.message = message

    def step(self, frame, now, fps):
        with self._lock:
            self.fps = fps
            motors = self.timed.command(now)
        left, right = motors or (0.0, 0.0)
        return draw_overlay(frame, VizState(fsm_state="DRIVE" if motors else "CHECK", motor_left=left,
                                            motor_right=right, fps=fps)), motors

    def _say(self, message):
        with self._lock:
            self.message = message
