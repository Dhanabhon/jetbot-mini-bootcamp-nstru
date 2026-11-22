"""Debug view: draw what the robot sees and decides, then show it in a notebook or a browser.

Overlays are drawn on the robot so trainees see exactly what the code used.
Written for Python 3.6 (JetPack 4 on Jetson Nano): no dataclasses, no `X | None`.

Notebook (robot standing still, tuning thresholds):
    image = ipywidgets.Image(format="jpeg")
    image.value = encode_jpeg(draw_overlay(frame, state))

Browser (robot driving):
    server = MjpegServer(port=8080).start()   # open http://<robot-ip>:8080
    server.push(draw_overlay(frame, state))   # call every loop; extra frames are dropped
"""
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import List, NamedTuple, Optional, Tuple

import cv2
import numpy as np

from .line import Box
from .signs import Detection

# BGR
LINE_ROI_COLOR = (39, 159, 239)
CENTROID_COLOR = (74, 75, 226)
SIGN_BOX_COLOR = (89, 196, 151)
TEXT_COLOR = (232, 239, 241)
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.4
HUD_ROW_HEIGHT = 16


class VizState(NamedTuple):
    """Everything the overlay can show. Leave a field as None to hide it."""

    fsm_state: str = ""
    line_roi: Optional[Box] = None
    cx: Optional[int] = None  # line centroid x; None while the line is lost
    cy: Optional[int] = None  # row to draw the centroid on; defaults to the ROI middle
    steer: Optional[float] = None
    motor_left: Optional[float] = None
    motor_right: Optional[float] = None
    sign: Optional[Detection] = None
    fps: Optional[float] = None


def hud_lines(state: VizState) -> List[str]:
    """Text rows for the top-left HUD. ASCII only: cv2.putText cannot draw Thai."""
    # TODO(instructor): choose which numbers trainees need on screen while tuning.
    lines = []
    if state.fsm_state:
        lines.append("state: " + state.fsm_state)
    return lines


def draw_overlay(frame: np.ndarray, state: VizState) -> np.ndarray:
    """Return a copy of a BGR frame with ROI, centroid, sign box and HUD drawn on it."""
    out = frame.copy()
    height, width = out.shape[:2]
    center_x = width // 2

    if state.line_roi is not None:
        x, y, roi_w, roi_h = state.line_roi
        cv2.rectangle(out, (x, y), (x + roi_w - 1, y + roi_h - 1), LINE_ROI_COLOR, 2)
        cv2.line(out, (center_x, y), (center_x, y + roi_h - 1), TEXT_COLOR, 1)
        if state.cx is None:
            _label(out, "LINE LOST", (x + 4, y + 14), CENTROID_COLOR)

    if state.cx is not None:
        cy = state.cy if state.cy is not None else _default_cy(state.line_roi, height)
        cv2.line(out, (center_x, cy), (state.cx, cy), CENTROID_COLOR, 2)
        cv2.circle(out, (state.cx, cy), 5, CENTROID_COLOR, -1)
        _label(out, "err {:+d}".format(state.cx - center_x), (state.cx + 8, cy - 8), CENTROID_COLOR)

    if state.sign is not None:
        x, y, box_w, box_h = state.sign.box
        cv2.rectangle(out, (x, y), (x + box_w, y + box_h), SIGN_BOX_COLOR, 2)
        text = "{} {:.2f}".format(state.sign.label, state.sign.confidence)
        _label(out, text, (x, max(HUD_ROW_HEIGHT, y - 4)), SIGN_BOX_COLOR)

    for row, text in enumerate(hud_lines(state)):
        _label(out, text, (6, HUD_ROW_HEIGHT * (row + 1)), TEXT_COLOR)
    return out


