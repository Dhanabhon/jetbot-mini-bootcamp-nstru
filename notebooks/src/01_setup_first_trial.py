# %% [markdown]
# # Module 1: System Architecture & First Trial
#
# **เวลา:** 09:00 – 09:45 น.
#
# ## เป้าหมาย
#
# - รู้จักชิ้นส่วนของ JetBot Mini และเส้นทางข้อมูล: กล้อง → Jetson Nano → มอเตอร์
# - อ่านแรงดันแบตเตอรี่ แสดงข้อความบนจอ OLED และดูภาพจากกล้อง
# - สั่งรถวิ่งครั้งแรกอย่างปลอดภัย
#
# ```text
# กล้อง IMX219 ──CSI──▶ Jetson Nano (Python + OpenCV) ──I2C──▶ บอร์ดขับมอเตอร์ ──▶ ล้อซ้าย / ขวา
#                              │
#                              └──I2C──▶ จอ OLED, Buzzer, วัดแรงดันแบตเตอรี่
# ```
#
# > **กฎความปลอดภัย:** ทุก cell ที่สั่งมอเตอร์จะหยุดรถใน `finally` เสมอ ถ้ารถวิ่งไม่หยุด กดปุ่ม ■ (Interrupt)
# > ที่แถบด้านบน แล้วรัน `robot.stop()`

# %% [setup]

# %% [markdown]
# ## 1. ตรวจเครื่อง
#
# - power mode ต้องเป็น **MAXN** (โหมด 0) ไม่อย่างนั้น CPU และ GPU จะถูกจำกัดความเร็ว
# - กล้องต้องโผล่เป็น `/dev/video0`

# %%
!sudo nvpmodel -q
!ls /dev/video*
!free -h

# %% [markdown]
# ## 2. ระดับแบตเตอรี่
#
# แบตเตอรี่เป็น Li-ion 3 เซลล์ เต็มที่ `12.6V` และไม่ควรใช้ต่อเมื่อต่ำกว่าราว `10.5V` (3.5V ต่อเซลล์)
# แรงดันที่ตกลงทำให้รถวิ่งช้าลง ใน Module 7 เราจะชดเชยค่านี้
#
# **TODO:** เขียน `battery_percent()` แปลงแรงดันเป็นเปอร์เซ็นต์แบบเส้นตรง 10.5V = 0% ถึง 12.6V = 100%
# และต้องไม่ต่ำกว่า 0 หรือเกิน 100 รันแล้วบรรทัด `assert` ต้องผ่าน

# %%
from jetbot_nstru.hardware import read_battery_voltage

EMPTY_V = 10.5
FULL_V = 12.6


def battery_percent(voltage):
    # BEGIN SOLUTION: คำนวณสัดส่วนระหว่าง EMPTY_V กับ FULL_V แล้วจำกัดให้อยู่ใน 0–100
    percent = (voltage - EMPTY_V) / (FULL_V - EMPTY_V) * 100
    return max(0.0, min(100.0, percent))
    # END SOLUTION


assert battery_percent(12.6) == 100
assert battery_percent(10.0) == 0
assert abs(battery_percent(11.55) - 50) < 0.01

voltage = read_battery_voltage()
print("แบตเตอรี่ {:.2f} V ประมาณ {:.0f}%".format(voltage, battery_percent(voltage)))

# %% [markdown]
# ## 3. จอ OLED
#
# จอ OLED มีโปรแกรมคอยแสดงชื่อ Wi-Fi และ IP อยู่ (`nstru_status` ที่โปรแกรมตั้งค่าติดตั้งให้ หรือ `jetbotmini_stats` ของ Yahboom)
# ต้องหยุดโปรแกรมนั้นก่อน ไม่อย่างนั้นข้อความของเราจะถูกเขียนทับ
# (โปรแกรมจะกลับมาเองเมื่อเปิดเครื่องใหม่)
#
# **TODO:** แสดงชื่อเล่นของคุณแบบตัวใหญ่ แล้วลองแบบหลายบรรทัด (`big=False`) ให้แสดงชื่อและแรงดันแบตเตอรี่
# ตัวใหญ่ใช้ภาษาอังกฤษเท่านั้น เพราะฟอนต์บนจอไม่มีตัวอักษรไทย

