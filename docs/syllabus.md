---
title: ตารางอบรม
nav_order: 3
---

# ตารางอบรม 6 ชั่วโมง

การอบรมจัด 1 วัน ส่วนการแข่งขันจัดแยกเป็นอีกวัน ดูกำหนดการวันแข่งที่ [competition-rules.md](competition-rules.md)

แต่ละ module มี notebook ของตัวเองใน `notebooks/` เลขบทในวงเล็บอ้างอิงบทเรียนของ Yahboom

บรรทัด **โค้ด:** ท้ายแต่ละ module ลิงก์ไปที่ notebook ที่ใช้ในห้อง (มีช่อง `TODO`), เฉลย และไฟล์ใน `jetbot_nstru/` ที่ module นั้นเรียกใช้ ลิงก์เปิดบน GitHub ไว้อ่านล่วงหน้า ตอนอบรมให้เปิด notebook ผ่าน Jupyter Lab บนหุ่นยนต์

สไลด์ที่ใช้บรรยายตลอดวัน เรียงตาม module เดียวกับตารางนี้: [ดาวน์โหลดสไลด์ (PDF)]({{ '/assets/slides/jetbot-mini-bootcamp-lecture.pdf' | relative_url }})

## ช่วงเช้า (09:00 – 12:00): เชื่อมต่อหุ่นยนต์และเดินตามเส้นความเร็วสูง

เป้าหมาย: ควบคุมมอเตอร์และกล้องผ่าน Jupyter Lab ได้ และมีระบบเดินตามเส้นที่จูน PID แล้ว

| เวลา | Module | สิ่งที่ลงมือทำ |
| :--- | :--- | :--- |
| 09:00 – 09:45 | **1: System Architecture & First Trial**<br>(บทที่ 2.2, 3.1, 4.1, 5.4, 5.5) | • ตรวจ hardware: Jetson Nano, กล้อง IMX219, มอเตอร์ TT Gear 1:48, จอ OLED<br>• อ่าน IP Address จากจอ OLED แล้วเข้า Jupyter Lab ที่ `http://<IP>:8888`<br>• เช็กระดับแบตเตอรี่ (Li-ion `12.6V`) และทดสอบแสดงข้อความบนจอ OLED<br>**โค้ด:** [notebook](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/01_setup_first_trial.ipynb) · [เฉลย](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/solutions/01_setup_first_trial_solution.ipynb) · [`hardware.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/hardware.py) |
| 09:45 – 10:30 | **2: Hardware & Differential Drive Control**<br>(บทที่ 6.1) | • ควบคุมความเร็วล้อซ้าย-ขวาด้วย `robot.set_motors(left, right)`<br>• ทำ Motor Trim ชดเชยล้อซ้าย-ขวา ให้รถวิ่งตรงที่ความเร็วสูงสุด<br>**โค้ด:** [notebook](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/02_motor_control_calibration.ipynb) · [เฉลย](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/solutions/02_motor_control_calibration_solution.ipynb) · [`pid.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/pid.py) · [`params.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/params.py) |
| 10:30 – 11:15 | **3: High-Speed Line Detection with OpenCV**<br>(บทที่ 4.2, 10.1) | • ตั้งมุมก้มกล้อง (Camera Pitch) และตัดภาพด้วย ROI ให้เหลือเฉพาะพื้นถนนเพื่อเพิ่ม FPS<br>• แปลงเป็น HSV หรือใช้ Adaptive Threshold รับมือแสงสะท้อนบนพื้นไวนิล<br>• หา centroid ของเส้น (`cx`) และตรวจจับสี่เหลี่ยมสีเขียวที่จุดตัด<br>**โค้ด:** [notebook](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/03_line_detection_opencv.ipynb) · [เฉลย](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/solutions/03_line_detection_opencv_solution.ipynb) · [`line.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/line.py) |
| 11:15 – 12:00 | **4: PID Control Tuning for Speed**<br>(บทที่ 6.6) | • เขียน PID Controller แปลง error (`cx - center_x`) เป็นความต่างความเร็วล้อ<br>• Dynamic Speed Control: ทางตรงเร่งเต็มที่ เข้าโค้งชะลอเอง<br>• วิ่งจับเวลาบนสนามซ้อม<br>**โค้ด:** [notebook](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/04_pid_line_following.ipynb) · [เฉลย](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/solutions/04_pid_line_following_solution.ipynb) · [`pid.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/pid.py) · [`viz.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/viz.py) |

## ช่วงบ่าย (13:00 – 16:00): อ่านป้ายจราจรและรวมเป็นภารกิจแข่งขัน

เป้าหมาย: หุ่นยนต์แยกป้ายได้แม่นขณะวิ่งเร็ว และเปลี่ยนพฤติกรรมที่จุดตัดได้ทันที

| เวลา | Module | สิ่งที่ลงมือทำ |
| :--- | :--- | :--- |
| 13:00 – 14:00 | **5: Traffic Sign Recognition**<br>(บทที่ 4.3, 4.6, 6.3) | • เทียบ 2 แนวทาง:<br>  1. Color + Contour/Shape Matching ด้วย OpenCV: เร็ว (>30 FPS) เหมาะกับป้ายที่สีและรูปทรงชัด<br>  2. Deep Learning Classifier (ResNet18 / TensorRT): เทรนจากภาพป้ายจริงแล้วรันบน GPU<br>• เทคนิคลด Motion Blur และแก้แสงสะท้อนบนสติ๊กเกอร์ป้าย<br>**โค้ด:** [notebook](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/05_traffic_sign_recognition.ipynb) · [เฉลย](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/solutions/05_traffic_sign_recognition_solution.ipynb) · [`signs.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/signs.py) |
| 14:00 – 14:45 | **6: State Machine & Mission Integration** | • ออกแบบ Finite State Machine (FSM) รวมการเดินตามเส้นกับการอ่านป้าย<br>• Pre-fetch Sign (อ่านป้ายล่วงหน้า) คู่กับ Green Node Trigger (สั่งเลี้ยวเมื่อเจอสี่เหลี่ยมสีเขียว)<br>• แสดงชื่อป้ายบนจอ OLED และส่งเสียง Buzzer ยืนยัน<br>**โค้ด:** [notebook](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/06_fsm_mission_integration.ipynb) · [เฉลย](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/solutions/06_fsm_mission_integration_solution.ipynb) · [`fsm.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/fsm.py) |
| 14:45 – 15:45 | **7: Free Practice & Track Optimization** | • เปิดสนามจริงให้ทดสอบวิ่ง (Qualifying Runs)<br>• จูน `Kp, Kd`, threshold ของสี/AI และชดเชยความเร็วเมื่อแรงดันแบตเตอรี่ตก<br>**โค้ด:** [notebook](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/07_competition_template.ipynb) · [เฉลย](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/solutions/07_competition_template_solution.ipynb) · [`params.py`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/jetbot_nstru/params.py) |
| 15:45 – 16:00 | **8: Briefing กติกาและเตรียมตัวสำหรับวันแข่ง** | • อธิบายกติกาและการคิด Net Time<br>• บันทึกโค้ดและค่าพารามิเตอร์ล่าสุดไว้ใน [`07_competition_template.ipynb`](https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru/blob/main/notebooks/07_competition_template.ipynb)<br>• นัดหมายวันแข่ง และแนะนำสิ่งที่นำหุ่นยนต์กลับไปพัฒนาต่อเองได้ (เช่น เก็บภาพป้ายเพิ่ม เทรน classifier จูนความเร็ว) |
