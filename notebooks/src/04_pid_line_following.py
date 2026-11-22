# %% [markdown]
# # Module 4: PID Control Tuning for Speed
#
# **เวลา:** 11:15 – 12:00 น.
#
# ## เป้าหมาย
#
# - เขียน PID Controller แปลง error ของเส้นเป็นค่าเลี้ยว (`steer`)
# - Dynamic Speed: ทางตรงเร่งเต็มที่ เข้าโค้งชะลอเอง
# - ดูการตัดสินใจของรถแบบ real-time ผ่าน browser แล้วจูน `Kp`, `Kd` จนวิ่งรอบสนามซ้อมได้เร็วและนิ่ง
#
# ```text
# error ──▶ PID ──▶ steer ──▶ mix_motors(speed, steer) ──▶ left, right ──▶ robot.set_motors
#   ▲                                                                          │
#   └──────────────────── detect_line(กล้อง) ◀──── รถเคลื่อนที่ ◀────────────────┘
# ```
#
# | เทอม | ทำอะไร | ถ้ามากไป |
# | :--- | :--- | :--- |
# | `Kp * error` | เลี้ยวแรงตามระยะที่เส้นห่างจากกลางภาพ | รถส่ายซ้ายขวา |
# | `Kd * (error - error_ก่อนหน้า) / dt` | เบรกการเลี้ยวเมื่อ error กำลังลดลงเร็ว ช่วยลดการส่าย | กระตุกตาม noise ของภาพ |
# | `Ki * ผลรวม error * dt` | แก้ error ที่ค้างนาน ๆ | แกว่งช้า ๆ และ overshoot (งานนี้มักตั้งเป็น 0) |

# %% [setup]

# %%
import time

import ipywidgets as widgets
from IPython.display import display

from jetbot_nstru.hardware import CsiCamera, open_robot
from jetbot_nstru.line import LineConfig, detect_line
from jetbot_nstru.params import load_params, save_params
from jetbot_nstru.pid import MotorTrim, clamp, mix_motors
from jetbot_nstru.viz import MjpegServer, VizState, draw_overlay

params = load_params()
trim = MotorTrim(params.get("left_gain", 1.0), params.get("right_gain", 1.0))
line_cfg = LineConfig(roi_top=params.get("roi_top", 0.55), black_v_max=params.get("black_v_max", 90))
print("โหลดค่าจาก Module 2-3:", trim, line_cfg.roi_top, line_cfg.black_v_max)

robot = open_robot()
camera = CsiCamera(width=320, height=240, lock_exposure=True)

# %% [markdown]
# ## 1. เขียน PID Controller
#
# **TODO:** เติม `update()` ให้คืน `kp*error + ki*integral + kd*derivative` โดย
#
# - `integral` สะสม `error * dt` และจำกัดไม่ให้เกิน ±`integral_limit` (กัน integral windup)
# - ครั้งแรกที่เรียก ยังไม่มี error ก่อนหน้า ให้ `derivative = 0` ไม่อย่างนั้นจะได้ค่ากระโดด
# - ผลลัพธ์จำกัดให้อยู่ใน ±`output_limit`
#
# ใช้ `clamp(value, low, high)` ที่ import มาแล้วได้

