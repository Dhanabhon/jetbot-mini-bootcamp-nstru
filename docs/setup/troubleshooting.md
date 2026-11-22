---
title: แก้ปัญหาการเชื่อมต่อ
parent: การเชื่อมต่อหุ่นยนต์
nav_order: 5
---

# แก้ปัญหาการเชื่อมต่อ

## เปิดเครื่องแล้วไม่มีสัญญาณ boot

- รอให้ครบ 2–3 นาทีก่อน
- ตรวจว่า SD card (รุ่น 2GB) หรือ USB drive (รุ่น 4GB) เสียบแน่น
- ตรวจระดับแบตเตอรี่ แล้วปิดเปิดเครื่องใหม่

## เสียบ USB แล้วคอมพิวเตอร์ไม่เห็นหุ่นยนต์
{: #usb-not-detected }

- สายเป็นสายชาร์จอย่างเดียวหรือเปล่า ลองเปลี่ยนสาย
- เปิดหุ่นยนต์ก่อนเสียบสายหรือเปล่า ถ้าไม่ ให้ถอดสาย รอ boot เสร็จ แล้วเสียบใหม่
- ลองเปลี่ยนช่อง USB ของคอมพิวเตอร์ และเสียบตรง ไม่ผ่าน hub

<div data-os="windows" markdown="1">

**Windows:** เปิด Device Manager (คลิกขวาที่ปุ่ม Start แล้วเลือก Device Manager) ดูหัวข้อ Network adapters ควรมีอุปกรณ์ชื่อประมาณ *Remote NDIS Compatible Device* ถ้าขึ้นเครื่องหมายตกใจสีเหลือง ให้คลิกขวาแล้วเลือก Update driver

</div>

<div data-os="mac" markdown="1">

**macOS:**

- เปิด System Settings > Network ควรมี interface ใหม่ของ Jetson ปรากฏขึ้น
- Mac ชิป Apple (M1 ขึ้นไป) ที่เคยกด **Don't Allow** ตอนเสียบสาย จะไม่เห็นหุ่นยนต์อีก ให้เปิด System Settings > Privacy & Security หาช่อง **Allow accessories to connect** แล้วตั้งเป็น *Ask for New Accessories* หรือ *Always* จากนั้นถอดสายแล้วเสียบใหม่ แล้วกด **Allow**
- Mac ที่มีแต่ช่อง USB-C ต้องใช้สายหรือหัวแปลงที่ส่งข้อมูลได้ หัวแปลงบางตัวจ่ายไฟได้อย่างเดียว

</div>

<div data-os="windows" markdown="1">

## Windows: ขึ้นว่า `ssh` is not recognized
{: #windows-ssh-missing }

Windows บางเครื่องยังไม่ได้ติดตั้ง OpenSSH Client ให้ติดตั้งเอง (ต้องต่อ internet)

1. เปิด **Settings**
   - Windows 11: System > Optional features
   - Windows 10: Apps > Optional features
2. กด **View features** (Windows 11) หรือ **Add a feature** (Windows 10) แล้วค้นหา `OpenSSH Client`
3. ติดตั้ง แล้วปิดเปิด Terminal ใหม่

ถ้าติดตั้งไม่ได้ (เช่น เครื่องของหน่วยงานที่ถูกล็อกไว้) ให้ใช้ [PuTTY](https://www.putty.org) แทน ตั้งค่าตาม[ขั้นที่ 2](02-usb-ssh.md)

</div>

## `ssh` ขึ้น Connection timed out หรือ Connection refused

- ผ่าน USB: ตรวจว่าเห็น drive `L4T-README` แล้ว และใช้ IP `192.168.55.1`
- ผ่าน Wi-Fi: คอมพิวเตอร์ต่อ Wi-Fi ของห้องอบรมอยู่จริงหรือไม่ (บางเครื่องสลับไป Wi-Fi อื่นเอง ดู[ขั้นที่ 3](03-wifi.md)) และ IP ตรงกับสติ๊กเกอร์หรือจอ OLED หรือไม่
- ลอง `ping 192.168.55.1` หรือ `ping <IP>` ถ้า ping ไม่ผ่าน ปัญหาอยู่ที่เครือข่าย ไม่ใช่ SSH
  <span data-os="mac">(บน macOS ping จะทำงานไปเรื่อยๆ กด `Control + C` เพื่อหยุด)</span>

## `ssh` ขึ้น REMOTE HOST IDENTIFICATION HAS CHANGED

เกิดเมื่อเคยต่อหุ่นยนต์ตัวอื่นที่ใช้ IP เดียวกันมาก่อน (เจอบ่อยกับ `192.168.55.1` เมื่อสลับหุ่นยนต์) ให้ลบค่าเก่าออก แล้วต่อใหม่

```bash
ssh-keygen -R 192.168.55.1
```

คำสั่งนี้ใช้ได้ทั้งใน Terminal ของ macOS และ PowerShell ของ Windows ถ้าเป็นหุ่นยนต์ผ่าน Wi-Fi ให้เปลี่ยน `192.168.55.1` เป็น IP ของหุ่นยนต์ตัวนั้น

## คอมพิวเตอร์ต่อ Wi-Fi ของห้องแล้ว แต่ต่อหุ่นยนต์ไม่ได้

- ดูว่าหุ่นยนต์ได้ IP ตรงกับสติ๊กเกอร์หรือไม่ ถ้าจอ OLED ไม่แสดง IP หรือแสดง IP วงอื่น แปลว่าหุ่นยนต์ไม่ได้ต่อ Wi-Fi ของห้อง ให้ต่อสาย USB แล้วตั้งใหม่ตาม[ขั้นที่ 3](03-wifi.md#robot-wifi)
- ถ้าทุกทีมต่อหุ่นยนต์ไม่ได้พร้อมกัน router อาจเปิด AP isolation หรือให้ต่อผ่าน Guest network อยู่ แจ้งทีมงานให้ตรวจตาม[คู่มือผู้สอน](../instructor-guide.md#network)

## หุ่นยนต์ต่อ Wi-Fi ไม่สำเร็จ

- ชื่อ Wi-Fi และรหัสผ่านพิมพ์ถูกต้องตามตัวพิมพ์เล็กใหญ่หรือไม่
- สั่ง `nmcli dev wifi` ดูว่าหุ่นยนต์มองเห็น Wi-Fi นั้นหรือไม่ ถ้าไม่เห็น ลองขยับเข้าใกล้ router
- Wi-Fi ที่ต้อง login ผ่านหน้าเว็บ (เช่น Wi-Fi ของมหาวิทยาลัย) ใช้กับหุ่นยนต์ไม่ได้ ให้ใช้ router ของห้องอบรม

## เปิด `http://<IP>:8888` ไม่ขึ้น

- ใช้ Google Chrome และพิมพ์ `http://` ไม่ใช่ `https://`
- ตรวจ IP กับสติ๊กเกอร์หรือจอ OLED อีกครั้ง
- restart Jupyter Lab ผ่าน SSH

  ```bash
  sudo systemctl restart jetbotmini_jupyter
  ```

## กล้องไม่มีภาพ หรือภาพกะพริบใน Jupyter Lab

มักเกิดหลังปิดเครื่องโดยไม่ shutdown หรือมี notebook อื่นใช้กล้องค้างอยู่

1. ปิด notebook อื่นที่ใช้กล้อง (คลิกขวาที่ notebook แล้วเลือก Shut Down Kernel)
2. ถ้ายังไม่หาย ให้ restart Jupyter Lab แล้ว refresh หน้าเว็บ

   ```bash
   sudo systemctl stop jetbotmini_jupyter
   sudo systemctl start jetbotmini_jupyter
   ```

## สั่งมอเตอร์แล้วรถไม่วิ่ง หรือวิ่งเอง

โปรแกรม APP ของ Yahboom อาจยังทำงานอยู่ ให้ปิดตาม[ขั้นที่ 4](04-jupyter-lab.md)

```bash
sudo systemctl stop jetbotmini_start
```