def with_mask(overlay: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Stack the threshold mask under the overlay, scaled to the same width."""
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) if mask.ndim == 2 else mask
    width = overlay.shape[1]
    height = max(1, int(round(mask_bgr.shape[0] * width / mask_bgr.shape[1])))
    return np.vstack([overlay, cv2.resize(mask_bgr, (width, height))])


def encode_jpeg(image: np.ndarray, quality: int = 70) -> bytes:
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("JPEG encoding failed for image of shape {}".format(image.shape))
    return buf.tobytes()


def _default_cy(line_roi: Optional[Box], frame_height: int) -> int:
    if line_roi is None:
        return frame_height - 20
    return line_roi[1] + line_roi[3] // 2


def _label(image: np.ndarray, text: str, origin: Tuple[int, int], color) -> None:
    """Draw text on a black box so it stays readable on any floor."""
    (text_w, text_h), baseline = cv2.getTextSize(text, FONT, FONT_SCALE, 1)
    x, y = origin
    cv2.rectangle(image, (x - 2, y - text_h - 2), (x + text_w + 2, y + baseline), (0, 0, 0), -1)
    cv2.putText(image, text, (x, y), FONT, FONT_SCALE, color, 1, cv2.LINE_AA)


_PAGE = b"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JetBot debug view</title>
<body style="margin:0;background:#111;display:flex;justify-content:center">
<img src="/stream" style="max-width:100%;height:auto;image-rendering:pixelated" alt="JetBot camera">
</body>"""


class _ThreadingServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True  # a viewer left open must not keep the kernel alive
    allow_reuse_address = True  # re-running the notebook cell can rebind the port


class MjpegServer:
    """Serve the latest frame as an MJPEG stream, capped at max_fps.

    JPEG encoding is the expensive part on a Jetson Nano, so push() drops frames
    above max_fps instead of slowing the control loop.
    """

    def __init__(self, port: int = 8080, max_fps: float = 10.0, quality: int = 70):
        if max_fps <= 0:
            raise ValueError("max_fps must be positive, got {}".format(max_fps))
        self._min_interval = 1.0 / max_fps
        self._quality = quality
        self._jpeg = None  # type: Optional[bytes]
        self._last_push = float("-inf")
        self._stopped = False
        self._cond = threading.Condition()
        self._httpd = _ThreadingServer(("0.0.0.0", port), _make_handler(self))
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    def start(self) -> "MjpegServer":
        self._thread.start()
        return self

    def stop(self) -> None:
        with self._cond:
            self._stopped = True
            self._cond.notify_all()
        if self._thread.is_alive():  # shutdown() blocks forever if serve_forever never ran
            self._httpd.shutdown()
        self._httpd.server_close()

    def __enter__(self) -> "MjpegServer":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()

    def push(self, image: np.ndarray) -> bool:
        """Offer a frame. Returns True if it was encoded and sent, False if throttled."""
        now = time.monotonic()
        if now - self._last_push < self._min_interval:
            return False
        jpeg = encode_jpeg(image, self._quality)
        with self._cond:
            self._jpeg = jpeg
            self._last_push = now
            self._cond.notify_all()
        return True

    def _wait_frame(self, previous: Optional[bytes], timeout: float = 2.0) -> Optional[bytes]:
        with self._cond:
            self._cond.wait_for(
                lambda: self._stopped or (self._jpeg is not None and self._jpeg is not previous),
                timeout,
            )
            return None if self._stopped else self._jpeg


def _make_handler(server: MjpegServer):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # keep notebook output clean

        def do_GET(self):
            if self.path == "/":
                self._send(200, "text/html; charset=utf-8", _PAGE)
            elif self.path == "/stream":
                self._stream()
            else:
                self.send_error(404)

        def _send(self, code, content_type, body):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _stream(self):
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            previous = None
            try:
                while True:
                    jpeg = server._wait_frame(previous)
                    if jpeg is None:
                        return  # server stopped
                    if jpeg is previous:
                        continue  # timed out with no new frame
                    previous = jpeg
                    header = "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: {}\r\n\r\n"
                    self.wfile.write(header.format(len(jpeg)).encode() + jpeg + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                return  # viewer closed the tab

    return Handler
