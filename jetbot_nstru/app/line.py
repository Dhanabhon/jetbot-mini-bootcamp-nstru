"""Module 3 panel: tune the black-line mask (roi_top, black_v_max) and see the line and green masks live."""
import threading

import cv2

from ..line import detect_line, green_mask
from ..viz import SIGN_BOX_COLOR, VizState, draw_overlay, with_mask
from .core import Panel

# Same ranges as the notebook. An int range keeps the value an int.
LIMITS = {"roi_top": (0.30, 0.90), "black_v_max": (20, 200)}
MASKS = ("line", "green")


def update_config(cfg, data):
    """A new LineConfig with the browser's values clamped to LIMITS. Unknown keys raise ValueError."""
    changes = {}
    for key, value in data.items():
        if key not in LIMITS:
            raise ValueError("unknown setting: {}".format(key))
        low, high = LIMITS[key]
        number = min(high, max(low, float(value)))
        changes[key] = int(round(number)) if isinstance(low, int) else round(number, 2)
    return cfg._replace(**changes)


class Tuner:
    """Settings shared between the web server thread and the camera loop."""

    def __init__(self, cfg, save):
        self.cfg = cfg
        self.mask = "line"
        self._save = save
        self._lock = threading.Lock()

    def snapshot(self):
        with self._lock:
            return self.cfg, self.mask

    def state(self):
        return {"roi_top": self.cfg.roi_top, "black_v_max": self.cfg.black_v_max, "mask": self.mask}

    def handle(self, path, data):
        """/set changes settings, /save writes them to my_params.json."""
        with self._lock:
            if path == "/set":
                data = dict(data)
                mask = data.pop("mask", self.mask)
                if mask not in MASKS:
                    raise ValueError("mask must be one of {}".format(MASKS))
                self.cfg = update_config(self.cfg, data)
                self.mask = mask
                return self.state()
            if path == "/save":
                reply = self.state()
                try:
                    self._save(roi_top=self.cfg.roi_top, black_v_max=self.cfg.black_v_max)
                except OSError as exc:  # e.g. the SD card went read-only
                    reply.update(saved=False, message="บันทึกไม่สำเร็จ: {}".format(exc))
                else:
                    reply.update(saved=True, message="บันทึกแล้ว roi_top={} black_v_max={}".format(
                        self.cfg.roi_top, self.cfg.black_v_max))
                return reply
        return None


def render(frame, cfg, mask_name, fps):
    """Camera frame with ROI, centroid and green box drawn on it, and the chosen mask stacked below."""
    result = detect_line(frame, cfg)
    state = VizState(fsm_state="GREEN" if result.green_box else "", line_roi=result.roi_box,
                     cx=result.cx, cy=result.cy, fps=fps)
    out = draw_overlay(frame, state)
    if result.green_box:
        x, y, w, h = result.green_box
        cv2.rectangle(out, (x, y), (x + w, y + h), SIGN_BOX_COLOR, 2)
    mask = result.mask
    if mask_name == "green":
        x0, y0, w, h = result.roi_box
        mask = green_mask(frame[y0:y0 + h, x0:x0 + w], cfg)
    return with_mask(out, mask)


class LinePanel(Panel):
    name = "line"
    title = "3 เส้นดำ"
    controls = """
<h2>จูนการหาเส้นดำ (Module 3)</h2>
<label><span>roi_top: ขอบบนของกรอบที่หาเส้น <b id="line_roi_top_v"></b></span>
  <input id="line_roi_top" type="range" min="0.3" max="0.9" step="0.01"></label>
<label><span>black_v_max: มืดกว่านี้นับเป็นเส้น <b id="line_black_v_max_v"></b></span>
  <input id="line_black_v_max" type="range" min="20" max="200" step="1"></label>
<div class="row2" role="radiogroup" aria-label="ภาพด้านล่าง">
  <label class="row"><input type="radio" name="line_mask" value="line"> mask เส้นดำ</label>
  <label class="row"><input type="radio" name="line_mask" value="green"> mask สีเขียว</label>
</div>
<p class="hint">ใน mask เส้นต้องเป็นสีขาวเส้นเดียวชัด ๆ พื้นเป็นสีดำ ถ้าพื้นมีจุดขาวเยอะ ลด <b>black_v_max</b></p>
<button class="save" id="line_save">บันทึกลง my_params.json</button>
"""
    script = """
panels.line = {show(s) {
  setRange("line", "roi_top", s.roi_top); setRange("line", "black_v_max", s.black_v_max);
  document.querySelector('input[name=line_mask][value="' + s.mask + '"]').checked = true;
}};
range("line", "roi_top"); range("line", "black_v_max");
for (const r of document.querySelectorAll("input[name=line_mask]")) r.addEventListener("change", e => act("set", {mask: e.target.value}));
$("line_save").addEventListener("click", () => act("save"));
"""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.tuner = Tuner(ctx.line, save=ctx.save)

    def state(self):
        return self.tuner.state()

    def handle(self, action, data):
        reply = self.tuner.handle(action, data)
        self.ctx.line = self.tuner.snapshot()[0]  # PID and mission tabs follow the line settings right away
        return reply

    def step(self, frame, now, fps):
        cfg, mask_name = self.tuner.snapshot()
        return render(frame, cfg, mask_name, fps), None
