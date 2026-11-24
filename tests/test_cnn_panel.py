"""Module 5 CNN tab: collect photos, train ResNet18 on the robot from the page, then read signs live.

torch is not needed here: the trainer and the model loader are replaced with fakes.
"""
import importlib.util
import os
import threading

import numpy as np
import pytest

from jetbot_nstru import cnn
from jetbot_nstru.app import PANEL_TYPES, build_page
from jetbot_nstru.app.cnn import CNN_NAMES, MIN_PER_SIGN, CnnPanel

from test_app import BLANK, ROOT, make_ctx


class FakeModel:
    def __init__(self, path, answer=("stop", 0.93)):
        self.path, self.answer = path, answer

    def predict(self, frame):
        return self.answer


def fill_dataset(folder, per_sign=MIN_PER_SIGN):
    for name in CNN_NAMES:
        os.makedirs(str(folder / name))
        for i in range(per_sign):
            (folder / name / "{}.jpg".format(i)).write_bytes(b"x")


def make_panel(tmp_path, trainer=None, loader=FakeModel, weights="/w/resnet18-f37072fd.pth", per_sign=MIN_PER_SIGN):
    ctx, clock = make_ctx()
    dataset = tmp_path / "signs"
    if per_sign and not dataset.exists():
        fill_dataset(dataset, per_sign)
    panel = CnnPanel(ctx, dataset_dir=str(dataset), model_path=str(tmp_path / "models" / "sign.pth"),
                     trainer=trainer, loader=loader, weights=lambda: weights)
    return panel, clock


def fake_trainer(accuracies):
    calls = []

    def train(dataset_dir, model_path, epochs, on_epoch, should_stop, weights_path):
        calls.append((epochs, weights_path))
        best = None
        for epoch, accuracy in enumerate(accuracies[:epochs], 1):
            if should_stop():
                break
            best = accuracy if best is None else max(best, accuracy)
            on_epoch(epoch, accuracy, best)
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        open(model_path, "w").close()
        return best

    return train, calls


def finish(panel):
    panel._thread.join(5)
    assert not panel._thread.is_alive()


def test_snap_saves_photos_for_each_sign_and_for_no_sign(tmp_path):
    panel, clock = make_panel(tmp_path, per_sign=0)
    panel.step(BLANK, clock.now, 30.0)
    assert panel.handle("/snap", {"label": "none"})["counts"]["none"] == 1
    assert panel.handle("/snap", {"label": "stop"})["counts"]["stop"] == 1
    with pytest.raises(ValueError):
        panel.handle("/snap", {"label": "../x"})


def test_train_refuses_when_a_sign_has_too_few_photos(tmp_path):
    train, calls = fake_trainer([0.9])
    panel, _ = make_panel(tmp_path, trainer=train, per_sign=0)
    state = panel.handle("/train", {})
    assert state["training"] is False and "ภาพยังไม่พอ" in state["message"] and calls == []


def test_train_refuses_without_pretrained_weights(tmp_path):
    train, calls = fake_trainer([0.9])
    panel, _ = make_panel(tmp_path, trainer=train, weights=None)
    state = panel.handle("/train", {})
    assert state["training"] is False and "resnet18" in state["message"] and calls == []


def test_train_runs_in_the_background_then_loads_the_model_and_reads_signs(tmp_path):
    train, calls = fake_trainer([0.6, 0.8, 0.75])
    panel, clock = make_panel(tmp_path, trainer=train)
    assert panel.state()["model"] is False
    panel.handle("/set", {"epochs": 3})
    assert panel.handle("/train", {})["training"] is True
    finish(panel)
    state = panel.state()
    assert calls == [(3, "/w/resnet18-f37072fd.pth")]
    assert state["training"] is False and state["model"] is True and state["best"] == 0.8
    assert "3/3" in state["progress"]
    picture, motors = panel.step(BLANK, clock.now, 30.0)
    assert motors is None and picture.shape == BLANK.shape  # this tab never drives
    assert panel.state()["prediction"] == {"label": "stop", "confidence": 0.93}


def test_stop_training_ends_after_the_current_step(tmp_path):
    seen = []

    def train(dataset_dir, model_path, epochs, on_epoch, should_stop, weights_path):
        on_epoch(1, 0.5, 0.5)
        panel.handle("/stop_train", {})
        seen.append(should_stop())
        return 0.5

    panel, _ = make_panel(tmp_path, trainer=train)
    panel.handle("/train", {})
    finish(panel)
    assert seen == [True] and panel.state()["training"] is False and "หยุด" in panel.state()["message"]


