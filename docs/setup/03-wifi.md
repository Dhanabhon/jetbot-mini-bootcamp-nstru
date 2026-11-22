---
title: "ทางสำรอง: Wi-Fi"
parent: การเชื่อมต่อหุ่นยนต์
nav_order: 12
---

# ทางสำรอง: ปัญหา Wi-Fi และการต่อ Wi-Fi อื่น

ในห้องอบรม คอมพิวเตอร์ต่อ Wi-Fi ของหุ่นยนต์ตัวเองตาม[ขั้นที่ 0](00-first-setup.md) หน้านี้ใช้เมื่อคอมพิวเตอร์หลุดจาก Wi-Fi นั้น หรือจะนำหุ่นยนต์ไปต่อ Wi-Fi ที่อื่น

## ถ้าคอมพิวเตอร์สลับไป Wi-Fi อื่นเอง
{: #auto-switch }

คอมพิวเตอร์บางเครื่องเห็นว่า Wi-Fi ของหุ่นยนต์ไม่มี internet แล้วย้ายไป Wi-Fi อื่นที่เคยต่อไว้ ทำให้ต่อหุ่นยนต์ไม่ได้ ให้ปิดการต่ออัตโนมัติของ Wi-Fi อื่นนั้นไว้ระหว่างอบรม

<div data-os="windows" markdown="1">

**Windows:** Settings > Network & internet > Wi-Fi > **Manage known networks** เลือก Wi-Fi อื่นนั้น แล้วปิด **Connect automatically when in range**

</div>

<div data-os="mac" markdown="1">

**macOS:** System Settings > Wi-Fi ในรายการ **Known Networks** กดปุ่ม `...` ท้าย Wi-Fi อื่นนั้น แล้วปิด **Auto-Join**

</div>

## ดู IP ของคอมพิวเตอร์

IP ของคอมพิวเตอร์ควรขึ้นต้นด้วยตัวเลข 3 ชุดแรกเหมือนหุ่นยนต์ ตอนต่อ Wi-Fi ของหุ่นยนต์ คอมพิวเตอร์ควรได้ `10.42.0.xxx` ถ้าไม่ตรง แปลว่าต่อ Wi-Fi อื่นอยู่

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

## ให้หุ่นยนต์ต่อ Wi-Fi อื่น
{: #robot-wifi }

ใช้เมื่อนำหุ่นยนต์ไปต่อ Wi-Fi ที่อื่น เช่น ที่บ้าน ทำใน Terminal ของ Jupyter Lab ได้ เมื่อสั่งข้อ 2 หุ่นยนต์จะปิด Wi-Fi ของตัวเอง หน้า Jupyter Lab จะหลุดไป ให้ต่อคอมพิวเตอร์เข้า Wi-Fi เดียวกับหุ่นยนต์ แล้วเปิด Jupyter Lab ด้วย IP ใหม่บนจอ OLED

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

เมื่อเปิดเครื่องใหม่ หุ่นยนต์จะกลับไปเปิด Wi-Fi ของตัวเองเสมอ ถ้าจะกลับทันทีโดยไม่ต้องเปิดเครื่องใหม่ ให้สั่ง

```bash
sudo nmcli con up nstru-hotspot
```

Wi-Fi ที่ต้อง login ผ่านหน้าเว็บ (เช่น Wi-Fi ของมหาวิทยาลัย) ใช้กับหุ่นยนต์ไม่ได้
