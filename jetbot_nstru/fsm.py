"""Mission state machine (Module 6): pre-fetch the sign, act on the green marker.

step() is a pure function: same state + observation + time in, same new state + command out.
That makes it testable without a robot, and the notebook loop stays a thin shell around it:

    state = MissionState()
    while state.mode != DONE:
        obs = observe(frame)                      # from detect_line + SignVoter
        state, cmd = step(state, obs, time.monotonic())
        apply(cmd)                                # PID for "follow", raw motors otherwise
"""
from typing import NamedTuple, Optional, Tuple

from .signs import LEFT, PARKING, RIGHT, STOP, STRAIGHT

FOLLOW = "FOLLOW"
CROSS = "CROSS"
TURN_LEFT = "TURN_LEFT"
TURN_RIGHT = "TURN_RIGHT"
STOP_WAIT = "STOP_WAIT"
PARK_APPROACH = "PARK_APPROACH"
DONE = "DONE"


class MissionConfig(NamedTuple):
    green_trigger: float = 0.85  # act when the green box bottom passes this fraction of frame height
    cross_time: float = 0.35  # s; drive straight onto the intersection before turning
    cross_speed: float = 0.35
    turn_speed: float = 0.35
    min_turn_time: float = 0.35  # s; ignore the line we are turning away from
    max_turn_time: float = 2.0  # s; give up and follow whatever line is visible
    turn_done_error: float = 0.3  # |error| below this after min_turn_time = new line found
    stop_time: float = 3.2  # s; rules need 3 s with wheels still, keep a margin
    cooldown: float = 1.0  # s after an action where green markers and signs are ignored
    park_width: float = 0.7  # line wider than this share of the ROI = bottom T junction


class Observation(NamedTuple):
    line_found: bool
    error: float  # normalised line error, -1..1
    width_ratio: float  # LineResult.width_ratio
    green_bottom: Optional[float]  # green box bottom / frame height, None when not visible
    sign: Optional[str]  # label confirmed by SignVoter, None when nothing confirmed


class MissionState(NamedTuple):
    mode: str = FOLLOW
    pending: Optional[str] = None  # sign read ahead of the next green marker
    after_cross: Optional[str] = None  # what CROSS hands over to: LEFT, RIGHT, PARKING or None
    entered_at: float = 0.0  # time the current mode started
    ignore_until: float = 0.0


class Command(NamedTuple):
    kind: str  # "follow" (caller runs PID), "drive" (use left/right as given) or "stop"
    left: float = 0.0
    right: float = 0.0
    display: Optional[str] = None  # new OLED text, None = leave the screen as it is
    beep: bool = False


def _enter(state: MissionState, mode: str, now: float, **changes) -> MissionState:
    return state._replace(mode=mode, entered_at=now, **changes)


def _finish_action(state: MissionState, now: float, cfg: MissionConfig) -> MissionState:
    return _enter(state, FOLLOW, now, pending=None, after_cross=None, ignore_until=now + cfg.cooldown)


def _follow(state: MissionState, obs: Observation, now: float,
            cfg: MissionConfig) -> Tuple[MissionState, Command]:
    if now < state.ignore_until:
        return state, Command("follow")

    if obs.green_bottom is not None and obs.green_bottom >= cfg.green_trigger:
        action = state.pending or STRAIGHT  # unsigned green marker: always straight on
        if action == STOP:
            return _enter(state, STOP_WAIT, now), Command("stop", display=STOP)
        after = action if action in (LEFT, RIGHT, PARKING) else None
        return (_enter(state, CROSS, now, after_cross=after),
                Command("drive", cfg.cross_speed, cfg.cross_speed))

    if obs.sign is not None and obs.sign != state.pending:
        # announcing the sign before acting on it earns the OLED bonus
        return state._replace(pending=obs.sign), Command("follow", display=obs.sign, beep=True)
    return state, Command("follow")


def _turn(state: MissionState, obs: Observation, now: float,
          cfg: MissionConfig) -> Tuple[MissionState, Command]:
    elapsed = now - state.entered_at
    reacquired = elapsed >= cfg.min_turn_time and obs.line_found and abs(obs.error) < cfg.turn_done_error
    if reacquired or elapsed >= cfg.max_turn_time:
        return _finish_action(state, now, cfg), Command("follow")
    speed = cfg.turn_speed
    if state.mode == TURN_LEFT:
        return state, Command("drive", -speed, speed)
    return state, Command("drive", speed, -speed)


def step(state: MissionState, obs: Observation, now: float,
         cfg: MissionConfig = MissionConfig()) -> Tuple[MissionState, Command]:
    if state.mode == FOLLOW:
        return _follow(state, obs, now, cfg)

    if state.mode == STOP_WAIT:
        if now - state.entered_at < cfg.stop_time:
            return state, Command("stop")
        return (_enter(state, CROSS, now, after_cross=None),
                Command("drive", cfg.cross_speed, cfg.cross_speed))

    if state.mode == CROSS:
        if now - state.entered_at < cfg.cross_time:
            return state, Command("drive", cfg.cross_speed, cfg.cross_speed)
        if state.after_cross == LEFT:
            return _enter(state, TURN_LEFT, now), Command("drive", -cfg.turn_speed, cfg.turn_speed)
        if state.after_cross == RIGHT:
            return _enter(state, TURN_RIGHT, now), Command("drive", cfg.turn_speed, -cfg.turn_speed)
        if state.after_cross == PARKING:
            return _enter(state, PARK_APPROACH, now, pending=None, after_cross=None), Command("follow")
        return _finish_action(state, now, cfg), Command("follow")

    if state.mode in (TURN_LEFT, TURN_RIGHT):
        return _turn(state, obs, now, cfg)

    if state.mode == PARK_APPROACH:
        # the marker's own cross line is still in view right after CROSS, so wait before looking for the T
        settled = now - state.entered_at >= cfg.cooldown
        if settled and (not obs.line_found or obs.width_ratio >= cfg.park_width):
            return _enter(state, DONE, now), Command("stop", display="PARKED", beep=True)
        return state, Command("follow")

    return state, Command("stop")  # DONE, or an unknown mode: never drive blind
