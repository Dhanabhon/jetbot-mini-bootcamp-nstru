"""Line detection (Module 3): ROI, black-line mask, centroid and the green intersection marker.

All coordinates returned are in full-frame pixels so they can be drawn straight onto the frame.
"""
from typing import NamedTuple, Optional, Tuple

import cv2
import numpy as np

Box = Tuple[int, int, int, int]  # x, y, w, h


class LineConfig(NamedTuple):
    roi_top: float = 0.55  # ROI starts at this fraction of frame height; above it is far floor and signs
    black_v_max: int = 90  # HSV value below this counts as black line
    use_adaptive: bool = False  # adaptive threshold copes with uneven light but breaks up wide blobs
    adaptive_block: int = 31  # must be odd
    adaptive_c: int = 10
    min_line_area: int = 150  # px; smaller blobs are noise or dirt
    green_lower: Tuple[int, int, int] = (35, 80, 50)
    green_upper: Tuple[int, int, int] = (90, 255, 255)
    min_green_area: int = 400


class LineResult(NamedTuple):
    found: bool
    cx: Optional[int]  # line centroid x; None when no line
    cy: Optional[int]
    error: float  # (cx - centre) / half width, in -1..1; 0 when no line
    width_ratio: float  # line blob width / ROI width; near 1 means a horizontal line (T junction)
    green_box: Optional[Box]
    roi_box: Box
    mask: np.ndarray  # ROI-sized binary mask of the line


def roi_box(frame_shape: Tuple[int, ...], cfg: LineConfig) -> Box:
    height, width = frame_shape[:2]
    top = int(height * cfg.roi_top)
    return 0, top, width, height - top


def line_mask(roi_bgr: np.ndarray, cfg: LineConfig) -> np.ndarray:
    """255 where the black line is, 0 elsewhere."""
    if cfg.use_adaptive:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        mask = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, cfg.adaptive_block, cfg.adaptive_c
        )
    else:
        value = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)[:, :, 2]
        mask = np.where(value < cfg.black_v_max, 255, 0).astype(np.uint8)
    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


def green_mask(roi_bgr: np.ndarray, cfg: LineConfig) -> np.ndarray:
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, np.array(cfg.green_lower), np.array(cfg.green_upper))


def largest_contour(mask: np.ndarray, min_area: float):
    """Largest external contour with at least min_area pixels, or None."""
    found = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = found[-2]  # OpenCV 3 returns 3 values, OpenCV 4 returns 2
    big = [c for c in contours if cv2.contourArea(c) >= min_area]
    return max(big, key=cv2.contourArea) if big else None


def detect_line(frame: np.ndarray, cfg: LineConfig = LineConfig()) -> LineResult:
    box = roi_box(frame.shape, cfg)
    x0, y0, width, height = box
    roi = frame[y0 : y0 + height, x0 : x0 + width]
    mask = line_mask(roi, cfg)
    green = largest_contour(green_mask(roi, cfg), cfg.min_green_area)
    green_box = None
    if green is not None:
        gx, gy, gw, gh = cv2.boundingRect(green)
        green_box = (gx + x0, gy + y0, gw, gh)

    line = largest_contour(mask, cfg.min_line_area)
    if line is None:
        return LineResult(False, None, None, 0.0, 0.0, green_box, box, mask)

    moments = cv2.moments(line)
    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])
    half = width / 2.0
    error = max(-1.0, min(1.0, (cx - half) / half))
    width_ratio = cv2.boundingRect(line)[2] / float(width)
    return LineResult(True, cx + x0, cy + y0, error, width_ratio, green_box, box, mask)
