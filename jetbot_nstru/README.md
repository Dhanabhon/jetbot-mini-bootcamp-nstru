# jetbot_nstru

โค้ด Python ที่ใช้ร่วมกันหลาย notebook เพื่อไม่ต้อง copy ซ้ำ เมื่อผู้เข้าอบรมเขียนส่วนไหนเสร็จใน module ก่อนหน้า module ถัดไปจะ import จากที่นี่

โครงที่วางไว้:

| ไฟล์ | หน้าที่ |
| :--- | :--- |
| `line.py` | ROI, threshold, หา centroid และตรวจ Green Node |
| `pid.py` | PID Controller |
| `signs.py` | ตรวจจับและจำแนกป้ายจราจร |
| `fsm.py` | State Machine ของภารกิจ |
| `viz.py` | วาด ROI, centroid, กรอบป้าย และ HUD ลงบนภาพ แล้วแสดงใน notebook หรือ stream ไปที่ `http://<IP>:8080` |
