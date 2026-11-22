# %% [markdown]
# # Module 3: High-Speed Line Detection with OpenCV
#
# **เวลา:** 10:30 – 11:15 น.
#
# ## เป้าหมาย
#
# - ตั้งมุมก้มกล้อง และตัดภาพด้วย ROI ให้เหลือเฉพาะพื้นถนนเพื่อเพิ่ม FPS
# - แยกเส้นดำด้วย HSV (ค่าความสว่าง V) หรือ Adaptive Threshold
# - หา centroid ของเส้น (`cx`) แล้วแปลงเป็น error สำหรับ PID
# - ตรวจจับสี่เหลี่ยมสีเขียวที่จุดตัด
#
# ```text
# เฟรม 320x240 ──▶ ตัด ROI (ครึ่งล่าง) ──▶ mask เส้นดำ ──▶ contour ใหญ่สุด ──▶ centroid cx ──▶ error = (cx - 160) / 160
#                         └──────────▶ mask สีเขียว ──▶ กล่องสี่เหลี่ยมเขียว (จุดตัด)
# ```

# %% [setup]

# %%
import time

import cv2
import ipywidgets as widgets
import numpy as np
from IPython.display import display

from jetbot_nstru.hardware import CsiCamera
from jetbot_nstru.viz import VizState, draw_overlay, encode_jpeg, with_mask

camera = CsiCamera(width=320, height=240, lock_exposure=True)
view = widgets.Image(format="jpeg", width=320)
display(view)

# %% [markdown]
# ## 1. ตั้งมุมก้มกล้อง (Camera Pitch)
#
# วางรถบนเส้นดำของสนาม รัน cell นี้ แล้วค่อย ๆ ปรับมุมกล้องด้วยมือจนได้ภาพแบบนี้:
#
# - **ครึ่งล่าง** ของภาพเห็นเส้นดำชัด ช่วงประมาณ 10–30 ซม. หน้ารถ
# - **ครึ่งบน** ยังเห็นเสาป้ายที่มุมจุดตัดถัดไป (Module 5 ต้องใช้)
#
# ก้มมากไปจะไม่เห็นป้าย เงยมากไปเส้นใกล้รถจะหลุดเฟรม

# %%
start = time.monotonic()
while time.monotonic() - start < 15:
    frame = camera.read()
    cv2.line(frame, (0, 120), (319, 120), (0, 200, 255), 1)  # เส้นแบ่งครึ่งภาพ
    view.value = encode_jpeg(frame)

# %% [markdown]
# ## 2. ตัด ROI
#
# ประมวลผลแค่ส่วนที่ต้องใช้ทำให้เร็วขึ้น และตัดสิ่งรบกวนด้านบน (ขอบโต๊ะ เสาป้าย คนเดินผ่าน) ทิ้งไป
#
# **TODO:** เขียน `crop_roi(frame, top_ratio)` คืนภาพเฉพาะส่วนล่าง เริ่มที่แถว `int(height * top_ratio)` ถึงล่างสุด

# %%
ROI_TOP = 0.55


def crop_roi(frame, top_ratio):
    # BEGIN SOLUTION: height = frame.shape[0] แล้ว slice frame[top:, :]
    top = int(frame.shape[0] * top_ratio)
    return frame[top:, :]
    # END SOLUTION


frame = camera.read()
roi = crop_roi(frame, ROI_TOP)
assert roi.shape == (240 - int(240 * ROI_TOP), 320, 3)
view.value = encode_jpeg(roi)

# %% [markdown]
# ## 3. ทำ mask เส้นดำ
#
# แปลงเป็น HSV แล้วดูช่อง V (ความสว่าง) พื้นขาว V สูง เส้นดำ V ต่ำ ส่วนสี่เหลี่ยมเขียวยังสว่างพอ จึงไม่ถูกนับเป็นเส้น
#
# **TODO:** เขียน `black_mask(roi, v_max)` คืนภาพขาวดำ: 255 ตรงที่ V < `v_max`, 0 ที่อื่น
# แล้วใช้ `cv2.morphologyEx(..., cv2.MORPH_OPEN, kernel)` ลบจุด noise เล็ก ๆ
#
# เลื่อน slider ให้ mask เห็นเส้นเต็ม ๆ แต่ไม่มีจุดขาวกระจายบนพื้น แล้วจดค่าไว้

