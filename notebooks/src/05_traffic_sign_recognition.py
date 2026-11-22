# %% [markdown]
# # Module 5: Traffic Sign Recognition
#
# **เวลา:** 13:00 – 14:00 น.
#
# ## เป้าหมาย
#
# - จำแนกป้าย 5 แบบด้วยสีและรูปทรง: เลี้ยวซ้าย, เลี้ยวขวา, ตรงไป, STOP (หยุด), PARKING
# - ใช้ majority vote หลายเฟรม กันภาพเบลอเฟรมเดียวทำให้รถตัดสินใจผิด
# - เก็บภาพป้ายจากกล้องจริงไว้เทรน classifier (ทางเลือก ทำต่อที่บ้านได้)
#
# ## ป้ายต่างกันตรงไหน
#
# | ป้าย | สี | รูปทรง | แยกด้วย |
# | :--- | :--- | :--- | :--- |
# | หยุด (STOP) | แดง | แปดเหลี่ยม | ป้ายสีแดงมีแบบเดียว ใช้สีพอ |
# | ที่จอดรถ (PARKING) | น้ำเงิน | สี่เหลี่ยม | extent = พื้นที่ contour / พื้นที่กล่อง ≈ 1.0 |
# | ซ้าย, ขวา, ตรง | น้ำเงิน | วงกลม (extent ≈ 0.78) | ดูว่าลูกศรสีขาว**ครึ่งบน**ของป้ายเอียงไปทางไหน |
#
# ```text
#   ซ้าย          ขวา          ตรง
#  ◀━━┓         ┏━━▶          ▲
#     ┃         ┃             ┃       หัวลูกศรอยู่ครึ่งบนเสมอ: ซ้ายมีสีขาวครึ่งบนฝั่งซ้ายมากกว่า
#     ┃         ┃             ┃       ขวามีฝั่งขวามากกว่า ตรงไปเท่า ๆ กัน
# ```

# %% [setup]

# %%
import os
import time

import cv2
import ipywidgets as widgets
import numpy as np
from IPython.display import display

from jetbot_nstru.viz import VizState, draw_overlay, encode_jpeg

FIXTURES = os.path.join(root, "tests", "fixtures", "signs")  # ภาพป้ายจากไฟล์สติ๊กเกอร์ ใช้ทดสอบโดยไม่ต้องใช้กล้อง
view = widgets.Image(format="jpeg", width=320)
display(view)


def sample_scene(name, size=48):
    """วางภาพป้ายลงบนพื้นสีเทาอ่อน ให้คล้ายภาพจากกล้องรถ"""
    frame = np.full((240, 320, 3), 225, np.uint8)
    sign = cv2.resize(cv2.imread(os.path.join(FIXTURES, name + ".png")), (size, size))
    frame[30 : 30 + size, 200 : 200 + size] = sign
    return frame


view.value = encode_jpeg(sample_scene("left"))

# %% [markdown]
# ## 1. แยกป้ายด้วยสี (น้ำเงิน / แดง)
#
# ใน HSV ของ OpenCV สีแดงอยู่**ทั้งสองปลาย**ของช่วง H (0–10 และ 170–180) จึงต้อง `inRange` สองครั้งแล้วเอามา OR กัน
#
# ป้ายตั้งสูงจากพื้น จึงหาเฉพาะครึ่งบนของภาพ (`SEARCH_BOTTOM`) ลดโอกาสที่ของบนพื้นจะถูกนับเป็นป้าย
#
# **TODO:** เขียน `colour_masks(hsv)` คืน `(blue, red)` แต่ละตัวเป็น mask ขาวดำ

# %%
SEARCH_BOTTOM = 0.6
BLUE = ((100, 120, 50), (130, 255, 255))
RED1 = ((0, 120, 70), (10, 255, 255))
RED2 = ((170, 120, 70), (180, 255, 255))


def colour_masks(hsv):
    # BEGIN SOLUTION: cv2.inRange(hsv, np.array(lower), np.array(upper)) สำหรับ BLUE และ RED1 | RED2
    blue = cv2.inRange(hsv, np.array(BLUE[0]), np.array(BLUE[1]))
    red = cv2.inRange(hsv, np.array(RED1[0]), np.array(RED1[1])) | cv2.inRange(hsv, np.array(RED2[0]), np.array(RED2[1]))
    return blue, red
    # END SOLUTION


hsv = cv2.cvtColor(sample_scene("stop"), cv2.COLOR_BGR2HSV)
blue, red = colour_masks(hsv)
assert red.sum() > 0 and blue.sum() == 0
view.value = encode_jpeg(red)

