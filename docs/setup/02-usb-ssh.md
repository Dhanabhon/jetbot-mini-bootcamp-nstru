---
title: "ทางสำรอง: SSH"
parent: การเชื่อมต่อหุ่นยนต์
nav_order: 11
---

# ทางสำรอง: SSH เข้าหุ่นยนต์

ระหว่างอบรมใช้ Terminal ใน Jupyter Lab แทน SSH ได้ทุกอย่าง หน้านี้ใช้เมื่อเปิด Jupyter Lab ไม่ได้

## SSH ผ่าน Wi-Fi ของหุ่นยนต์

ถ้าคอมพิวเตอร์ต่อ Wi-Fi `JETBOT-NN` อยู่ แต่หน้า Jupyter Lab ไม่ขึ้น ให้ SSH ไปที่ `10.42.0.1` ด้วยวิธีเดียวกับหัวข้อ SSH ด้านล่าง แค่เปลี่ยน IP

```bash
ssh jetson@10.42.0.1
```

หุ่นยนต์ทุกตัวใช้ IP นี้เหมือนกัน ถ้าเคยต่อหุ่นยนต์ตัวอื่นมาก่อนแล้วขึ้น `REMOTE HOST IDENTIFICATION HAS CHANGED` ให้แก้ตาม[แก้ปัญหาการเชื่อมต่อ](troubleshooting.md#host-key-changed)

## SSH ผ่านสาย USB

วิธีนี้เรียกว่า **headless mode** คอมพิวเตอร์คุยกับหุ่นยนต์ผ่านสาย USB โดยตรง ไม่ต้องมี Wi-Fi จอ หรือคีย์บอร์ด และ IP ของหุ่นยนต์เป็น `192.168.55.1` เสมอ

### ต่อสาย

1. **เปิดสวิตช์หุ่นยนต์ก่อน** แล้วรอจน boot เสร็จ (Buzzer ดัง 3 ครั้ง)
2. เสียบสาย micro USB ที่ช่องบนบอร์ด Jetson Nano อีกด้านเสียบคอมพิวเตอร์ ถ้าคอมพิวเตอร์มีแต่ช่อง USB-C ให้ใช้สาย USB-C to micro USB ที่ส่งข้อมูลได้ หรือหัวแปลง
3. รอสักครู่ แล้วตรวจว่าคอมพิวเตอร์เห็นหุ่นยนต์

<div data-os="windows" markdown="1">

**Windows:** File Explorer จะมี drive ใหม่ชื่อประมาณ `L4T-README` และ Device Manager แสดงอุปกรณ์ *Linux File-Stor Gadget USB Device* แปลว่าต่อสำเร็จ

</div>

<div data-os="mac" markdown="1">

**macOS:** drive ชื่อ `L4T-README` จะขึ้นบน Desktop และแถบซ้ายของ Finder แปลว่าต่อสำเร็จ

Mac ที่ใช้ชิป Apple (M1 ขึ้นไป) อาจขึ้นหน้าต่าง **Allow accessory to connect?** ให้กด **Allow** ถ้าเผลอกด Don't Allow ให้ดูวิธีแก้ใน[แก้ปัญหาการเชื่อมต่อ](troubleshooting.md#usb-not-detected)

</div>

ลำดับสำคัญ: ต้องเปิดหุ่นยนต์ก่อนเสียบสาย และสายต้องเป็นสายที่ส่งข้อมูลได้

<div data-os="windows" markdown="1">

## SSH บน Windows

Windows 10 และ 11 มี SSH ติดมาในเครื่องแล้ว ไม่ต้องลงโปรแกรมเพิ่ม

1. กด `Win + X` แล้วเลือก **Terminal** หรือ **Windows PowerShell**
2. พิมพ์คำสั่ง

   ```powershell
   ssh jetson@192.168.55.1
   ```

3. ครั้งแรกจะถามว่า `Are you sure you want to continue connecting` ให้พิมพ์ `yes`
4. ใส่ password `yahboom` (ระหว่างพิมพ์จะไม่มีตัวอักษรขึ้น เป็นเรื่องปกติ)

เมื่อเห็น prompt ขึ้นต้นด้วย `jetson@` แปลว่าเข้าหุ่นยนต์ได้แล้ว

- **วางคำสั่งที่ copy มา:** กด `Ctrl + V` หรือคลิกขวาในหน้าต่าง Terminal
- **ขึ้นว่า `ssh` is not recognized:** เครื่องยังไม่มี OpenSSH Client ให้ติดตั้งตาม[แก้ปัญหาการเชื่อมต่อ](troubleshooting.md#windows-ssh-missing) หรือใช้ PuTTY ด้านล่างแทน

### ถ้าอยากใช้โปรแกรมแบบมีหน้าต่าง

Yahboom แนะนำ PuTTY หรือ Xshell ตั้งค่าดังนี้

| ช่อง | ค่า |
| :--- | :--- |
| Host Name | `192.168.55.1` |
| Port | `22` |
| Connection type | SSH |
| Username / Password | `jetson` / `yahboom` |

</div>

<div data-os="mac" markdown="1">

## SSH บน macOS

macOS มี SSH ติดมาในเครื่องแล้ว ไม่ต้องลงโปรแกรมเพิ่ม

1. เปิด **Terminal** (กด `Cmd + Space` แล้วพิมพ์ Terminal หรือเปิดจาก Applications > Utilities)
2. พิมพ์คำสั่ง

   ```bash
   ssh jetson@192.168.55.1
   ```

3. ครั้งแรกจะถามว่า `Are you sure you want to continue connecting` ให้พิมพ์ `yes`
4. ใส่ password `yahboom` (ระหว่างพิมพ์จะไม่มีตัวอักษรขึ้น เป็นเรื่องปกติ)

เมื่อเห็น prompt ขึ้นต้นด้วย `jetson@` แปลว่าเข้าหุ่นยนต์ได้แล้ว

- **วางคำสั่งที่ copy มา:** กด `Cmd + V`
- **หยุดคำสั่งที่ค้างอยู่:** กด `Control + C` (ปุ่ม Control ไม่ใช่ Cmd)

</div>

## ตรวจว่าใช้งานได้

ลองสั่งคำสั่งนี้ในหุ่นยนต์ ควรได้ชื่อเครื่องกลับมา

```bash
hostname
```

ใช้เสร็จแล้วพิมพ์ `exit` เพื่อออกจากหุ่นยนต์ กลับมาที่คอมพิวเตอร์ของเรา
