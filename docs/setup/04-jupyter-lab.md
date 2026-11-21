---
title: 4. เข้า Jupyter Lab
parent: การเชื่อมต่อหุ่นยนต์
nav_order: 4
---

# ขั้นที่ 4: เข้า Jupyter Lab และเตรียมพร้อมเขียนโค้ด

## เปิด Jupyter Lab

1. เปิด **Google Chrome** (Yahboom ระบุว่า browser อื่นใช้งานได้ไม่ดี หรือ login ไม่ได้)
2. พิมพ์ที่ address bar โดยใช้ IP จากจอ OLED

   ```text
   http://192.168.1.196:8888
   ```

3. ใส่ password `yahboom`

ถ้ายังต่อสาย USB อยู่ ใช้ `http://192.168.55.1:8888` แทนได้

## ปิดโปรแกรม APP ของ Yahboom ก่อนเขียนโค้ด

image ของ Yahboom เปิดโปรแกรมควบคุมผ่าน APP มือถือไว้ตั้งแต่ boot โปรแกรมนี้ใช้มอเตอร์และกล้องอยู่ ถ้าไม่ปิด โค้ดของเราจะแย่งอุปกรณ์กับมันและทำงานผิดปกติ

เปิด Terminal ใน Jupyter Lab (เมนู **File > New > Terminal**) แล้วสั่ง

```bash
sudo systemctl stop jetbotmini_start
```

คำสั่งนี้ปิดเฉพาะรอบนี้ เปิดเครื่องใหม่โปรแกรมจะกลับมา ถ้าต้องการปิดถาวรตลอดช่วงอบรม ให้สั่ง

```bash
sudo systemctl disable jetbotmini_start
```

เปิดกลับคืนภายหลังได้ด้วย `sudo systemctl enable jetbotmini_start`

### เมื่อโค้ดของเราต้องเขียนจอ OLED เอง

จอ OLED มีโปรแกรมอีกตัวคอยแสดง IP อยู่ ถ้าโค้ดของเราจะเขียนข้อความลงจอ (เช่น แสดงชื่อป้ายใน Module 6) ต้องปิดตัวนี้ก่อน

```bash
sudo systemctl stop jetbotmini_stats
```

หลังปิดแล้วจอจะไม่แสดง IP อีก ให้จด IP ไว้ก่อนสั่ง

## ตรวจ power mode

Jetson Nano มี 2 โหมด: `MAXN` ใช้ CPU ครบ 4 core ส่วน `5W` ใช้แค่ 2 core และช้ากว่ามาก งาน vision ของเราควรใช้ `MAXN`

```bash
sudo nvpmodel -q        # ดูโหมดปัจจุบัน
sudo nvpmodel -m0       # เปลี่ยนเป็น MAXN
```

## นำโค้ดของ bootcamp ลงหุ่นยนต์

ใน Terminal ของ Jupyter Lab

```bash
cd ~
git clone https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru.git
```

จากนั้นเปิด folder `jetbot-mini-bootcamp-nstru/notebooks` จากแถบด้านซ้าย แล้วเริ่มที่ `01_setup_first_trial.ipynb`

หุ่นยนต์ต้องออก internet ได้จึงจะ clone ได้ ถ้า Wi-Fi ห้องอบรมไม่มี internet ให้ใช้วิธีส่งไฟล์ด้านล่าง

## ส่งไฟล์ระหว่างคอมพิวเตอร์กับหุ่นยนต์

- **ลากวางใน Jupyter Lab:** ลากไฟล์จากคอมพิวเตอร์ไปวางที่แถบไฟล์ด้านซ้าย ง่ายที่สุดสำหรับไฟล์ไม่กี่ไฟล์
- **Windows:** ใช้ [WinSCP](https://winscp.net) ตั้ง Host เป็น IP ของหุ่นยนต์ Port `22` Username `jetson` Password `yahboom` แล้วลากไฟล์ข้ามฝั่งได้ อย่าแก้ไฟล์โค้ดใน WinSCP โดยตรง เพราะ encoding และ indent อาจเพี้ยน
- **macOS หรือ PowerShell:** ใช้คำสั่ง `scp`

  ```bash
  scp ไฟล์ของฉัน.py jetson@192.168.1.196:~/
  ```
