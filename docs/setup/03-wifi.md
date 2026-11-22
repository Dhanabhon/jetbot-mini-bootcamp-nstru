---
title: 3. ต่อ Wi-Fi
parent: การเชื่อมต่อหุ่นยนต์
nav_order: 3
---

# ขั้นที่ 3: ต่อ Wi-Fi ของห้องอบรม

ห้องอบรมใช้ router ที่ทีมงานนำมาตั้งไว้ หุ่นยนต์ทุกตัวต่อ Wi-Fi นี้ไว้ให้แล้ว และมีสติ๊กเกอร์บอก IP ที่ตัวรถ ผู้เข้าอบรมแค่ต่อคอมพิวเตอร์เข้า Wi-Fi เดียวกัน

## ต่อคอมพิวเตอร์เข้า Wi-Fi ของห้อง

1. ต่อ Wi-Fi ตามชื่อและรหัสผ่านที่ติดไว้หน้าห้อง
2. Wi-Fi นี้อาจไม่มี internet ระบบจะขึ้นว่า *No internet* หรือ *No Internet Connection* เป็นเรื่องปกติ ยังต่อหุ่นยนต์ได้ตามเดิม
3. ดู IP ของหุ่นยนต์จากสติ๊กเกอร์ที่ตัวรถ หรือจอ OLED
4. ถ้ายังต่อสาย USB จากขั้นที่ 2 อยู่ ให้พิมพ์ `exit` แล้ว**ถอดสาย USB**
5. SSH ด้วย IP ของหุ่นยนต์

   ```bash
   ssh jetson@192.168.0.101
   ```

ถ้าเข้าได้ แปลว่าพร้อมใช้งานแบบไร้สายแล้ว ครั้งต่อไปที่เปิดเครื่อง หุ่นยนต์จะต่อ Wi-Fi นี้เอง

### ถ้าคอมพิวเตอร์สลับไป Wi-Fi อื่นเอง

คอมพิวเตอร์บางเครื่องเห็นว่า Wi-Fi ของห้องไม่มี internet แล้วย้ายไป Wi-Fi อื่นที่เคยต่อไว้ ทำให้ต่อหุ่นยนต์ไม่ได้ ให้ปิดการต่ออัตโนมัติของ Wi-Fi อื่นนั้นไว้ระหว่างอบรม

<div data-os="windows" markdown="1">

**Windows:** Settings > Network & internet > Wi-Fi > **Manage known networks** เลือก Wi-Fi อื่นนั้น แล้วปิด **Connect automatically when in range**

</div>

<div data-os="mac" markdown="1">

**macOS:** System Settings > Wi-Fi ในรายการ **Known Networks** กดปุ่ม `...` ท้าย Wi-Fi อื่นนั้น แล้วปิด **Auto-Join**

</div>

### ดู IP ของคอมพิวเตอร์

โดยทั่วไป IP ของคอมพิวเตอร์ควรขึ้นต้นด้วยตัวเลข 3 ชุดแรกเหมือนหุ่นยนต์ เช่น หุ่นยนต์ได้ `192.168.0.101` คอมพิวเตอร์ควรได้ `192.168.0.xxx` ถ้าไม่ตรง แปลว่าอยู่คนละวง ให้เปลี่ยน Wi-Fi ของคอมพิวเตอร์

<div data-os="windows" markdown="1">

**Windows:** ใน Terminal หรือ PowerShell สั่ง

```powershell
ipconfig
```

ดูบรรทัด `IPv4 Address` ใต้หัวข้อ *Wireless LAN adapter Wi-Fi*

</div>

<div data-os="mac" markdown="1">

**macOS:** ใน Terminal สั่ง

```bash
ipconfig getifaddr en0
```

ถ้าไม่มีอะไรขึ้น (เกิดกับ Mac บางรุ่นที่ Wi-Fi ไม่ใช่ `en0`) ให้ดูที่ System Settings > Wi-Fi > กด **Details** ที่ชื่อ Wi-Fi ที่ต่ออยู่ > TCP/IP

</div>

## ตั้ง Wi-Fi ให้หุ่นยนต์เอง
{: #robot-wifi }

ใช้เมื่อนำหุ่นยนต์ไปต่อ Wi-Fi ที่อื่น เช่น ที่บ้าน หรือทีมงานยังไม่ได้ตั้งไว้ให้ ทำผ่าน SSH ทางสาย USB จาก[ขั้นที่ 2](02-usb-ssh.md)

1. ดูรายชื่อ Wi-Fi ที่หุ่นยนต์มองเห็น

   ```bash
   nmcli dev wifi
   ```

2. ต่อ Wi-Fi โดยแทน `ชื่อWiFi` และ `รหัสผ่าน` ด้วยค่าจริง

   ```bash
   sudo nmcli dev wifi connect ชื่อWiFi password รหัสผ่าน
   ```

   ถ้าชื่อ Wi-Fi มีช่องว่าง ให้ครอบด้วยเครื่องหมายคำพูด เช่น `"NSTRU Robot"`

3. ระบบจะถาม password ของ `sudo` ให้ใส่ `yahboom`
4. ถ้าสำเร็จจะขึ้นข้อความ `successfully activated`
5. ดู IP ใหม่ของหุ่นยนต์ที่จอ OLED หรือสั่ง `ifconfig wlan0` แล้วดูบรรทัด `inet` ใต้ `wlan0`

Wi-Fi ที่ต้อง login ผ่านหน้าเว็บ (เช่น Wi-Fi ของมหาวิทยาลัย) ใช้กับหุ่นยนต์ไม่ได้

ถัดไป: [ขั้นที่ 4 เข้า Jupyter Lab](04-jupyter-lab.md)
