---
title: 1. ใช้งาน Jupyter Lab
parent: การเชื่อมต่อหุ่นยนต์
nav_order: 1
---

# ขั้นที่ 1: ใช้งาน Jupyter Lab

ทุกอย่างที่ต้องทำกับหุ่นยนต์ระหว่างอบรมทำใน Jupyter Lab ได้หมด ทั้งเขียนโค้ด สั่งคำสั่งใน Terminal ส่งไฟล์ และปิดเครื่อง ไม่ต้องใช้ SSH

## เปิด Jupyter Lab

1. ต่อคอมพิวเตอร์เข้า Wi-Fi ของหุ่นยนต์ตัวเอง ชื่อตามบรรทัดแรกของจอ OLED เช่น `JETBOT-07`
2. เปิด **Google Chrome** (Yahboom ระบุว่า browser อื่นใช้งานได้ไม่ดี หรือ login ไม่ได้) แล้วพิมพ์ที่ address bar

   ```text
   http://10.42.0.1:8888
   ```

3. ใส่ password `yahboom`

ถ้าต่อสาย USB ตาม[ทางสำรอง](02-usb-ssh.md)อยู่ ใช้ `http://192.168.55.1:8888` แทนได้

## เปิด Terminal

เมนู **File > New > Terminal** จะได้ Terminal ของหุ่นยนต์ในแท็บใหม่ ใช้สั่งคำสั่ง Linux ได้เหมือน SSH ทุกอย่าง คำสั่งที่ขึ้นต้นด้วย `sudo` จะถาม password ให้ใส่ `yahboom`

## เมื่อโค้ดของเราต้องเขียนจอ OLED เอง

จอ OLED มีโปรแกรมอีกตัวคอยแสดงชื่อ Wi-Fi และ IP อยู่ ถ้าโค้ดของเราจะเขียนข้อความลงจอ (เช่น แสดงชื่อป้ายใน Module 6) ต้องปิดตัวนี้ก่อน

```bash
sudo systemctl stop nstru_status jetbotmini_stats
```

`nstru_status` คือตัวที่โปรแกรมตั้งค่าติดตั้งให้ ส่วน `jetbotmini_stats` คือตัวเดิมของ Yahboom สั่งปิดพร้อมกันได้เลย ตัวที่ไม่มีในเครื่องจะขึ้น `not loaded` ซึ่งไม่เป็นไร

หลังปิดแล้วจอจะไม่แสดงชื่อ Wi-Fi และรหัสอีก คอมพิวเตอร์ที่ต่ออยู่แล้วใช้งานต่อได้ตามปกติ ตัวแสดงผลจะกลับมาเองเมื่อเปิดเครื่องใหม่

## ตรวจ power mode

Jetson Nano มี 2 โหมด: `MAXN` ใช้ CPU ครบ 4 core ส่วน `5W` ใช้แค่ 2 core และช้ากว่ามาก งาน vision ของเราควรใช้ `MAXN` ขั้นที่ 6 ของโปรแกรมตั้งค่าตั้งให้แล้ว คำสั่งด้านล่างใช้ตรวจซ้ำ

```bash
sudo nvpmodel -q        # ดูโหมดปัจจุบัน
sudo nvpmodel -m0       # เปลี่ยนเป็น MAXN
```

## เปิดโค้ดของ bootcamp

ทีมงานคัดลอกโค้ดลงหุ่นยนต์ทุกตัวไว้แล้วที่ `~/jetbot-mini-bootcamp-nstru` ไม่ต้องดาวน์โหลดเพิ่ม และไม่ต้องใช้ internet

1. แถบไฟล์ด้านซ้ายของ Jupyter Lab เปิดที่ folder นี้ให้แล้ว ดับเบิลคลิกเข้า `notebooks`
2. เปิด notebook ตาม Module ที่บรรยายอยู่ เริ่มที่ `01_setup_first_trial.ipynb`

ถ้าไม่เห็น folder นี้ ให้แจ้งทีมงาน

### แก้ notebook จนเสีย อยากเริ่มใหม่