# %%
def black_mask(roi, v_max):
    # BEGIN SOLUTION: v = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)[:, :, 2] แล้ว np.where(v < v_max, 255, 0).astype(np.uint8)
    value = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)[:, :, 2]
    mask = np.where(value < v_max, 255, 0).astype(np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # END SOLUTION


mask_view = widgets.Image(format="jpeg", width=320)
v_slider = widgets.IntSlider(value=90, min=20, max=200, description="v_max")


def show_mask(change=None):
    roi = crop_roi(camera.read(), ROI_TOP)
    mask_view.value = encode_jpeg(black_mask(roi, v_slider.value))


v_slider.observe(show_mask, names="value")
display(v_slider, mask_view)
show_mask()

# %% [markdown]
# ### ทางเลือก: Adaptive Threshold
#
# ถ้าแสงในห้องไม่เท่ากัน เช่น มุมหนึ่งของสนามมีเงา ค่า `v_max` ค่าเดียวจะใช้ไม่ได้ทั้งสนาม
# Adaptive Threshold เทียบแต่ละ pixel กับค่าเฉลี่ยรอบตัวมันแทน แต่เส้นที่กว้างมาก ๆ (เช่น จุดตัด) จะกลวงตรงกลาง
# ลองดูทั้งสองแบบแล้วเลือกแบบที่เหมาะกับสนามของเรา

# %%
gray = cv2.cvtColor(crop_roi(camera.read(), ROI_TOP), cv2.COLOR_BGR2GRAY)
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 10)
mask_view.value = encode_jpeg(adaptive)

# %% [markdown]
# ## 4. หา centroid `cx`
#
# บนพื้นอาจมี mask จุดเล็ก ๆ หลายก้อน เราเลือกเฉพาะ contour ที่ใหญ่ที่สุด แล้วหาจุดศูนย์กลางมวลด้วย moments:
# `cx = m10 / m00`, `cy = m01 / m00`
#
# **TODO:** เขียน `find_centroid(mask, min_area)` คืน `(cx, cy)` ของ contour ที่ใหญ่ที่สุด
# ถ้าไม่มี contour ไหนใหญ่ถึง `min_area` ให้คืน `None`
#
# `cv2.findContours` คืนค่า 2 ตัวใน OpenCV 4 และ 3 ตัวใน OpenCV 3 ใช้ `[-2]` เพื่อให้ได้ list ของ contour ทั้งสองเวอร์ชัน

# %%
def find_centroid(mask, min_area=150):
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    # BEGIN SOLUTION: กรอง contour ที่ cv2.contourArea >= min_area เลือกตัวใหญ่สุด แล้วใช้ cv2.moments
    big = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not big:
        return None
    m = cv2.moments(max(big, key=cv2.contourArea))
    return int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])
    # END SOLUTION


test_mask = np.zeros((100, 320), np.uint8)
test_mask[:, 200:220] = 255
assert find_centroid(test_mask) == (209, 49)
assert find_centroid(np.zeros((100, 320), np.uint8)) is None

# %% [markdown]
# แปลง `cx` เป็น error ที่ไม่ขึ้นกับขนาดภาพ: `error = (cx - 160) / 160` จะได้ค่า -1 (เส้นอยู่ซ้ายสุด) ถึง 1 (ขวาสุด)
# PID ใน Module 4 จะใช้ค่านี้

# %%
V_MAX = v_slider.value
start = time.monotonic()
while time.monotonic() - start < 15:
    frame = camera.read()
    top = int(frame.shape[0] * ROI_TOP)
    mask = black_mask(crop_roi(frame, ROI_TOP), V_MAX)
    found = find_centroid(mask)
    state = VizState(line_roi=(0, top, 320, 240 - top),
                     cx=found[0] if found else None, cy=found[1] + top if found else None)
    view.value = encode_jpeg(with_mask(draw_overlay(frame, state), mask))

