# %% [markdown]
# # Module 6: State Machine & Mission Integration
#
# **เวลา:** 14:00 – 14:45 น.
#
# ## เป้าหมาย
#
# - รวมการเดินตามเส้น (Module 4) กับการอ่านป้าย (Module 5) ด้วย Finite State Machine (FSM)
# - **Pre-fetch Sign:** อ่านป้ายล่วงหน้าแล้วจำไว้ แต่ยังไม่ทำ
# - **Green Node Trigger:** ลงมือทำตามป้ายเมื่อเห็นสี่เหลี่ยมเขียวที่ขอบล่างของภาพ
# - แสดงชื่อป้ายบน OLED และส่งเสียง Buzzer ทันทีที่อ่านได้ (ได้โบนัส −2 วินาทีต่อป้าย)
#
# ## ทำไมต้องแยกเป็น 2 จังหวะ
#
# กล้องมองไปข้างหน้า ป้ายจึงเข้าเฟรมก่อนรถถึงจุดตัดหลายสิบ ซม. ถ้าเลี้ยวทันทีที่เห็นป้าย รถจะเลี้ยวก่อนถึงจุดตัด
# เราจึงจำป้ายไว้ใน `pending` แล้วรอจนสี่เหลี่ยมเขียวเลื่อนลงมาถึงขอบล่างของภาพ (`green_trigger`) จึงลงมือ
#
# ## States
#
# ```text
#                  เห็นป้าย: จำไว้ใน pending, โชว์ OLED, beep
#                 ┌──────┐
#                 ▼      │
#   START ──▶ FOLLOW ────┘
#               │ เขียวถึงขอบล่าง
#               ├── pending = STOP ─────▶ STOP_WAIT (หยุด 3 วินาที) ──▶ CROSS
#               └── อื่น ๆ ──────────────▶ CROSS (วิ่งตรงขึ้นไปกลางจุดตัด)
#                                            ├── LEFT / RIGHT ──▶ TURN_LEFT / TURN_RIGHT ──เจอเส้นใหม่──▶ FOLLOW
#                                            ├── PARKING ───────▶ PARK_APPROACH ──เจอตัว T──▶ DONE
#                                            └── ตรงไป ─────────▶ FOLLOW
# ```
#
# หลังทำตามป้ายเสร็จ FSM จะไม่สนสี่เหลี่ยมเขียวและป้ายช่วงสั้น ๆ (`cooldown`) เพราะจุดตัดเดิมและป้ายเดิมยังอยู่ในภาพ
# จุดตัดเขียวที่ไม่มีป้าย FSM จะวิ่งตรงไปเสมอตามกติกา
#
# โค้ด FSM อยู่ใน `jetbot_nstru/fsm.py` ฟังก์ชัน `step(state, observation, now)` เป็น pure function:
# รับสถานะเดิมกับสิ่งที่เห็น แล้วคืนสถานะใหม่กับคำสั่ง (`Command`) โดยไม่สั่งมอเตอร์เอง
# งานของเราใน module นี้คือเขียนส่วนที่ต่อ FSM เข้ากับกล้องและมอเตอร์

# %% [setup]

# %%
import time

from jetbot_nstru import fsm
from jetbot_nstru.fsm import Command, MissionConfig, MissionState, Observation, step
from jetbot_nstru.line import LineConfig, detect_line
from jetbot_nstru.params import load_params
from jetbot_nstru.pid import PID, MotorTrim, mix_motors, speed_for_error
from jetbot_nstru.signs import SignConfig, SignVoter, detect_sign

params = load_params()
trim = MotorTrim(params.get("left_gain", 1.0), params.get("right_gain", 1.0))
line_cfg = LineConfig(roi_top=params.get("roi_top", 0.55), black_v_max=params.get("black_v_max", 90))
sign_cfg = SignConfig()
mission_cfg = MissionConfig()
print(params)

# %% [markdown]
# ## 1. ลองเดิน FSM บนกระดาษก่อน (ไม่ต้องใช้รถ)
#
# เราป้อน observation ปลอมทีละเฟรม พร้อมเวลา แล้วดูว่า FSM เปลี่ยน state อย่างไร
# ลองแก้ลำดับเหตุการณ์ เช่น เปลี่ยน `"LEFT"` เป็น `"STOP"` หรือเอาป้ายออก แล้วทำนายผลก่อนรัน