def test_a_failed_training_reports_the_error_and_keeps_the_app_running(tmp_path):
    def train(*args):
        raise RuntimeError("CUDA out of memory")

    panel, clock = make_panel(tmp_path, trainer=train)
    panel.handle("/train", {})
    finish(panel)
    assert "CUDA out of memory" in panel.state()["message"] and panel.state()["training"] is False
    assert panel.step(BLANK, clock.now, 30.0)[1] is None


def test_only_one_training_at_a_time_and_no_live_reading_while_it_runs(tmp_path):
    release = threading.Event()
    calls = []

    def train(dataset_dir, model_path, epochs, on_epoch, should_stop, weights_path):
        calls.append(1)
        release.wait(5)
        return 0.9

    panel, clock = make_panel(tmp_path, trainer=train)
    panel.classifier = FakeModel("old")
    panel.handle("/train", {})
    assert "กำลังเทรน" in panel.handle("/train", {})["message"] and calls == [1]
    panel.step(BLANK, clock.now, 30.0)
    assert panel.state()["prediction"]["label"] is None  # the GPU is busy training
    release.set()
    finish(panel)


def test_confidence_threshold_and_the_no_sign_class(tmp_path):
    panel, clock = make_panel(tmp_path)
    panel.classifier = FakeModel("x", ("left", 0.55))
    panel.handle("/set", {"threshold": 0.6})
    panel.step(BLANK, clock.now, 30.0)
    assert panel.state()["prediction"]["label"] is None  # not sure enough
    panel.handle("/set", {"threshold": 0.5})
    panel.step(BLANK, clock.now, 30.0)
    assert panel.state()["prediction"]["label"] == "left"
    panel.classifier = FakeModel("x", ("none", 0.99))
    panel.step(BLANK, clock.now, 30.0)
    assert panel.state()["prediction"]["label"] is None
    with pytest.raises(ValueError):
        panel.handle("/set", {"epochs": 0})
    with pytest.raises(ValueError):
        panel.handle("/set", {"threshold": 2})


def test_a_saved_model_loads_at_start_and_a_broken_one_is_reported(tmp_path):
    os.makedirs(str(tmp_path / "models"))
    (tmp_path / "models" / "sign.pth").write_bytes(b"x")
    panel, _ = make_panel(tmp_path)
    assert panel.state()["model"] is True

    def broken(path):
        raise ImportError("No module named 'torch'")

    panel, _ = make_panel(tmp_path, loader=broken)
    assert panel.state()["model"] is False and "torch" in panel.state()["message"]


def test_the_imagenet_weights_come_with_the_repo():
    import hashlib
    path = cnn.find_pretrained()
    assert path == os.path.join(cnn.MODEL_DIR, cnn.WEIGHTS_NAME)
    with open(path, "rb") as handle:  # torchvision names the file after the start of its SHA-256
        assert hashlib.sha256(handle.read()).hexdigest().startswith(cnn.WEIGHTS_NAME[9:17])


def test_find_pretrained_looks_in_each_folder(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "resnet18-5c106cde.pth").write_bytes(b"x")
    assert cnn.find_pretrained([str(tmp_path / "a"), str(tmp_path / "b")]).endswith("resnet18-5c106cde.pth")
    assert cnn.find_pretrained([str(tmp_path / "a")]) is None


def test_cnn_tab_is_on_the_page_and_has_its_own_script(tmp_path):
    assert "cnn" in PANEL_TYPES
    panel, _ = make_panel(tmp_path)
    page = build_page("JetBot", [panel]).decode("utf-8")
    assert 'id="cnn_train"' in page and 'id="cnn_threshold"' in page
    path = os.path.join(ROOT, "notebooks", "solutions", "05_sign_cnn.py")
    spec = importlib.util.spec_from_file_location("sign_cnn", path)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    assert script.PANELS == ["cnn"]


def test_predict_turns_a_bgr_frame_into_a_label():
    torch = pytest.importorskip("torch")
    pytest.importorskip("torchvision")
    model = cnn.SignClassifier.__new__(cnn.SignClassifier)
    model.classes = list(CNN_NAMES)
    model.device = torch.device("cpu")
    model.model = cnn.resnet18(len(CNN_NAMES)).eval()
    label, confidence = model.predict(np.zeros((240, 320, 3), np.uint8))
    assert label in CNN_NAMES and 0.0 < confidence <= 1.0