เปิด Terminal ใน Jupyter Lab แล้วสั่งคำสั่งนี้ (เปลี่ยนชื่อไฟล์ให้ตรงกับ notebook ที่ต้องการ) notebook จะกลับเป็นฉบับเริ่มต้น **ทุกอย่างที่แก้ไว้ในไฟล์นั้นจะหายหมด**

```bash
cd ~/jetbot-mini-bootcamp-nstru
git checkout -- notebooks/01_setup_first_trial.ipynb
```

ปิด notebook นั้นใน Jupyter Lab ก่อนสั่ง แล้วเปิดใหม่หลังสั่ง ไม่อย่างนั้น Jupyter อาจบันทึกฉบับเก่าทับ

## ปิดเครื่อง

สั่งใน Terminal ของ Jupyter Lab แล้วรอจนไฟบนบอร์ด Jetson Nano ดับ จึงค่อยปิดสวิตช์ power หน้า Jupyter Lab จะหลุดไป เป็นเรื่องปกติ

```bash
sudo shutdown -h now
```

การปิดสวิตช์ทันทีโดยไม่ shutdown อาจทำให้กล้องเรียกใช้งานไม่ได้ในครั้งถัดไป

## ส่งไฟล์ระหว่างคอมพิวเตอร์กับหุ่นยนต์

**ลากวางใน Jupyter Lab** ง่ายที่สุดสำหรับไฟล์ไม่กี่ไฟล์ ลากไฟล์จากคอมพิวเตอร์ไปวางที่แถบไฟล์ด้านซ้าย ส่วนการเอาไฟล์จากหุ่นยนต์กลับมา ให้คลิกขวาที่ไฟล์แล้วเลือก **Download**

ถ้ามีไฟล์เยอะหรือทั้ง folder ใช้วิธีด้านล่าง ซึ่งใช้ SSH อยู่เบื้องหลัง คอมพิวเตอร์ต้องต่อ Wi-Fi ของหุ่นยนต์อยู่

<div data-os="windows" markdown="1">

### Windows: WinSCP

ใช้ [WinSCP](https://winscp.net) (ฟรี) ตั้งค่าดังนี้ แล้วลากไฟล์ข้ามฝั่งได้

| ช่อง | ค่า |
| :--- | :--- |
| File protocol | SFTP |
| Host name | `10.42.0.1` |
| Port number | `22` |
| User name / Password | `jetson` / `yahboom` |

อย่าแก้ไฟล์โค้ดใน WinSCP โดยตรง เพราะ encoding และ indent อาจเพี้ยน

### Windows: คำสั่ง scp

ใช้ใน Terminal หรือ PowerShell ได้เลย สั่งจากคอมพิวเตอร์ ไม่ใช่จากใน SSH ของหุ่นยนต์

```powershell
# ส่งไฟล์ไปหุ่นยนต์ (ไฟล์อยู่ใน folder ที่ Terminal เปิดอยู่)
scp .\my_robot.py jetson@10.42.0.1:~/

# เอาไฟล์จากหุ่นยนต์มาไว้ที่ Downloads
scp jetson@10.42.0.1:~/my_robot.py $HOME\Downloads\
```

</div>

<div data-os="mac" markdown="1">

### macOS: คำสั่ง scp

สั่งใน Terminal ของคอมพิวเตอร์ ไม่ใช่จากใน SSH ของหุ่นยนต์

```bash
# ส่งไฟล์ไปหุ่นยนต์
scp my_robot.py jetson@10.42.0.1:~/

# เอาไฟล์จากหุ่นยนต์มาไว้ที่ Downloads
scp jetson@10.42.0.1:~/my_robot.py ~/Downloads/
```

พิมพ์ path ไม่ถูก ให้ลากไฟล์จาก Finder มาวางในหน้าต่าง Terminal ระบบจะใส่ path ให้เอง

### macOS: โปรแกรมแบบมีหน้าต่าง

ใช้ [Cyberduck](https://cyberduck.io) (ฟรี) กด **Open Connection** เลือก **SFTP** แล้วใส่ Server เป็น `10.42.0.1` Port `22` Username `jetson` Password `yahboom`

</div>
