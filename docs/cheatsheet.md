---
title: Cheat sheet
parent: เอกสารอ้างอิง
nav_order: 1
---

# Cheat Sheet

> คำสั่งของกล้อง OLED Buzzer และแบตเตอรี่ยังรอทดสอบกับหุ่นยนต์จริง ดู[คู่มือผู้สอน](instructor-guide.md)

## เชื่อมต่อ

- ต่อคอมพิวเตอร์เข้า Wi-Fi ของห้องอบรม (ชื่อและรหัสผ่านติดไว้หน้าห้อง)
- อ่าน IP จากสติ๊กเกอร์ที่ตัวรถ หรือจอ OLED แล้วเปิด `http://<IP>:8888` ใน Google Chrome

## คำสั่งที่ใช้บ่อย

| งาน | โค้ด |
| :--- | :--- |
| เปิดรถ | `from jetbot_nstru.hardware import open_robot` แล้ว `robot = open_robot()` |
| สั่งมอเตอร์ซ้าย-ขวา | `robot.set_motors(left, right)` (ค่า -1.0 ถึง 1.0) |
| หยุดรถ | `robot.stop()` |
| อ่านภาพจากกล้อง | `camera = CsiCamera(width=320, height=240)` แล้ว `frame = camera.read()` |
| ปิดกล้อง (ก่อนเปิด notebook อื่น) | `camera.release()` |
| แสดงข้อความบนจอ OLED | `!sudo systemctl stop nstru_status jetbotmini_stats` ครั้งเดียว แล้ว `Oled().show("STOP")` |
| ส่งเสียง Buzzer | `beep(robot)` (ไม่ block loop) |
| อ่านแรงดันแบต | `read_battery_voltage()` (เต็ม 12.6 V) |
| ดูภาพ debug บนเครื่องตัวเอง | `server = MjpegServer().start()` แล้ว `server.push(draw_overlay(frame, VizState(...)))` เปิด `http://<IP>:8080` |
| โหลด / บันทึกค่าของรถ | `load_params()` / `save_params(kp=0.6)` (ไฟล์ `my_params.json`) |

`CsiCamera`, `Oled`, `beep`, `read_battery_voltage` import จาก `jetbot_nstru.hardware` ส่วน `MjpegServer`, `VizState`, `draw_overlay` อยู่ใน `jetbot_nstru.viz`

ถ้าเปิดกล้องแล้วขึ้น error ว่ากล้องไม่ว่าง แปลว่ามี notebook อื่นถือกล้องอยู่ ให้ Shutdown kernel ของ notebook นั้น หรือรัน `!sudo systemctl restart nvargus-daemon`

## จูน PID: อาการและวิธีแก้

| อาการ | สาเหตุที่เป็นไปได้ | ลองแก้ |
| :--- | :--- | :--- |
| ส่ายซ้ายขวาบนทางตรง | `Kp` สูงเกิน | ลด `Kp` หรือเพิ่ม `Kd` |
| เลี้ยวไม่ทัน หลุดโค้ง | `Kp` ต่ำเกิน หรือเร็วเกิน | เพิ่ม `Kp` หรือลดความเร็วตอนเข้าโค้ง |
| กระตุกแรงเมื่อ error เปลี่ยนเร็ว | `Kd` สูงเกิน หรือภาพมี noise | ลด `Kd` หรือ filter ค่า `cx` |
| วิ่งดีตอนแบตเต็ม แล้วแย่ลง | แรงดันแบตเตอรี่ตก | ชดเชยความเร็วตามแรงดัน |

## Vision: ปัญหาที่เจอบ่อย

| อาการ | ลองแก้ |
| :--- | :--- |
| ภาพสว่าง/มืดวูบวาบ | ปิด Auto Exposure ของกล้อง |
| mask เส้นขาดเป็นช่วง ๆ | ปรับช่วง HSV หรือใช้ Adaptive Threshold |
| อ่านป้ายพลาดตอนวิ่งเร็ว | ลด Motion Blur หรือชะลอก่อนถึงจุดตัด |