# %% [markdown]
# ## 5. ตรวจจับสี่เหลี่ยมสีเขียว
#
# สีเขียวแยกด้วยช่อง H (เฉดสี) ได้ดีกว่าแสง ใน OpenCV ค่า H อยู่ในช่วง 0–179 สีเขียวอยู่ราว 35–90
# ใช้ S (ความสด) ขั้นต่ำเพื่อไม่ให้พื้นขาวที่อมเขียวนิด ๆ หลุดเข้ามา
#
# **TODO:** เขียน `find_green(roi, lower, upper, min_area)` คืนกล่อง `(x, y, w, h)` ของก้อนเขียวที่ใหญ่ที่สุด หรือ `None`

# %%
GREEN_LOWER = (35, 80, 50)
GREEN_UPPER = (90, 255, 255)


def find_green(roi, lower=GREEN_LOWER, upper=GREEN_UPPER, min_area=400):
    # BEGIN SOLUTION: cv2.inRange บนภาพ HSV ด้วย np.array(lower) และ np.array(upper) แล้วหา contour ใหญ่สุด ใช้ cv2.boundingRect
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    big = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not big:
        return None
    return cv2.boundingRect(max(big, key=cv2.contourArea))
    # END SOLUTION


test_roi = np.full((100, 320, 3), 235, np.uint8)
test_roi[40:80, 100:150] = (60, 170, 40)  # BGR สีเขียว
assert find_green(test_roi) == (100, 40, 50, 40)

# %% [markdown]
# ## 6. วัด FPS: ทั้งภาพ เทียบกับ ROI
#
# ลองดูว่าการตัด ROI ช่วยให้เร็วขึ้นเท่าไร (ยังไม่รวมเวลาอ่านกล้อง)

# %%
frame = camera.read()
for name, image in (("ทั้งภาพ", frame), ("ROI", crop_roi(frame, ROI_TOP))):
    start = time.monotonic()
    for _ in range(200):
        find_centroid(black_mask(image, V_MAX))
        find_green(image)
    per_frame = (time.monotonic() - start) / 200
    print("{}: {:.1f} ms ต่อเฟรม ({:.0f} FPS)".format(name, per_frame * 1000, 1 / per_frame))

# %% [markdown]
# ## 7. ใช้ `detect_line` จาก `jetbot_nstru`
#
# โค้ดทั้งหมดที่เขียนมารวมไว้แล้วใน `jetbot_nstru/line.py` module ถัดไปจะ import จากที่นี่
# ใส่ค่า `v_max` ที่จูนได้ลงใน `LineConfig` แล้วบันทึกไว้

# %%
from jetbot_nstru.line import LineConfig, detect_line
from jetbot_nstru.params import save_params

line_cfg = LineConfig(roi_top=ROI_TOP, black_v_max=V_MAX)
save_params(roi_top=ROI_TOP, black_v_max=V_MAX)

start = time.monotonic()
while time.monotonic() - start < 15:
    frame = camera.read()
    result = detect_line(frame, line_cfg)
    state = VizState(fsm_state="green" if result.green_box else "", line_roi=result.roi_box,
                     cx=result.cx, cy=result.cy)
    view.value = encode_jpeg(with_mask(draw_overlay(frame, state), result.mask))

# %%
camera.release()

# %% [markdown]
# ## สรุป
#
# - [ ] ตั้งมุมกล้องแล้ว ครึ่งล่างเห็นเส้น ครึ่งบนเห็นป้าย
# - [ ] mask เส้นดำสะอาด ไม่มี noise บนพื้น
# - [ ] `cx` ตามเส้นได้ตอนเลื่อนรถซ้ายขวาด้วยมือ
# - [ ] เห็นกล่องสีเขียวตอนวางรถหน้าจุดตัด
# - [ ] บันทึก `roi_top` และ `black_v_max` แล้ว
#
# ถ้าตามไม่ทัน เปิดเฉลยใน `solutions/` แล้วไปต่อ module ถัดไปได้เลย