# %%
!sudo systemctl stop nstru_status jetbotmini_stats  # ตัวไหนไม่มีในเครื่อง จะขึ้น not loaded ไม่เป็นไร

from jetbot_nstru.hardware import Oled

oled = Oled()
# BEGIN SOLUTION: oled.show("NAME") แล้วลอง oled.show("line 1\nline 2", big=False)
oled.show("NSTRU")
oled.show("JetBot NSTRU\nbatt {:.1f} V".format(read_battery_voltage()), big=False)
# END SOLUTION

# %% [markdown]
# ## 4. ภาพจากกล้อง
#
# เราใช้ภาพขนาด 320×240 เพราะเล็กพอให้ประมวลผลได้เร็ว และยังเห็นเส้นกับป้ายชัด
#
# `lock_exposure=True` ล็อกค่าแสงและสมดุลสีขาว ไม่ให้กล้องปรับเองทุกเฟรม ภาพจึงไม่วูบวาบเวลารถหันเข้าหาไฟเพดาน
# ซึ่งสำคัญมากตอนใช้ threshold สีใน Module 3 และ 5
#
# กล้องเปิดได้ทีละ notebook เท่านั้น ก่อนเปิด notebook ถัดไปให้รัน cell ปิดอุปกรณ์ท้าย notebook หรือ Shut Down Kernel

# %%
import time

import ipywidgets as widgets
from IPython.display import display

from jetbot_nstru.hardware import CsiCamera
from jetbot_nstru.viz import encode_jpeg

camera = CsiCamera(width=320, height=240, lock_exposure=True)
view = widgets.Image(format="jpeg", width=320, height=240)
display(view)

start = time.monotonic()
frames = 0
while time.monotonic() - start < 5:  # ภาพสด 5 วินาที
    view.value = encode_jpeg(camera.read())
    frames += 1
print("ได้ {:.1f} เฟรมต่อวินาที (รวมเวลาส่งภาพมาที่ browser)".format(frames / 5.0))

# %% [markdown]
# ## 5. สำหรับผู้สอน: ตรวจ API ของ Yahboom
#
# ค่าที่มีคำว่า `VERIFY ON ROBOT` ใน `jetbot_nstru/hardware.py` มาจากเอกสารของ Yahboom และ NVIDIA JetBot
# ยังไม่ได้ทดสอบกับหุ่นยนต์ชุดนี้ cell ด้านล่างพิมพ์ที่อยู่และโค้ดของ Yahboom ที่อ่านแบตเตอรี่และสั่ง buzzer
# ถ้า address, register หรือชื่อ attribute ไม่ตรงกับใน `hardware.py` ให้แก้ที่ `hardware.py` ที่เดียว
#
# ผู้เข้าอบรมข้ามส่วนนี้ได้

# %%
!systemctl cat jetbotmini_stats | grep ExecStart

import inspect

from jetbot_nstru.hardware import open_robot

robot = open_robot()
print(type(robot), inspect.getsourcefile(type(robot)))
print([name for name in dir(robot) if not name.startswith("_")])  # Robot ของ Yahboom ไม่มี buzzer จึงใช้ set_buzzer() ใน hardware.py แทน
print(inspect.getsource(type(robot))[:3000])

# %% [markdown]
# ## 6. วิ่งครั้งแรก
#
# วางรถบนพื้น (ไม่ใช่บนโต๊ะ) แล้วรัน cell นี้ รถจะเดินหน้าช้า ๆ 1 วินาทีแล้วหยุด
# ค่าความเร็วอยู่ในช่วง -1 ถึง 1 (ติดลบคือถอยหลัง)

# %%
robot = open_robot()
try:
    robot.set_motors(0.3, 0.3)
    time.sleep(1.0)
finally:
    robot.stop()

# %% [markdown]
# ## ปิดอุปกรณ์
#
# รัน cell นี้ก่อนไป Module 2 เพื่อปล่อยกล้องให้ notebook ถัดไปใช้

# %%
robot.stop()
camera.release()
oled.clear()

# %% [markdown]
# ## สรุป
#
# - [ ] power mode เป็น MAXN
# - [ ] อ่านแรงดันแบตเตอรี่ได้ และแปลงเป็นเปอร์เซ็นต์
# - [ ] แสดงข้อความบนจอ OLED ได้
# - [ ] เห็นภาพจากกล้อง
# - [ ] รถเดินหน้าแล้วหยุดเองได้