# %% [markdown]
# ## 2. ตรวจรูปทรงด้วย contour
#
# **TODO:** เขียน `extent(contour)` คืน พื้นที่ contour / พื้นที่ bounding box
# วงกลมได้ราว π/4 ≈ 0.785 สี่เหลี่ยมได้เกือบ 1.0

# %%
def extent(contour):
    # BEGIN SOLUTION: x, y, w, h = cv2.boundingRect(contour) แล้วคืน cv2.contourArea(contour) / (w * h)
    x, y, w, h = cv2.boundingRect(contour)
    return cv2.contourArea(contour) / float(w * h)
    # END SOLUTION


def biggest(mask, min_area=250):
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    big = [c for c in contours if cv2.contourArea(c) >= min_area]
    return max(big, key=cv2.contourArea) if big else None


for name in ("left", "parking"):
    blue, _ = colour_masks(cv2.cvtColor(sample_scene(name, size=80), cv2.COLOR_BGR2HSV))
    print(name, "extent = {:.2f}".format(extent(biggest(blue))))

# %% [markdown]
# ## 3. แยกทิศลูกศร ซ้าย / ขวา / ตรง
#
# ตัดเฉพาะกรอบป้าย หาพิกเซลสีขาว (S ต่ำ, V สูง) แล้วนับเฉพาะครึ่งบน:
#
# `balance = (ขาวฝั่งซ้าย - ขาวฝั่งขวา) / (ขาวทั้งหมด)`
#
# ป้ายมีขอบขาวรอบวงกลม ซึ่งมีเท่ากันทั้งสองฝั่งแต่ทำให้ balance เข้าใกล้ 0 จึงหดรูปป้ายเข้ามาก่อน (`erode`)
# ให้เหลือแต่ด้านในวงกลม
#
# **TODO:** เขียน `arrow_direction(balance, threshold)` คืน `"LEFT"`, `"RIGHT"` หรือ `"STRAIGHT"`

# %%
from jetbot_nstru.signs import SignConfig, arrow_balance

TURN_BALANCE = 0.15


def arrow_direction(balance, threshold=TURN_BALANCE):
    # BEGIN SOLUTION: balance > threshold คือ LEFT, < -threshold คือ RIGHT, นอกนั้น STRAIGHT
    if balance > threshold:
        return "LEFT"
    if balance < -threshold:
        return "RIGHT"
    return "STRAIGHT"
    # END SOLUTION


for name in ("left", "right", "straight"):
    hsv = cv2.cvtColor(sample_scene(name, size=80), cv2.COLOR_BGR2HSV)
    contour = biggest(colour_masks(hsv)[0])
    x, y, w, h = cv2.boundingRect(contour)
    balance = arrow_balance(hsv[y : y + h, x : x + w], contour - [x, y], SignConfig())
    print("{:8s} balance {:+.2f} -> {}".format(name, balance, arrow_direction(balance)))
    assert arrow_direction(balance) == name.upper()

# %% [markdown]
# ## 4. รวมทุกขั้นตอน: `detect_sign` แล้วลองกับกล้องจริง
#
# ขั้นตอนทั้งหมดรวมอยู่ใน `jetbot_nstru/signs.py` แล้ว ถือป้ายจริงห่างจากกล้องหลายระยะ หรือวางรถหน้าเสาป้าย
# แล้วดูว่าอ่านได้ไกลสุดกี่ ซม. จดไว้ เพราะเป็นตัวกำหนดว่ารถมีเวลาตัดสินใจก่อนถึงจุดตัดเท่าไร

# %%
from jetbot_nstru.hardware import CsiCamera
from jetbot_nstru.signs import LABELS, detect_sign

for name in LABELS:
    assert detect_sign(sample_scene(name.lower())).label == name

camera = CsiCamera(width=320, height=240, lock_exposure=True)
display(view)  # แสดงภาพใต้ cell นี้ด้วย ไม่อย่างนั้นภาพจะขยับอยู่แค่ด้านบนสุดของ notebook
start = time.monotonic()
while time.monotonic() - start < 20:
    frame = camera.read()
    sign = detect_sign(frame)
    view.value = encode_jpeg(draw_overlay(frame, VizState(fsm_state=sign.label if sign else "", sign=sign)))

