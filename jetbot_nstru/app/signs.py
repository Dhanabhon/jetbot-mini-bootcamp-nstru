"""Module 5 panel: watch sign detection live, see the numbers behind each label, and save training photos."""
import os
import threading
import uuid

import cv2

from ..params import REPO_ROOT
from ..signs import LABELS, SignConfig, SignVoter, classify, colour_masks, sign_features, white_mask
from ..viz import TEXT_COLOR, VizState, draw_overlay, with_mask
from .core import Panel

DATASET_DIR = os.path.join(REPO_ROOT, "dataset", "signs")
NAMES = tuple(label.lower() for label in LABELS)  # folder names, same as the notebook
MASKS = ("none", "blue", "red", "white")


def count_images(dataset_dir):
    """Number of .jpg files saved for each sign."""
    counts = {}
    for name in NAMES:
        folder = os.path.join(dataset_dir, name)
        counts[name] = len([f for f in os.listdir(folder) if f.endswith(".jpg")]) if os.path.isdir(folder) else 0
    return counts


class Viewer:
    """Latest camera frame and the page's choices, shared between the web server thread and the camera loop."""

    def __init__(self, dataset_dir=DATASET_DIR):
        self.dataset_dir = dataset_dir
        self.mask = "none"
        self.counts = count_images(dataset_dir)
        self._frame = None
        self._lock = threading.Lock()

    def put_frame(self, frame):
        with self._lock:
            self._frame = frame

    def current_mask(self):
        with self._lock:
            return self.mask

    def state(self):
        return {"mask": self.mask, "counts": dict(self.counts)}

    def handle(self, path, data):
        """/set picks the mask, /snap saves the current frame."""
        with self._lock:
            if path == "/set":
                mask = data.get("mask", self.mask)
                if mask not in MASKS:
                    raise ValueError("mask must be one of {}".format(MASKS))
                self.mask = mask
                return self.state()
            if path == "/snap":
                return self._snap(data.get("label"))
        return None

    def _snap(self, label):
        if label not in NAMES:
            raise ValueError("label must be one of {}".format(NAMES))
        reply = self.state()
        if self._frame is None:
            reply.update(saved=False, message="ยังไม่มีภาพจากกล้อง")
            return reply
        folder = os.path.join(self.dataset_dir, label)
        path = os.path.join(folder, "{}.jpg".format(uuid.uuid4().hex[:12]))
        try:
            os.makedirs(folder, exist_ok=True)
            if not cv2.imwrite(path, self._frame):
                raise OSError("cv2.imwrite could not write {}".format(path))
        except OSError as exc:  # e.g. the SD card went read-only
            reply.update(saved=False, message="บันทึกภาพไม่สำเร็จ: {}".format(exc))
            return reply
        self.counts[label] += 1
        reply = self.state()
        reply.update(saved=True, message="เก็บภาพ {} แล้ว ({} ภาพ)".format(label, self.counts[label]))
        return reply


def describe(features):
    """Short ASCII text of what decided the label, e.g. 'blue ext 0.79 bal +0.03'."""
    if features is None:
        return "no sign"
    text = "{} ext {:.2f}".format(features.colour, features.extent)
    return text if features.balance is None else text + " bal {:+.2f}".format(features.balance)


def render(frame, features, confirmed, mask_name, fps, cfg=SignConfig()):
    """Frame with the search area, sign box, measured features and confirmed label, plus the chosen mask below."""
    detection = classify(features, cfg) if features else None
    status = "{}  {}".format("SIGN " + confirmed if confirmed else "-", describe(features))
    out = draw_overlay(frame, VizState(fsm_state=status, sign=detection, fps=fps))
    bottom = int(frame.shape[0] * cfg.search_bottom)
    cv2.line(out, (0, bottom), (frame.shape[1] - 1, bottom), TEXT_COLOR, 1)  # signs are only searched above this
    if mask_name == "none":
        return out
    hsv = cv2.cvtColor(frame[:bottom], cv2.COLOR_BGR2HSV)
    if mask_name == "white":
        return with_mask(out, white_mask(hsv, cfg))
    blue, red = colour_masks(hsv, cfg)
    return with_mask(out, blue if mask_name == "blue" else red)


class SignPanel(Panel):
    name = "signs"
    title = "5 ป้าย"
    controls = """
<h2>ดูการอ่านป้าย (Module 5)</h2>
<div class="row2" role="radiogroup" aria-label="ภาพด้านล่าง">
  <label class="row"><input type="radio" name="signs_mask" value="none"> ไม่แสดง mask</label>
  <label class="row"><input type="radio" name="signs_mask" value="blue"> mask น้ำเงิน</label>
  <label class="row"><input type="radio" name="signs_mask" value="red"> mask แดง</label>
  <label class="row"><input type="radio" name="signs_mask" value="white"> mask ขาว (ลูกศร)</label>
</div>
<p class="hint">บนภาพ: <b>ext</b> ต่ำกว่า 0.90 คือป้ายกลม ตั้งแต่ 0.90 คือ PARKING ·
  <b>bal</b> เกิน +0.15 คือ LEFT ต่ำกว่า -0.15 คือ RIGHT ระหว่างนั้นคือ STRAIGHT</p>
<h3>เก็บภาพไว้เทรน (กดเลข 1-5 บนคีย์บอร์ดได้)</h3>
<div class="row2" id="signs_snaps"></div>
"""
    script = """
const signNames = NAMES_JSON;
signNames.forEach((name, i) => {
  const b = document.createElement("button");
  b.className = name === "stop" ? "halt" : "blue";
  b.innerHTML = "<kbd>" + (i + 1) + "</kbd> " + name + " <span id=signs_n_" + name + ">0</span>";
  b.addEventListener("click", () => act("snap", {label: name}));
  $("signs_snaps").appendChild(b);
});
panels.signs = {show(s) {
  document.querySelector('input[name=signs_mask][value="' + s.mask + '"]').checked = true;
  for (const name of signNames) $("signs_n_" + name).textContent = s.counts[name];
}};
for (const r of document.querySelectorAll("input[name=signs_mask]")) r.addEventListener("change", e => act("set", {mask: e.target.value}));
document.addEventListener("keydown", e => {
  const i = Number(e.key) - 1;
  if (active === "signs" && !e.repeat && e.target.tagName !== "INPUT" && i >= 0 && i < signNames.length)
    act("snap", {label: signNames[i]});
});
""".replace("NAMES_JSON", "[" + ", ".join('"{}"'.format(name) for name in NAMES) + "]")

    def __init__(self, ctx, dataset_dir=DATASET_DIR):
        super().__init__(ctx)
        self.viewer = Viewer(dataset_dir)
        self.voter = SignVoter(window=7, min_votes=4)

    def state(self):
        return self.viewer.state()

    def handle(self, action, data):
        return self.viewer.handle(action, data)

    def step(self, frame, now, fps):
        self.viewer.put_frame(frame)
        features = sign_features(frame)
        confirmed = self.voter.update(classify(features).label if features else None)
        return render(frame, features, confirmed, self.viewer.current_mask(), fps), None
