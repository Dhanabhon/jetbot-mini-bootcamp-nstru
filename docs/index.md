---
title: หน้าแรก
nav_order: 1
---

# JetBot Mini Bootcamp @ NSTRU

คู่มือประกอบการอบรม **AI Vision Grand Prix** สอนเขียนโค้ดให้ Yahboom JetBot Mini เดินตามเส้นบนสนาม grid อ่านป้ายจราจร แล้วตัดสินใจเองที่ทางแยก

## เริ่มจากตรงไหน

| ถ้าคุณ... | ไปที่ |
| :--- | :--- |
| เพิ่งได้หุ่นยนต์ ยังไม่เคยต่อกับคอมพิวเตอร์ | [การเชื่อมต่อหุ่นยนต์](setup/index.md) |
| อยากรู้ว่าวันอบรมเรียนอะไรบ้าง | [ตารางอบรม](syllabus.md) |
| อยากรู้โจทย์และกติกาวันแข่ง | [กติกาการแข่งขัน](competition-rules.md) |
| ติดปัญหาระหว่างเขียนโค้ด | [Cheat sheet](cheatsheet.md) |

## สิ่งที่ต้องเตรียมมาวันอบรม

- Notebook คอมพิวเตอร์ (Windows หรือ macOS) ที่ต่อ Wi-Fi ได้
- **Google Chrome** ติดตั้งไว้ก่อน (Yahboom ระบุว่า Jupyter Lab ของหุ่นยนต์ใช้งานได้ดีกับ Chrome เท่านั้น) Wi-Fi ของห้องอบรมอาจไม่มี internet จึงควรติดตั้งและดาวน์โหลดทุกอย่างมาก่อน
- สาย micro USB ที่ส่งข้อมูลได้ (สายชาร์จอย่างเดียวใช้ไม่ได้) ถ้าคอมพิวเตอร์มีแต่ช่อง USB-C ให้เตรียมสาย USB-C to micro USB หรือหัวแปลงที่ส่งข้อมูลได้

## ตรวจคอมพิวเตอร์ก่อนวันอบรม

{% include os-switch.html %}

<div data-os="windows" markdown="1">

1. กด `Win + X` แล้วเลือก **Terminal** หรือ **Windows PowerShell**
2. พิมพ์ `ssh` แล้วกด Enter
3. ถ้าขึ้นวิธีใช้ที่ขึ้นต้นด้วย `usage: ssh` แปลว่าพร้อมแล้ว ถ้าขึ้นว่า *is not recognized* ให้ติดตั้ง OpenSSH Client ตาม[แก้ปัญหาการเชื่อมต่อ](setup/troubleshooting.md#windows-ssh-missing) ก่อนวันอบรม (ต้องต่อ internet)

</div>

<div data-os="mac" markdown="1">

1. เปิด **Terminal** (กด `Cmd + Space` แล้วพิมพ์ Terminal)
2. พิมพ์ `ssh` แล้วกด Enter
3. ถ้าขึ้นวิธีใช้ที่ขึ้นต้นด้วย `usage: ssh` แปลว่าพร้อมแล้ว macOS มี SSH ติดมาทุกเครื่อง

</div>
