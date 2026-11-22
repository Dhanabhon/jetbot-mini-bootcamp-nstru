"""The browser tuner for Module 3: input clamping, save handling, rendering and the JSON endpoint."""
import json
import urllib.error
import urllib.request

import numpy as np
import pytest

from jetbot_nstru.app import line as tuner_mod
from jetbot_nstru.app.core import App, Context, build_page
from jetbot_nstru.line import LineConfig
from jetbot_nstru.viz import MjpegServer


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


def _post(base, path, body, **headers):
    headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(base + path, data=body, headers=headers)
    return urllib.request.urlopen(request, timeout=5)


def test_server_serves_the_app_page_and_json_posts():
    panel = tuner_mod.LinePanel(Context({}, save=lambda **kw: None))
    app = App([panel])
    with MjpegServer(port=0, page=build_page("จูนการหาเส้นดำ", [panel]), on_post=app.handle) as server:
        base = "http://127.0.0.1:{}".format(server.port)
        assert "จูนการหาเส้นดำ".encode("utf-8") in urllib.request.urlopen(base + "/", timeout=5).read()
        assert json.loads(_post(base, "/line/set", b'{"roi_top": 0.6}').read())["roi_top"] == 0.6
        assert panel.ctx.line.roi_top == 0.6  # the other tabs see the new value
        for path, body, code in (("/line/set", b"not json", 400), ("/line/set", b"[1]", 400),
                                 ("/line/set", b'{"kp": 1}', 400), ("/line/nope", b"{}", 404), ("/nope", b"{}", 404)):
            with pytest.raises(urllib.error.HTTPError) as err:
                _post(base, path, body)
            assert err.value.code == code


def test_server_without_on_post_refuses_posts():
    with MjpegServer(port=0) as server:
        with pytest.raises(urllib.error.HTTPError) as err:
            _post("http://127.0.0.1:{}".format(server.port), "/set", b"{}")
    assert err.value.code == 404


def test_server_refuses_posts_a_foreign_page_could_send():
    tuner = tuner_mod.Tuner(LineConfig(), save=lambda **kw: None)
    with MjpegServer(port=0, page=b"<p>tuner</p>", on_post=tuner.handle) as server:
        base = "http://127.0.0.1:{}".format(server.port)
        cases = (({"Content-Type": "text/plain"}, 415),  # a form or sendBeacon from another site
                 ({"Origin": "http://evil.example"}, 403))
        for headers, code in cases:
            with pytest.raises(urllib.error.HTTPError) as err:
                _post(base, "/set", b'{"roi_top": 0.7}', **headers)
            assert err.value.code == code
        same_origin = _post(base, "/set", b'{"roi_top": 0.7}', Origin=base)
        assert json.loads(same_origin.read())["roi_top"] == 0.7


@pytest.mark.parametrize("host,ok", [("10.42.0.1:8080", True), ("127.0.0.1", True), ("[::1]:8080", True),
                                     ("localhost:8080", True), ("evil.example:8080", False), ("", False), (None, False)])
def test_host_allowed_only_names_the_robot_itself(host, ok):
    from jetbot_nstru.viz import host_allowed
    assert host_allowed(host) is ok


def test_server_refuses_a_rebound_domain_on_every_request():
    tuner = tuner_mod.Tuner(LineConfig(), save=lambda **kw: None)
    with MjpegServer(port=0, page=b"<p>tuner</p>", on_post=tuner.handle) as server:
        base = "http://127.0.0.1:{}".format(server.port)
        rebound = {"Host": "evil.example:{}".format(server.port), "Origin": "http://evil.example:{}".format(server.port)}
        for request in (urllib.request.Request(base + "/", headers=rebound),
                        urllib.request.Request(base + "/set", data=b'{"roi_top": 0.7}',
                                               headers=dict(rebound, **{"Content-Type": "application/json"}))):
            with pytest.raises(urllib.error.HTTPError) as err:
                urllib.request.urlopen(request, timeout=5)
            assert err.value.code == 403
        assert tuner.handle("/set", {})["roi_top"] == 0.55  # the rebound POST changed nothing