# %% [markdown]
# ## 5. Majority vote กันเฟรมเบลอ
#
# ตอนรถวิ่งเร็ว บางเฟรมจะเบลอจนอ่านผิด `SignVoter` จำผลของ 7 เฟรมล่าสุด แล้วยืนยันป้ายก็ต่อเมื่อมีอย่างน้อย 4 เฟรมตรงกัน
#
# **TODO:** ใส่ผลอ่านต่อไปนี้ทีละเฟรมลงใน voter แล้วดูว่าเฟรมไหนที่ป้ายถูกยืนยัน เปลี่ยน `min_votes` แล้วลองใหม่
# คิดดู: ถ้า `min_votes` สูงไป หรือต่ำไป จะเกิดอะไรขึ้นในสนามจริง

# %%
from jetbot_nstru.signs import SignVoter

readings = [None, "LEFT", "RIGHT", "LEFT", None, "LEFT", "LEFT", "STRAIGHT", "LEFT"]
voter = SignVoter(window=7, min_votes=4)
for index, reading in enumerate(readings):
    print(index, reading, "->", voter.update(reading))

# %% [markdown]
# ## 6. ลด Motion Blur และแสงสะท้อน
#
# | ปัญหา | วิธีแก้ |
# | :--- | :--- |
# | ภาพเบลอตอนวิ่งเร็ว | ล็อก exposure ให้สั้น (`lock_exposure=True` ล็อกค่าที่กล้องเลือกตอนเปิด ให้เปิดกล้องในที่สว่าง), ชะลอเมื่อเริ่มเห็นป้าย |
# | แสงไฟเพดานสะท้อนเป็นจุดขาวบนป้าย | ใช้สติ๊กเกอร์ด้าน (Matte) และเอียงหน้าป้ายก้มลง 5–10° ตาม `docs/sign-specs.md` |
# | สีเพี้ยนในห้องแสงเหลือง | จูนช่วง H ของ `SignConfig` ด้วยภาพจากห้องจริง |
#
# ## 7. ทางเลือก: เก็บภาพไว้เทรน Deep Learning Classifier
#
# วิธีสีและรูปทรงเร็ว (เป้าหมายเกิน 30 FPS บน Jetson Nano) แต่พังได้ถ้าแสงต่างจากที่จูนไว้มาก
# อีกแนวทางคือเทรน CNN เช่น ResNet18 จากภาพป้ายจริง แล้วแปลงเป็น TensorRT ให้รันบน GPU ของ Jetson Nano
# ซึ่งต้องใช้ภาพจริงจำนวนมาก cell ด้านล่างช่วยเก็บภาพ: เลือกชนิดป้าย ถือรถหรือป้ายหลายระยะหลายมุม แล้วกดถ่าย
#
# ภาพจะถูกเก็บใน `dataset/signs/<ชนิดป้าย>/` เก็บอย่างน้อยชนิดละ 100 ภาพ หลายสภาพแสง การเทรนทำต่อที่บ้านได้
# (ภาพและไฟล์ model ไม่ถูก commit ขึ้น git ตาม `.gitignore`)
#
# ถ้าจะเก็บภาพเยอะ ๆ ใช้ `solutions/05_sign_viewer.py` สะดวกกว่า: ถือรถแล้วกดปุ่มตัวเลขบนคีย์บอร์ดถ่ายได้เลย

# %%
import uuid

label_picker = widgets.ToggleButtons(options=[name.lower() for name in LABELS], description="ป้าย")
snap = widgets.Button(description="ถ่าย")
counter = widgets.Label()


def save_snapshot(_):
    folder = os.path.join(root, "dataset", "signs", label_picker.value)
    os.makedirs(folder, exist_ok=True)
    frame = camera.read()
    cv2.imwrite(os.path.join(folder, "{}.jpg".format(uuid.uuid4().hex[:12])), frame)
    view.value = encode_jpeg(frame)
    counter.value = "{}: {} ภาพ".format(label_picker.value, len(os.listdir(folder)))


snap.on_click(save_snapshot)
display(label_picker, snap, counter, view)

# %%
camera.release()

# %% [markdown]
# ## สรุป
#
# - [ ] แยกสีแดงและน้ำเงินได้
# - [ ] บอกได้ว่าป้ายน้ำเงินเป็นวงกลมหรือสี่เหลี่ยม
# - [ ] แยกทิศลูกศรซ้าย ขวา ตรงได้ถูกทั้ง 3 ภาพตัวอย่าง
# - [ ] จดระยะไกลสุดที่กล้องจริงอ่านป้ายได้ถูก: ______ ซม.
#
# ถ้าตามไม่ทัน เปิดเฉลยใน `solutions/` แล้วไปต่อ module ถัดไปได้เลย
