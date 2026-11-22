"""Traffic sign recognition with colour and shape (Module 5).

The five sticker signs in stickers/ are told apart like this:
  red blob                      -> STOP (the only red sign)
  blue blob, square (extent~1)  -> PARKING
  blue blob, round (extent~.78) -> arrow; white pixels in the top half lean towards the arrow head
"""
from collections import Counter, deque
from typing import NamedTuple, Optional, Tuple

import cv2
import numpy as np

from .line import Box, largest_contour

LEFT, RIGHT, STRAIGHT, STOP, PARKING = "LEFT", "RIGHT", "STRAIGHT", "STOP", "PARKING"
LABELS = (LEFT, RIGHT, STRAIGHT, STOP, PARKING)


class SignConfig(NamedTuple):
    search_bottom: float = 0.6  # only search above this fraction of frame height; signs stand above the floor
    blue_lower: Tuple[int, int, int] = (100, 120, 50)
    blue_upper: Tuple[int, int, int] = (130, 255, 255)
    red_lower1: Tuple[int, int, int] = (0, 120, 70)  # red wraps around hue 0, so it needs two ranges
    red_upper1: Tuple[int, int, int] = (10, 255, 255)
    red_lower2: Tuple[int, int, int] = (170, 120, 70)
    red_upper2: Tuple[int, int, int] = (180, 255, 255)
    white_s_max: int = 70
    white_v_min: int = 150
    min_area: int = 250  # px; about a 18x18 sign, i.e. still far away
    max_aspect: float = 1.5  # w/h or h/w; rejects long blobs like a blue table edge
    square_extent: float = 0.9  # contour area / box area above this = square sign
    turn_balance: float = 0.15  # top-half white balance beyond this = turn arrow


class Detection(NamedTuple):
    label: str
    confidence: float  # 0..1, how clearly the deciding feature passed its threshold
    box: Box


def colour_masks(hsv: np.ndarray, cfg: SignConfig) -> Tuple[np.ndarray, np.ndarray]:
    blue = cv2.inRange(hsv, np.array(cfg.blue_lower), np.array(cfg.blue_upper))
    red = cv2.inRange(hsv, np.array(cfg.red_lower1), np.array(cfg.red_upper1)) | cv2.inRange(
        hsv, np.array(cfg.red_lower2), np.array(cfg.red_upper2)
    )
    kernel = np.ones((5, 5), np.uint8)
    return (cv2.morphologyEx(blue, cv2.MORPH_CLOSE, kernel), cv2.morphologyEx(red, cv2.MORPH_CLOSE, kernel))


def arrow_balance(hsv_crop: np.ndarray, contour_in_crop, cfg: SignConfig) -> float:
    """(left - right) / total of white pixels in the top half of the sign.

    > 0 means the arrow head is on the left. Eroding the sign shape first drops the white rim.
    """
    height, width = hsv_crop.shape[:2]
    shape = np.zeros((height, width), np.uint8)
    cv2.drawContours(shape, [contour_in_crop], -1, 1, -1)
    inner = cv2.erode(shape, np.ones((3, 3), np.uint8), iterations=max(1, int(0.12 * width)))
    white = (hsv_crop[:, :, 1] < cfg.white_s_max) & (hsv_crop[:, :, 2] > cfg.white_v_min) & (inner > 0)
    top = white[: height // 2]
    left = int(top[:, : width // 2].sum())
    right = int(top[:, width // 2 :].sum())
    return (left - right) / float(max(1, left + right))


def _plausible(contour, cfg: SignConfig) -> bool:
    _, _, w, h = cv2.boundingRect(contour)
    return max(w, h) / float(max(1, min(w, h))) <= cfg.max_aspect


def detect_sign(frame: np.ndarray, cfg: SignConfig = SignConfig()) -> Optional[Detection]:
    """Biggest sign in the upper part of the frame, or None."""
    search = frame[: int(frame.shape[0] * cfg.search_bottom)]
    hsv = cv2.cvtColor(search, cv2.COLOR_BGR2HSV)
    blue, red = colour_masks(hsv, cfg)
    candidates = []
    for colour, mask in (("blue", blue), ("red", red)):
        contour = largest_contour(mask, cfg.min_area)
        if contour is not None and _plausible(contour, cfg):
            candidates.append((cv2.contourArea(contour), colour, contour))
    if not candidates:
        return None

    _, colour, contour = max(candidates, key=lambda item: item[0])
    x, y, w, h = cv2.boundingRect(contour)
    box = (x, y, w, h)
    if colour == "red":
        return Detection(STOP, 1.0, box)

    extent = cv2.contourArea(contour) / float(w * h)
    if extent >= cfg.square_extent:
        return Detection(PARKING, min(1.0, (extent - 0.78) / (cfg.square_extent - 0.78)), box)

    balance = arrow_balance(hsv[y : y + h, x : x + w], contour - [x, y], cfg)
    confidence = min(1.0, abs(balance) / (2 * cfg.turn_balance))
    if balance > cfg.turn_balance:
        return Detection(LEFT, confidence, box)
    if balance < -cfg.turn_balance:
        return Detection(RIGHT, confidence, box)
    return Detection(STRAIGHT, 1.0 - confidence, box)


class SignVoter:
    """Majority vote over the last few frames so one blurred frame cannot change the plan."""

    def __init__(self, window: int = 7, min_votes: int = 4):
        if not 0 < min_votes <= window:
            raise ValueError("need 0 < min_votes <= window, got {} and {}".format(min_votes, window))
        self.min_votes = min_votes
        self._recent = deque(maxlen=window)

    def update(self, label: Optional[str]) -> Optional[str]:
        """Add this frame's label (None = no sign) and return the confirmed label, if any."""
        self._recent.append(label)
        counts = Counter(item for item in self._recent if item is not None)
        if not counts:
            return None
        best, votes = counts.most_common(1)[0]
        return best if votes >= self.min_votes else None

    def reset(self) -> None:
        self._recent.clear()
