"""Race day panel: tune on the browser tabs, then KEY1 on the robot starts the run and its timer, KEY1 again stops it.

A run started with KEY1 keeps going when the browser loses the robot (laptop put away, Wi-Fi drops), and it
also starts with no page open at all. KEY1, Stop / Space, closing the page, the 90 s limit and a lost line still stop it. A run started with the page's
Start button behaves like the mission tab and stops when the page goes quiet.
"""
from .line import LinePanel
from .mission import LOG_PATH, MissionPanel
from .pid import PidPanel
from .signs import SignPanel
from .trim import TrimPanel

KEY_DEBOUNCE = 0.5  # s; a contact bounce or a second press sooner than this is ignored


class KeyPresses:
    """Turns the key level read every frame into one event per press."""

    def __init__(self, debounce=KEY_DEBOUNCE):
        self.debounce = debounce
        self._down = False
        self._last = float("-inf")

    def update(self, down, now):
        """True on the frame the key goes down, unless the last press was under `debounce` seconds ago."""
        pressed = down and not self._down and now - self._last >= self.debounce
        if pressed:
            self._last = now
        self._down = down
        return pressed


def open_key1():
    """The board's KEY1, or None when it can't be read (no GPIO library, e.g. on a laptop)."""
    from ..hardware import Key1
    try:
        return Key1()
    except Exception as exc:  # the race still runs from the page's Start button
        print("อ่านปุ่ม KEY1 ไม่ได้ ({}) ใช้ปุ่ม Start บนหน้าเว็บแทน".format(exc))
        return None


class RacePanel(MissionPanel):
    """MissionPanel plus KEY1. It keeps the name "mission" so the page script and the /live screen work unchanged."""

    title = "แข่ง (KEY1)"
    controls = MissionPanel.controls.replace(
        "<h2>วิ่งภารกิจเต็ม (Module 6–7)</h2>",
        '<h2>วันแข่ง: กด KEY1 บนบอร์ดเพื่อเริ่มและจับเวลา กดอีกครั้งเพื่อหยุด</h2>\n'
        '<p class="hint" id="mission_key" aria-live="polite"></p>')
    script = MissionPanel.script + """
const missionShow = panels.mission.show;
panels.mission.show = s => { missionShow(s); $("mission_key").textContent = s.key; };
"""

    def __init__(self, ctx, key=None, watch_only=False, log_path=LOG_PATH):
        """key: anything with pressed(); None opens the board's KEY1, False means no key."""
        super().__init__(ctx, watch_only=watch_only, log_path=log_path)
        self.key = open_key1() if key is None else (key or None)
        self.presses = KeyPresses()
        self.key_run = False  # the current run was started with KEY1

    def step(self, frame, now, fps):
        if self.key is not None and self.presses.update(self.key.pressed(), now):
            self._toggle()
        return super().step(frame, now, fps)

    def page_optional(self):
        with self._lock:
            return self.running and self.key_run

    def _toggle(self):
        with self._lock:
            if self.running:
                self._finish("หยุดด้วย KEY1", finished=False)
            else:
                self._start()
                self.key_run = True
                self.message = "เริ่มด้วย KEY1 · กด KEY1 อีกครั้งเพื่อหยุด"
        self.ctx.beep()

    def _start(self):
        self.key_run = False  # the page's Start button; _toggle sets it after a KEY1 press
        super()._start()

    def _snapshot(self):
        if self.key is None:
            key = "ไม่พบปุ่ม KEY1: ใช้ปุ่ม Start บนหน้านี้ (รถจะหยุดถ้าปิดหน้าเว็บ)"
        elif self.running and self.key_run:
            key = "กำลังวิ่ง เริ่มด้วย KEY1 · Wi-Fi หลุดรถก็ยังวิ่งต่อ · กด KEY1 เพื่อหยุด"
        elif self.running:
            key = "กำลังวิ่ง เริ่มจากหน้าเว็บ · ห้ามปิดหน้านี้ · กด KEY1 หรือ Space เพื่อหยุด"
        else:
            key = "พร้อม: วางรถที่ START แล้วกด KEY1 (ต้องอยู่แท็บนี้)"
        return dict(super()._snapshot(), key=key)


# Tab order for jetbot_race.py: the race tab first, so KEY1 works without opening the page at all.
RACE_PANELS = [RacePanel, TrimPanel, LinePanel, PidPanel, SignPanel]
