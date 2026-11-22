# %% [markdown]
# # Module 2: Differential Drive & Motor Trim
#
# **เวลา:** 09:45 – 10:30 น.
#
# ## เป้าหมาย
#
# - เข้าใจ differential drive: รถเลี้ยวได้เพราะล้อซ้ายกับขวาหมุนเร็วไม่เท่ากัน
# - เขียนฟังก์ชันสั่งรถวิ่งตามเวลาที่หยุดรถเสมอ แม้โค้ดจะ error
# - ทำ Motor Trim ให้รถวิ่งตรงเมื่อสั่งล้อทั้งสองเท่ากัน แล้วบันทึกค่าไว้ใช้ใน module ถัดไป
#
# | `left` | `right` | รถทำอะไร |
# | :---: | :---: | :--- |
# | 0.4 | 0.4 | เดินหน้าตรง (ถ้า trim ดีแล้ว) |
# | 0.5 | 0.3 | โค้งไปทางขวา |
# | -0.3 | 0.3 | หมุนตัวทางซ้ายอยู่กับที่ |
# | 0 | 0 | หยุด |

# %% [setup]

# %%
import time

from jetbot_nstru.hardware import open_robot
from jetbot_nstru.params import load_params, save_params
from jetbot_nstru.pid import MotorTrim, mix_motors

robot = open_robot()

# %% [markdown]
# ## 1. ฟังก์ชันวิ่งตามเวลาแบบปลอดภัย
#
# **TODO:** เขียน `drive_for(left, right, seconds)` สั่งมอเตอร์ รอตามเวลา แล้วหยุดรถใน `finally`
# เพื่อให้รถหยุดแม้เรากด Interrupt ระหว่างรอ

# %%
def drive_for(left, right, seconds):
    # BEGIN SOLUTION: ใช้ try / finally: ใน try สั่ง robot.set_motors แล้ว time.sleep ใน finally สั่ง robot.stop()
    try:
        robot.set_motors(left, right)
        time.sleep(seconds)
    finally:
        robot.stop()
    # END SOLUTION


drive_for(0.3, 0.3, 0.5)  # เดินหน้า
drive_for(-0.3, 0.3, 0.5)  # หมุนซ้าย
drive_for(0.3, -0.3, 0.5)  # หมุนขวา

# %% [markdown]
# ## 2. วัดว่ารถเบี้ยวไปทางไหน
#
# 1. แปะเทปเป็นเส้นตรงยาว 1 เมตรบนพื้น วางรถให้ล้อหน้าอยู่ที่ต้นเส้น หันตามเส้น
# 2. รัน cell ด้านล่าง รถจะวิ่งด้วยความเร็วที่ใช้แข่ง (`TEST_SPEED`) 2 วินาที
# 3. วัดว่าปลายทางรถเบี้ยวออกจากเส้นไปทางซ้ายหรือขวากี่ ซม.
#
# มอเตอร์ TT สองตัวไม่มีทางเหมือนกันเป๊ะ ตัวหนึ่งจะหมุนเร็วกว่าเล็กน้อย รถที่เบี้ยว**ไปทางขวา** แปลว่า**ล้อซ้ายเร็วกว่า**

# %%
TEST_SPEED = 0.5
saved = load_params()
trim = MotorTrim(saved.get("left_gain", 1.0), saved.get("right_gain", 1.0))
print("trim ปัจจุบัน:", trim)

left, right = mix_motors(TEST_SPEED, 0.0, trim)
drive_for(left, right, 2.0)

# %% [markdown]
# ## 3. ปรับ trim
#
# ลดกำลังเฉพาะล้อที่เร็วกว่า ไม่เพิ่มกำลังล้อที่ช้ากว่า เพราะถ้าสั่งเต็ม 1.0 แล้วคูณเพิ่ม ค่าจะเกินขีดจำกัด
#
# **TODO:** เขียน `adjust_trim()` รับ trim เดิมกับระยะที่เบี้ยว (`drift_cm` ค่าบวก = เบี้ยวขวา, ลบ = เบี้ยวซ้าย)
# แล้วคืน `MotorTrim` ใหม่ที่ลด gain ของล้อที่เร็วกว่าลงตาม `step_per_cm` ต่อ 1 ซม.
#
# ห้ามแก้ trim เดิม ให้สร้างอันใหม่ (`MotorTrim` แก้ค่าไม่ได้อยู่แล้ว ใช้ `trim._replace(...)`)

# %%
def adjust_trim(trim, drift_cm, step_per_cm=0.005):
    # BEGIN SOLUTION: drift_cm > 0 คือเบี้ยวขวา ล้อซ้ายเร็วกว่า ให้ลด left_gain; drift_cm < 0 ให้ลด right_gain
    change = abs(drift_cm) * step_per_cm
    if drift_cm > 0:
        return trim._replace(left_gain=round(trim.left_gain - change, 3))
    if drift_cm < 0:
        return trim._replace(right_gain=round(trim.right_gain - change, 3))
    return trim
    # END SOLUTION


assert adjust_trim(MotorTrim(), 4) == MotorTrim(0.98, 1.0)
assert adjust_trim(MotorTrim(), -2) == MotorTrim(1.0, 0.99)
assert adjust_trim(MotorTrim(), 0) == MotorTrim()

# %% [markdown]
# ใส่ระยะที่วัดได้ใน `DRIFT_CM` แล้วรันซ้ำสลับกับ cell ทดสอบด้านล่าง จนรถเบี้ยวไม่เกิน 2 ซม. ใน 2 วินาที

# %%
DRIFT_CM = 0  # แก้เป็นค่าที่วัดได้ เช่น 6 (เบี้ยวขวา 6 ซม.) หรือ -3

trim = adjust_trim(trim, DRIFT_CM)
print("trim ใหม่:", trim)

left, right = mix_motors(TEST_SPEED, 0.0, trim)
drive_for(left, right, 2.0)

# %% [markdown]
# ## 4. บันทึกค่า
#
# ค่าจะถูกเก็บใน `my_params.json` ที่ root ของ repo ทุก module หลังจากนี้จะโหลดค่านี้ไปใช้เอง
# ไฟล์นี้ไม่ถูก commit ขึ้น git เพราะรถแต่ละคันมีค่าของตัวเอง

# %%
print(save_params(left_gain=trim.left_gain, right_gain=trim.right_gain, trim_speed=TEST_SPEED))

# %% [markdown]
# ## 5. ทดลองเพิ่ม: โค้งด้วยความต่างของล้อ
#
# `mix_motors(base, steer)` คือหัวใจของการเดินตามเส้นใน Module 4: `steer` บวกทำให้ล้อซ้ายเร็วขึ้น รถโค้งไปทางขวา
# ลองเปลี่ยน `steer` แล้วสังเกตว่ารัศมีโค้งเปลี่ยนอย่างไร

# %%
for steer in (0.1, 0.2, -0.2):
    left, right = mix_motors(0.4, steer, trim)
    print("steer {:+.1f} -> left {:.2f}, right {:.2f}".format(steer, left, right))
    drive_for(left, right, 1.0)
    time.sleep(0.5)

# %%
robot.stop()

# %% [markdown]
# ## สรุป
#
# - [ ] `drive_for` หยุดรถเสมอ แม้กด Interrupt
# - [ ] รถวิ่งตรงที่ `TEST_SPEED` เบี้ยวไม่เกิน 2 ซม. ใน 2 วินาที
# - [ ] บันทึก trim ลง `my_params.json` แล้ว