# %%
def fake(found=True, error=0.0, width=0.1, green=None, sign=None):
    return Observation(found, error, width, green, sign)


script = [
    (0.0, fake()),
    (0.5, fake(sign="LEFT")),  # อ่านป้ายได้
    (1.0, fake(green=0.6)),  # เห็นเขียว แต่ยังไกล
    (1.5, fake(green=0.9)),  # เขียวถึงขอบล่าง
    (1.9, fake(green=0.95)),  # ข้ามจุดตัดเสร็จ
    (2.1, fake(error=0.0)),  # ยังเห็นเส้นเดิม แต่เร็วเกินไปที่จะถือว่าเลี้ยวเสร็จ
    (2.4, fake(error=0.8)),  # กำลังหมุน เส้นใหม่เข้ามาด้านข้าง
    (2.6, fake(error=0.1)),  # เส้นใหม่อยู่กลางภาพ
    (2.8, fake(green=0.95, sign="LEFT")),  # จุดตัดเดิมยังอยู่ในภาพ: ต้องไม่ทำซ้ำ
]
state = MissionState()
for now, observation in script:
    state, command = step(state, observation, now, mission_cfg)
    print("{:4.1f}s  {:14s} pending={!s:8s} {}".format(now, state.mode, state.pending, command))

# %% [markdown]
# ## 2. แปลงภาพเป็น Observation
#
# **TODO:** เขียน `observe(frame)` คืน `(Observation, line_result, sign)`:
#
# - `line_result = detect_line(frame, line_cfg)`
# - `sign = detect_sign(frame, sign_cfg)` แล้วส่ง `sign.label` (หรือ `None`) เข้า `voter.update(...)` ได้ป้ายที่ยืนยันแล้ว
# - `green_bottom` = ขอบล่างของกล่องเขียว (`y + h`) หารด้วยความสูงภาพ หรือ `None` ถ้าไม่เห็นเขียว

# %%
voter = SignVoter(window=7, min_votes=4)


def observe(frame):
    # BEGIN SOLUTION: เรียก detect_line, detect_sign, voter.update แล้วสร้าง Observation(found, error, width_ratio, green_bottom, confirmed)
    line_result = detect_line(frame, line_cfg)
    sign = detect_sign(frame, sign_cfg)
    confirmed = voter.update(sign.label if sign else None)
    green_bottom = None
    if line_result.green_box is not None:
        _, y, _, h = line_result.green_box
        green_bottom = (y + h) / float(frame.shape[0])
    observation = Observation(line_result.found, line_result.error, line_result.width_ratio, green_bottom, confirmed)
    return observation, line_result, sign
    # END SOLUTION


import numpy as np

test_frame = np.full((240, 320, 3), 235, np.uint8)
test_frame[:, 150:170] = 20
test_frame[200:236, 140:180] = (60, 170, 40)
test_obs, _, _ = observe(test_frame)
assert test_obs.line_found and test_obs.sign is None
assert abs(test_obs.green_bottom - 236 / 240.0) < 1e-6

# %% [markdown]
# ## 3. ทำตามคำสั่งของ FSM
#
# **TODO:** เขียน `apply(command, steer, speed)` ให้รถทำตาม `Command`:
#
# | `command.kind` | ทำอะไร |
# | :--- | :--- |
# | `"follow"` | `robot.set_motors(*mix_motors(speed, steer, trim))` (เดินตามเส้นด้วย PID) |
# | `"drive"` | สั่งล้อตรง ๆ: `command.left * trim.left_gain`, `command.right * trim.right_gain` (ใช้ตอนข้ามจุดตัดและหมุนตัว) |
# | `"stop"` | `robot.stop()` |
#
# และถ้า `command.display` ไม่ใช่ `None` ให้ `oled.show(command.display)`, ถ้า `command.beep` ให้ `beep(robot)`

# %%
!sudo systemctl stop jetbotmini_stats

from jetbot_nstru.hardware import CsiCamera, Oled, beep, open_robot

