"""The browser tuner for Module 3: input clamping, save handling, rendering and the JSON endpoint."""
import importlib.util
import json
import os
import urllib.error
import urllib.request

import numpy as np
import pytest

from jetbot_nstru.line import LineConfig
from jetbot_nstru.viz import MjpegServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("line_tuner", os.path.join(ROOT, "notebooks", "solutions", "03_line_tuner.py"))
tuner_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tuner_mod)


def test_values_are_clamped_and_typed():
    cfg = tuner_mod.update_config(LineConfig(), {"roi_top": "0.456", "black_v_max": 999})
    assert cfg.roi_top == 0.46 and cfg.black_v_max == 200 and isinstance(cfg.black_v_max, int)
    assert tuner_mod.update_config(LineConfig(), {"roi_top": -1}).roi_top == 0.30


@pytest.mark.parametrize("data", [{"kp": 1}, {"black_v_max": "dark"}, {"black_v_max": None}])
def test_bad_input_is_rejected(data):
    with pytest.raises((ValueError, TypeError)):
        tuner_mod.update_config(LineConfig(), data)


def test_set_and_save_report_state():
    saved = {}
    tuner = tuner_mod.Tuner(LineConfig(), save=lambda **kw: saved.update(kw))
    assert tuner.handle("/set", {"black_v_max": 70, "mask": "green"}) == {"roi_top": 0.55, "black_v_max": 70, "mask": "green"}
    reply = tuner.handle("/save", {})
    assert reply["saved"] is True and saved == {"roi_top": 0.55, "black_v_max": 70}
    assert tuner.handle("/nope", {}) is None
    with pytest.raises(ValueError):
        tuner.handle("/set", {"mask": "blue"})


def test_save_failure_is_reported_not_raised():
    def read_only(**kw):
        raise OSError(30, "Read-only file system")

    reply = tuner_mod.Tuner(LineConfig(), save=read_only).handle("/save", {})
    assert reply["saved"] is False and "Read-only" in reply["message"]


@pytest.mark.parametrize("mask", tuner_mod.MASKS)
def test_render_stacks_the_chosen_mask_under_the_frame(mask):
    frame = np.full((240, 320, 3), 235, np.uint8)
    frame[:, 150:170] = 20  # black line
    out = tuner_mod.render(frame, LineConfig(), mask, fps=20.0)
    assert out.shape == (240 + 240 - int(240 * 0.55), 320, 3)


def _post(base, path, body):
    request = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(request, timeout=5)


def test_server_serves_custom_page_and_json_posts():
    tuner = tuner_mod.Tuner(LineConfig(), save=lambda **kw: None)
    with MjpegServer(port=0, page=tuner_mod.PAGE, on_post=tuner.handle) as server:
        base = "http://127.0.0.1:{}".format(server.port)
        assert "จูนการหาเส้นดำ".encode("utf-8") in urllib.request.urlopen(base + "/", timeout=5).read()
        assert json.loads(_post(base, "/set", b'{"roi_top": 0.6}').read())["roi_top"] == 0.6
        for path, body, code in (("/set", b"not json", 400), ("/set", b"[1]", 400), ("/set", b'{"kp": 1}', 400),
                                 ("/nope", b"{}", 404)):
            with pytest.raises(urllib.error.HTTPError) as err:
                _post(base, path, body)
            assert err.value.code == code


def test_server_without_on_post_refuses_posts():
    with MjpegServer(port=0) as server:
        with pytest.raises(urllib.error.HTTPError) as err:
            _post("http://127.0.0.1:{}".format(server.port), "/set", b"{}")
    assert err.value.code == 404
