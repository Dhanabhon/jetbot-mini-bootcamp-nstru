# jetbot_nstru

โค้ด Python ที่ใช้ร่วมกันหลาย notebook เพื่อไม่ต้อง copy ซ้ำ เมื่อผู้เข้าอบรมเขียนส่วนไหนเสร็จใน module ก่อนหน้า module ถัดไปจะ import จากที่นี่

| ไฟล์ | หน้าที่ |
| :--- | :--- |
| `hardware.py` | เปิดรถ กล้อง CSI จอ OLED Buzzer และอ่านแรงดันแบต (ค่าที่ติด `VERIFY ON ROBOT` ต้องทดสอบกับรถจริง) |
| `params.py` | โหลดและบันทึกค่าเฉพาะรถแต่ละคันลง `my_params.json` |
| `line.py` | ROI, threshold, หา centroid และตรวจ Green Node |
| `pid.py` | PID Controller, motor trim, Dynamic Speed และชดเชยแบตเตอรี่ |
| `signs.py` | ตรวจจับและจำแนกป้ายจราจร |
| `fsm.py` | State Machine ของภารกิจ เป็น pure function ทดสอบได้โดยไม่ต้องมีรถ |
| `viz.py` | วาด ROI, centroid, กรอบป้าย และ HUD ลงบนภาพ แล้วแสดงใน notebook หรือ stream ไปที่ `http://<IP>:8080` |

ทุกไฟล์เขียนให้รันบน Python 3.6 (JetPack 4) ได้ และมี test ใน `tests/` รันด้วย `python3 -m pytest tests -q`
