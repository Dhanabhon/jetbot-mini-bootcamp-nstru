import os

import cv2
import numpy as np
import pytest

from jetbot_nstru import fsm
from jetbot_nstru.fsm import Command, MissionConfig, MissionState, Observation, step
from jetbot_nstru.signs import LABELS, SignVoter, detect_sign

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "signs")


def scene(label, size=40, top=30, left=200, blur=0):
    """Paste a real sticker crop onto a light floor, like a sign seen by the robot camera."""
    frame = np.full((240, 320, 3), 225, dtype=np.uint8)
    sign = cv2.resize(cv2.imread(os.path.join(FIXTURES, label.lower() + ".png")), (size, size),
                      interpolation=cv2.INTER_AREA)
    frame[top : top + size, left : left + size] = sign
    if blur:
        frame = cv2.blur(frame, (blur, 1))  # horizontal motion blur
    return frame


@pytest.mark.parametrize("label", LABELS)
@pytest.mark.parametrize("size", [32, 48, 80])
def test_each_sticker_is_recognised_at_several_distances(label, size):
    detection = detect_sign(scene(label, size=size))

    assert detection is not None
    assert detection.label == label


@pytest.mark.parametrize("label", LABELS)
def test_recognition_survives_mild_motion_blur(label):
    assert detect_sign(scene(label, size=48, blur=5)).label == label


def test_sign_below_search_area_is_ignored():
    assert detect_sign(scene("STOP", size=40, top=180)) is None


def test_empty_frame_has_no_sign():
    assert detect_sign(np.full((240, 320, 3), 225, dtype=np.uint8)) is None


def test_voter_needs_enough_agreeing_frames():
    voter = SignVoter(window=5, min_votes=3)

    assert [voter.update(x) for x in ["LEFT", None, "RIGHT", "LEFT"]] == [None, None, None, None]
    assert voter.update("LEFT") == "LEFT"


def test_voter_rejects_bad_settings():
    with pytest.raises(ValueError):
        SignVoter(window=3, min_votes=4)


CFG = MissionConfig()


def obs(found=True, error=0.0, width=0.1, green=None, sign=None):
    return Observation(found, error, width, green, sign)


def run(state, observation, now):
    return step(state, observation, now, CFG)


def test_left_sign_is_announced_then_executed_at_green_marker():
    state, cmd = run(MissionState(), obs(sign="LEFT"), 0.0)
    assert state.pending == "LEFT"
    assert cmd == Command("follow", display="LEFT", beep=True)

    state, cmd = run(state, obs(green=0.9), 1.0)
    assert state.mode == fsm.CROSS
    assert cmd.kind == "drive" and cmd.left == cmd.right

    state, cmd = run(state, obs(green=0.95), 1.0 + CFG.cross_time)
    assert state.mode == fsm.TURN_LEFT
    assert cmd.left < 0 < cmd.right

    # the old line is still centred, but too early to count as the new one
    state, _ = run(state, obs(error=0.0), 1.0 + CFG.cross_time + 0.1)
    assert state.mode == fsm.TURN_LEFT

    now = 1.0 + CFG.cross_time + CFG.min_turn_time + 0.05
    state, cmd = run(state, obs(error=0.1), now)
    assert state.mode == fsm.FOLLOW
    assert state.pending is None
    assert cmd.kind == "follow"

    # same marker and sign still in view during cooldown: no second action
    state, _ = run(state, obs(green=0.95, sign="LEFT"), now + 0.1)
    assert state.mode == fsm.FOLLOW and state.pending is None


def test_unsigned_green_marker_goes_straight():
    state, _ = run(MissionState(), obs(green=0.9), 0.0)
    state, cmd = run(state, obs(), CFG.cross_time)

    assert state.mode == fsm.FOLLOW
    assert cmd.kind == "follow"


def test_turn_gives_up_after_max_time():
    state = MissionState(mode=fsm.TURN_RIGHT, entered_at=0.0)

    state, cmd = run(state, obs(found=False), CFG.max_turn_time)

    assert state.mode == fsm.FOLLOW


def test_stop_sign_holds_still_then_crosses():
    state, _ = run(MissionState(), obs(sign="STOP"), 0.0)
    state, cmd = run(state, obs(green=0.9), 1.0)
    assert state.mode == fsm.STOP_WAIT
    assert cmd == Command("stop", display="STOP")

    state, cmd = run(state, obs(green=0.9), 1.0 + CFG.stop_time - 0.01)
    assert cmd.kind == "stop"

    state, cmd = run(state, obs(), 1.0 + CFG.stop_time)
    assert state.mode == fsm.CROSS and cmd.kind == "drive"


def test_parking_waits_for_bottom_t_then_stops():
    state, _ = run(MissionState(), obs(sign="PARKING"), 0.0)
    state, _ = run(state, obs(green=0.9), 1.0)
    state, _ = run(state, obs(), 1.0 + CFG.cross_time)
    assert state.mode == fsm.PARK_APPROACH

    # the marker's own cross line is wide, but parking must not trigger on it
    start = state.entered_at
    state, cmd = run(state, obs(width=0.95), start + 0.1)
    assert state.mode == fsm.PARK_APPROACH and cmd.kind == "follow"

    state, cmd = run(state, obs(width=0.95), start + CFG.cooldown)
    assert state.mode == fsm.DONE
    assert cmd == Command("stop", display="PARKED", beep=True)

    assert run(state, obs(), start + 10)[1].kind == "stop"