# %%
class MyPID:
    def __init__(self, kp, ki=0.0, kd=0.0, output_limit=1.0, integral_limit=1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.output_limit = output_limit
        self.integral_limit = integral_limit
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.previous_error = None

    def update(self, error, dt):
        # BEGIN SOLUTION: อัปเดต self.integral, คำนวณ derivative จาก self.previous_error, เก็บ error ไว้ แล้วคืนผลรวมที่ clamp แล้ว
        self.integral = clamp(self.integral + error * dt, -self.integral_limit, self.integral_limit)
        derivative = 0.0 if self.previous_error is None else (error - self.previous_error) / dt
        self.previous_error = error
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        return clamp(output, -self.output_limit, self.output_limit)
        # END SOLUTION


pid = MyPID(kp=0.5, kd=0.1)
assert abs(pid.update(0.4, 0.05) - 0.2) < 1e-9  # ครั้งแรก มีแต่ P
assert abs(pid.update(0.5, 0.05) - (0.25 + 0.1 * 2.0)) < 1e-9  # P + D
assert MyPID(kp=10).update(1.0, 0.05) == 1.0  # ถูก clamp

# %% [markdown]
# ## 2. Dynamic Speed
#
# **TODO:** เขียน `choose_speed(error)` ให้ความเร็วเป็น `MAX_SPEED` เมื่อ error = 0 แล้วลดลงแบบเส้นตรงจนเหลือ
# `MIN_SPEED` เมื่อ |error| ≥ 1

# %%
MAX_SPEED = 0.45
MIN_SPEED = 0.25


def choose_speed(error):
    # BEGIN SOLUTION: MAX_SPEED - (MAX_SPEED - MIN_SPEED) * min(1, abs(error))
    return MAX_SPEED - (MAX_SPEED - MIN_SPEED) * min(1.0, abs(error))
    # END SOLUTION


assert choose_speed(0) == MAX_SPEED
assert abs(choose_speed(-0.5) - (MAX_SPEED + MIN_SPEED) / 2) < 1e-9
assert choose_speed(3) == MIN_SPEED

# %% [markdown]
# ## 3. ดูภาพแบบ real-time บนเครื่องตัวเอง
#
# รัน cell นี้ครั้งเดียว แล้วเปิดลิงก์ที่พิมพ์ออกมาในแท็บใหม่ของ Chrome ระหว่างรถวิ่ง หน้านั้นจะแสดง:
#
# - กรอบสีส้ม = ROI, เส้นประกลาง = กลางภาพ
# - จุดแดง = centroid ของเส้น พร้อมค่า `err` เป็น pixel
# - mask ขาวดำต่อท้ายด้านล่าง
#
# ภาพส่งแค่ 10 เฟรมต่อวินาทีเพื่อไม่ให้ loop ควบคุมรถช้าลง และช้ากว่าความจริงราว 0.1–0.2 วินาที
# อย่าจูน PID ตามความหน่วงของจอ ให้ดูรถจริงเป็นหลัก

# %%
from jetbot_nstru.viz import with_mask

server = MjpegServer(port=8080, max_fps=10).start()
ip = !hostname -I
print("เปิด http://{}:8080".format(ip[0].split()[0]))

# %% [markdown]
# ## 4. Loop เดินตามเส้น
#
# ถ้าเส้นหลุดจากภาพ เราใช้ `steer` ค่าล่าสุดต่อ รถจะเลี้ยวกลับไปทางที่เห็นเส้นครั้งสุดท้าย

# %%
def follow_line(pid, seconds=20.0):
    pid.reset()
    steer = 0.0
    last = time.monotonic()
    start = last
    frames = 0
    try:
        while time.monotonic() - start < seconds:
            frame = camera.read()
            now = time.monotonic()
            dt = max(now - last, 1e-3)
            last = now

            result = detect_line(frame, line_cfg)
            if result.found:
                steer = pid.update(result.error, dt)
                speed = choose_speed(result.error)
            else:
                speed = MIN_SPEED
            left, right = mix_motors(speed, steer, trim)
            robot.set_motors(left, right)

            frames += 1
            state = VizState(line_roi=result.roi_box, cx=result.cx, cy=result.cy, steer=steer,
                             motor_left=left, motor_right=right, fps=frames / max(now - start, 1e-3))
            server.push(with_mask(draw_overlay(frame, state), result.mask))
    finally:
        robot.stop()
    print("loop {:.1f} FPS".format(frames / (time.monotonic() - start)))


follow_line(MyPID(kp=0.6, kd=0.05), seconds=10)

# %% [markdown]
# ## 5. จูน PID
#
# จูนทีละค่า เริ่มจาก `Kd = 0`:
#
# 1. เพิ่ม `Kp` ทีละ 0.1 จนรถเข้าโค้งทัน แต่เริ่มส่ายบนทางตรง
# 2. เพิ่ม `Kd` ทีละ 0.02 จนการส่ายหายไป
# 3. เพิ่ม `MAX_SPEED` ทีละ 0.05 แล้ววนกลับไปข้อ 1 ถ้าเริ่มหลุดโค้ง
#
# จดผลทุกครั้งในตารางนี้ (double-click เพื่อแก้):
#
# | ครั้งที่ | Kp | Kd | MAX_SPEED | เวลา 1 รอบ (วินาที) | อาการ |
# | :---: | :---: | :---: | :---: | :---: | :--- |
# | 1 | 0.6 | 0.05 | 0.45 | | |
# | 2 | | | | | |
# | 3 | | | | | |

# %%
KP = 0.6
KD = 0.05
MAX_SPEED = 0.45

follow_line(MyPID(kp=KP, kd=KD), seconds=30)

# %% [markdown]
# ## 6. บันทึกค่าที่ดีที่สุด

# %%
print(save_params(kp=KP, kd=KD, max_speed=MAX_SPEED, min_speed=MIN_SPEED))

# %%
server.stop()
camera.release()
robot.stop()

# %% [markdown]
# ## สรุป
#
# - [ ] `MyPID` ผ่าน assert ทุกข้อ
# - [ ] เห็นภาพ debug ใน browser ระหว่างรถวิ่ง
# - [ ] รถวิ่งรอบสนามซ้อมได้โดยไม่หลุดเส้น
# - [ ] บันทึก `kp`, `kd`, `max_speed` แล้ว
#
# ถ้าตามไม่ทัน เปิดเฉลยใน `solutions/` แล้วไปต่อ module ถัดไปได้เลย
