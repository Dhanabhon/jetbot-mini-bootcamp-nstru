"""Module 5 CNN tab: collect photos, train ResNet18 on the robot's GPU with one button, then read signs live.

Training runs in a background thread so the page and the camera keep going; live reading pauses meanwhile
because the Nano's 4 GB is shared by both. This tab never drives the motors.
"""
import os
import threading

from .. import cnn
from ..viz import VizState, draw_overlay
from .core import Panel
from .signs import DATASET_DIR, NAMES, Viewer

CNN_NAMES = NAMES + ("none",)  # "none": the track with no sign, else the model calls every frame some sign
MIN_PER_SIGN = 20  # below this the test split is too small to trust; 100 per class works much better
EPOCH_LIMITS = (1, 30)
THRESHOLD_LIMITS = (0.3, 0.99)


def _number(data, key, limits, cast):
    value = cast(data[key])
    if not limits[0] <= value <= limits[1]:
        raise ValueError("{} must be between {} and {}".format(key, *limits))
    return value


class CnnPanel(Panel):
    name = "cnn"
    title = "5 ป้าย CNN"
    controls = """
<h2>อ่านป้ายด้วย CNN (ResNet18)</h2>
<p class="big" id="cnn_pred" aria-live="polite">-</p>
<h3>1. เก็บภาพ (กดเลข 1-6 บนคีย์บอร์ดได้)</h3>
<div class="row2" id="cnn_snaps"></div>
<p class="hint">อย่างน้อย MIN ภาพต่อชนิด แนะนำ 100 หลายระยะ หลายมุม หลายแสง ·
  <b>none</b> คือพื้นสนามที่ไม่มีป้าย ต้องเก็บด้วย ไม่งั้น model จะเห็นป้ายทุกเฟรม</p>
<h3>2. เทรนบนรถ</h3>
<label><span>epochs: จำนวนรอบที่ดูภาพทั้งหมด <b id="cnn_epochs_v"></b></span>
  <input id="cnn_epochs" type="range" min="1" max="30" step="1"></label>
<div class="row2"><button class="go" id="cnn_train">เริ่มเทรน</button><button class="halt" id="cnn_stop_train">หยุดเทรน</button></div>
<p class="hint" id="cnn_progress" aria-live="polite"></p>
<h3>3. ทดสอบสด</h3>
<label><span>ความมั่นใจขั้นต่ำ: ต่ำกว่านี้ถือว่าไม่แน่ใจ <b id="cnn_threshold_v"></b></span>
  <input id="cnn_threshold" type="range" min="0.3" max="0.99" step="0.01"></label>
<p class="hint">ถือป้ายหน้ากล้องหลายระยะ ถ้าทายผิดบ่อย เก็บภาพมุมนั้นเพิ่มแล้วเทรนใหม่</p>
""".replace("MIN", str(MIN_PER_SIGN))
    script = """
const cnnNames = NAMES_JSON;
cnnNames.forEach((name, i) => {
  const b = document.createElement("button");
  b.className = name === "stop" ? "halt" : name === "none" ? "" : "blue";
  b.innerHTML = "<kbd>" + (i + 1) + "</kbd> " + name + " <span id=cnn_n_" + name + ">0</span>";
  b.addEventListener("click", () => act("snap", {label: name}));
  $("cnn_snaps").appendChild(b);
});
panels.cnn = {show(s) {
  for (const name of cnnNames) $("cnn_n_" + name).textContent = s.counts[name];
  setRange("cnn", "epochs", s.epochs); setRange("cnn", "threshold", s.threshold);
  $("cnn_train").disabled = s.training; $("cnn_stop_train").disabled = !s.training;
  $("cnn_progress").textContent = s.progress;
  const p = s.prediction;
  $("cnn_pred").textContent = s.training ? "กำลังเทรน" : !s.model ? "ยังไม่มี model"
    : p.label ? p.label.toUpperCase() + " " + Math.round(p.confidence * 100) + "%" : "-";
}};
range("cnn", "epochs"); range("cnn", "threshold");
$("cnn_train").addEventListener("click", () => act("train"));
$("cnn_stop_train").addEventListener("click", () => act("stop_train"));
document.addEventListener("keydown", e => {
  const i = Number(e.key) - 1;
  if (active === "cnn" && !e.repeat && e.target.tagName !== "INPUT" && i >= 0 && i < cnnNames.length)
    act("snap", {label: cnnNames[i]});
});
""".replace("NAMES_JSON", "[" + ", ".join('"{}"'.format(name) for name in CNN_NAMES) + "]")

    def __init__(self, ctx, dataset_dir=DATASET_DIR, model_path=cnn.MODEL_PATH, trainer=None, loader=None,
                 weights=None):
        """trainer, loader and weights default to the torch code in jetbot_nstru/cnn.py; tests pass fakes."""
        super().__init__(ctx)
        self.viewer = Viewer(dataset_dir, CNN_NAMES)
        self.dataset_dir, self.model_path = dataset_dir, model_path
        self.trainer = trainer or cnn.train
        self.loader = loader or cnn.SignClassifier
        self.find_weights = weights or cnn.find_pretrained
        self.epochs, self.threshold = 10, 0.7
        self.training, self.progress, self.best, self.message = False, "", None, ""
        self.classifier, self.prediction = None, (None, 0.0)
        self._stop = threading.Event()
        self._thread = None
        if os.path.exists(model_path):
            self._load()

    def state(self):
        with self._lock:
            label, confidence = self.prediction
            return {"counts": dict(self.viewer.counts), "epochs": self.epochs, "threshold": self.threshold,
                    "training": self.training, "progress": self.progress, "best": self.best,
                    "model": self.classifier is not None, "message": self.message,
                    "prediction": {"label": label, "confidence": round(confidence, 2)}}

    def handle(self, action, data):
        if action == "/snap":
            return dict(self.state(), **self.viewer.handle(action, data))
        if action == "/set":
            with self._lock:
                if "epochs" in data:
                    self.epochs = _number(data, "epochs", EPOCH_LIMITS, int)
                if "threshold" in data:
                    self.threshold = _number(data, "threshold", THRESHOLD_LIMITS, float)
            return self.state()
        if action == "/train":
            self._start_training()
            return self.state()
        if action == "/stop_train":
            self._stop.set()
            return self.state()
        return None

    def step(self, frame, now, fps):
        self.viewer.put_frame(frame)
        with self._lock:
            classifier = None if self.training else self.classifier
            threshold, training, best = self.threshold, self.training, self.best
        label, confidence = None, 0.0
        if classifier is not None:
            try:
                label, confidence = classifier.predict(frame)
            except Exception as exc:  # e.g. CUDA out of memory: report once, keep the camera going
                with self._lock:
                    self.classifier, self.message = None, "ทายภาพไม่ได้: {}".format(exc)
                classifier = None
        shown = label if label != "none" and confidence >= threshold else None
        with self._lock:
            self.prediction = (shown, confidence if shown else 0.0)
        if training:  # ASCII only: OpenCV can't draw Thai
            status = "TRAINING" + ("" if best is None else " best {:.0f}%".format(best * 100))
        elif classifier is None:
            status = "CNN: no model"
        else:
            status = "CNN {} {:.2f}".format(shown.upper() if shown else "-", confidence)
        return draw_overlay(frame, VizState(fsm_state=status, fps=fps)), None

    def _load(self):
        try:
            classifier, message = self.loader(self.model_path), "โหลด model แล้ว"
        except Exception as exc:  # no torch on a laptop, or a broken file: the tab still collects photos
            classifier, message = None, "โหลด model ไม่ได้: {}".format(exc)
        with self._lock:
            self.classifier, self.message = classifier, message

    def _start_training(self):
        with self._lock:
            if self.training:
                self.message = "กำลังเทรนอยู่ รอให้เสร็จหรือกดหยุดเทรนก่อน"
                return
            short = [name for name in CNN_NAMES if self.viewer.counts[name] < MIN_PER_SIGN]
            if short:
                self.message = "ภาพยังไม่พอ: {} ต้องมีอย่างน้อยชนิดละ {} ภาพ".format(", ".join(short), MIN_PER_SIGN)
                return
            weights = self.find_weights()
            if weights is None:
                self.message = ("ไม่พบไฟล์ models/{}: สั่ง git pull ใน ~/jetbot-mini-bootcamp-nstru "
                                "แล้วรันโปรแกรมใหม่".format(cnn.WEIGHTS_NAME))
                return
            self.training, self.best, self.message = True, None, ""
            self.progress = "กำลังโหลดภาพและ ResNet18..."
            self._stop.clear()
            self._thread = threading.Thread(target=self._train, args=(weights, self.epochs), daemon=True)
            self._thread.start()

    def _train(self, weights, epochs):
        def on_epoch(epoch, accuracy, best):
            with self._lock:
                self.best = round(best, 3)
                self.progress = "epoch {}/{} · accuracy {:.0f}% · ดีที่สุด {:.0f}%".format(
                    epoch, epochs, accuracy * 100, best * 100)

        try:
            best = self.trainer(self.dataset_dir, self.model_path, epochs, on_epoch, self._stop.is_set, weights)
            if best is None:
                message = "หยุดเทรนก่อนจบ epoch แรก ยังไม่มี model ใหม่"
            else:
                message = "{} ดีที่สุด {:.0f}% บันทึกที่ models/{}".format(
                    "หยุดเทรนแล้ว" if self._stop.is_set() else "เทรนเสร็จ", best * 100,
                    os.path.basename(self.model_path))
        except Exception as exc:  # out of memory, a bad photo: say so, keep the app and the old model
            best, message = None, "เทรนไม่สำเร็จ: {}".format(exc)
        if best is not None and os.path.exists(self.model_path):
            self._load()
        with self._lock:
            self.training, self.message = False, message
