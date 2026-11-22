import urllib.request

import numpy as np
import pytest

from jetbot_nstru.viz import Detection, MjpegServer, VizState, draw_overlay, with_mask

FRAME = np.full((240, 320, 3), 180, dtype=np.uint8)
ROI = (0, 160, 320, 80)


def test_draw_overlay_returns_new_frame_and_leaves_input_untouched():
    original = FRAME.copy()
    state = VizState(
        fsm_state="FOLLOW_LINE",
        line_roi=ROI,
        cx=172,
        sign=Detection("LEFT", 0.93, (228, 16, 70, 70)),
    )

    out = draw_overlay(FRAME, state)

    assert out.shape == FRAME.shape
    assert np.array_equal(FRAME, original)
    assert not np.array_equal(out, FRAME)


def test_draw_overlay_handles_lost_line_and_empty_state():
    assert draw_overlay(FRAME, VizState(line_roi=ROI, cx=None)).shape == FRAME.shape
    assert np.array_equal(draw_overlay(FRAME, VizState()), FRAME)


def test_with_mask_stacks_scaled_mask_under_overlay():
    mask = np.zeros((40, 160), dtype=np.uint8)

    out = with_mask(FRAME, mask)

    assert out.shape == (240 + 80, 320, 3)


def test_push_drops_frames_above_max_fps():
    server = MjpegServer(port=0, max_fps=1)
    try:
        assert server.push(FRAME) is True
        assert server.push(FRAME) is False
    finally:
        server.stop()


def test_rejects_non_positive_max_fps():
    with pytest.raises(ValueError):
        MjpegServer(port=0, max_fps=0)


def test_serves_page_and_jpeg_stream():
    noisy = np.random.default_rng(0).integers(0, 256, FRAME.shape, dtype=np.uint8)
    with MjpegServer(port=0) as server:
        server.push(noisy)  # noise keeps one JPEG above the 2048-byte read below
        base = "http://127.0.0.1:{}".format(server.port)

        page = urllib.request.urlopen(base + "/", timeout=5).read()
        stream = urllib.request.urlopen(base + "/stream", timeout=5)
        chunk = stream.read(2048)
        stream.close()

    assert b'src="/stream"' in page
    assert b"--frame" in chunk
    assert b"\xff\xd8" in chunk  # JPEG start-of-image marker