robot = open_robot()
oled = Oled()


def apply(command, steer, speed):
    # BEGIN SOLUTION: แยกตาม command.kind แล้วจัดการ display / beep ท้ายฟังก์ชัน
    if command.kind == "follow":
        robot.set_motors(*mix_motors(speed, steer, trim))
    elif command.kind == "drive":
        robot.set_motors(command.left * trim.left_gain, command.right * trim.right_gain)
    else:
        robot.stop()
    if command.display is not None:
        oled.show(command.display)
    if command.beep:
        beep(robot)
    # END SOLUTION


apply(Command("stop", display="READY"), 0.0, 0.0)

# %% [markdown]
# ## 4. วิ่งภารกิจบนสนามซ้อม
#
# วางรถที่ START แล้วรัน ระหว่างวิ่งเปิด `http://<IP>:8080` ดูว่า FSM อยู่ state ไหน
# ถ้ารถหลุดหรือทำผิด กด ■ (Interrupt) รถจะหยุดเพราะ `finally`
#
# จูนใน `MissionConfig` ถ้า:
#
# | อาการ | ค่าที่ปรับ |
# | :--- | :--- |
# | เลี้ยวเร็วไป ล้อยังไม่ถึงกลางจุดตัด | เพิ่ม `cross_time` หรือ `green_trigger` |
# | เลี้ยวเลยเส้นใหม่ไป | ลด `turn_speed` หรือเพิ่ม `turn_done_error` |
# | เลี้ยวแล้วไปจับเส้นเดิม | เพิ่ม `min_turn_time` |
# | เลี้ยวซ้ำที่จุดตัดเดิม | เพิ่ม `cooldown` |

# %%
from jetbot_nstru.viz import MjpegServer, VizState, draw_overlay

KP = params.get("kp", 0.6)
KD = params.get("kd", 0.05)
MAX_SPEED = params.get("max_speed", 0.45)
MIN_SPEED = params.get("min_speed", 0.25)
TIME_LIMIT = 90.0  # กติกา: รอบละ 90 วินาที

camera = CsiCamera(width=320, height=240, lock_exposure=True)
server = MjpegServer(port=8080, max_fps=10).start()


def run_mission():
    pid = PID(kp=KP, kd=KD)
    voter.reset()
    state = MissionState()
    steer = 0.0
    start = last = time.monotonic()
    try:
        while state.mode != fsm.DONE and time.monotonic() - start < TIME_LIMIT:
            frame = camera.read()
            now = time.monotonic()
            dt, last = max(now - last, 1e-3), now

            observation, line_result, sign = observe(frame)
            state, command = step(state, observation, now, mission_cfg)
            if state.mode != fsm.FOLLOW and state.mode != fsm.PARK_APPROACH:
                pid.reset()  # ไม่ให้ error ช่วงหมุนตัวค้างอยู่ใน PID
            elif line_result.found:
                steer = pid.update(line_result.error, dt)
            apply(command, steer, speed_for_error(observation.error, MAX_SPEED, MIN_SPEED))

            server.push(draw_overlay(frame, VizState(fsm_state=state.mode, line_roi=line_result.roi_box,
                                                     cx=line_result.cx, cy=line_result.cy, sign=sign)))
    finally:
        robot.stop()
    print("จบใน {:.1f} วินาที state สุดท้าย {}".format(time.monotonic() - start, state.mode))


run_mission()

# %%
server.stop()
camera.release()
robot.stop()

# %% [markdown]
# ## สรุป
#
# - [ ] อธิบายได้ว่าทำไมต้องจำป้ายไว้ก่อน แล้วค่อยเลี้ยวตอนเห็นเขียว
# - [ ] `observe` และ `apply` ผ่าน assert
# - [ ] OLED แสดงชื่อป้ายทันทีที่อ่านได้ และมีเสียง beep
# - [ ] รถเลี้ยวซ้าย ขวา ตรง และหยุดที่ STOP ได้ถูกบนสนามซ้อม
#
# ถ้าตามไม่ทัน เปิดเฉลยใน `solutions/` แล้วไปต่อ module ถัดไปได้เลย
