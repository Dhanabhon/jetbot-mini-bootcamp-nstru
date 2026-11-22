"""The browser sign viewer for Module 5: photo capture, input checks and rendering."""
import os

import cv2
import numpy as np
import pytest

from jetbot_nstru.app import signs as viewer_mod
from jetbot_nstru.signs import sign_features

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scene(name, size=48):
    frame = np.full((240, 320, 3), 225, np.uint8)
    sign = cv2.resize(cv2.imread(os.path.join(ROOT, "tests", "fixtures", "signs", name + ".png")), (size, size))
    frame[30:30 + size, 200:200 + size] = sign
    return frame


def test_snap_saves_the_frame_into_the_sign_folder(tmp_path):
    viewer = viewer_mod.Viewer(str(tmp_path))
    assert viewer.handle("/snap", {"label": "left"})["saved"] is False  # no frame yet
    viewer.put_frame(scene("left"))
    reply = viewer.handle("/snap", {"label": "left"})
    assert reply["saved"] is True and reply["counts"]["left"] == 1
    files = os.listdir(str(tmp_path / "left"))
    assert len(files) == 1 and files[0].endswith(".jpg")
    assert viewer_mod.count_images(str(tmp_path))["left"] == 1  # counted again after a restart


def test_snap_failure_is_reported_not_raised(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where the dataset folder should be")
    viewer = viewer_mod.Viewer(str(blocker))
    viewer.put_frame(scene("stop"))
    reply = viewer.handle("/snap", {"label": "stop"})
    assert reply["saved"] is False and reply["counts"]["stop"] == 0


@pytest.mark.parametrize("path,data", [("/snap", {"label": "../../etc"}), ("/snap", {}), ("/set", {"mask": "green"})])
def test_bad_input_is_rejected(tmp_path, path, data):
    with pytest.raises(ValueError):
        viewer_mod.Viewer(str(tmp_path)).handle(path, data)


def test_mask_choice_and_unknown_path(tmp_path):
    viewer = viewer_mod.Viewer(str(tmp_path))
    assert viewer.handle("/set", {"mask": "red"})["mask"] == "red"
    assert viewer.current_mask() == "red"
    assert viewer.handle("/nope", {}) is None


@pytest.mark.parametrize("mask", viewer_mod.MASKS)
def test_render_draws_the_sign_and_stacks_the_mask(mask):
    frame = scene("parking")
    out = viewer_mod.render(frame, sign_features(frame), "PARKING", mask, fps=25.0)
    extra = 0 if mask == "none" else int(240 * 0.6)
    assert out.shape == (240 + extra, 320, 3)
    assert not np.array_equal(out[:240], frame)  # overlay drawn


def test_page_lists_every_sign_folder():
    script = viewer_mod.SignPanel.script
    assert all('"{}"'.format(name) in script for name in viewer_mod.NAMES)


def test_describe_shows_what_decided_the_label():
    assert viewer_mod.describe(None) == "no sign"
    assert viewer_mod.describe(sign_features(scene("stop"))).startswith("red ext ")
    text = viewer_mod.describe(sign_features(scene("left", size=80)))
    assert text.startswith("blue ext 0.") and " bal +" in text
