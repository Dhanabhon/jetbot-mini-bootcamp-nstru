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

- สายเป็นสายชาร์จอย่างเดียวหรือเปล่า ลองเปลี่ยนสาย
- เปิดหุ่นยนต์ก่อนเสียบสายหรือเปล่า ถ้าไม่ ให้ถอดสาย รอ boot เสร็จ แล้วเสียบใหม่
- ลองเปลี่ยนช่อง USB ของคอมพิวเตอร์ และเสียบตรง ไม่ผ่าน hub
- **Windows:** เปิด Device Manager ดูหัวข้อ Network adapters ควรมีอุปกรณ์ชื่อประมาณ *Remote NDIS Compatible Device* ถ้าขึ้นเครื่องหมายตกใจสีเหลือง ให้คลิกขวาแล้วเลือก Update driver
- **macOS:** เปิด System Settings > Network ควรมี interface ใหม่ของ Jetson ปรากฏขึ้น

## `ssh` ขึ้น Connection timed out หรือ Connection refused

- ผ่าน USB: ตรวจว่าเห็น drive `L4T-README` แล้ว และใช้ IP `192.168.55.1`
- ผ่าน Wi-Fi: คอมพิวเตอร์กับหุ่นยนต์อยู่ Wi-Fi วงเดียวกันหรือไม่ และ IP ตรงกับจอ OLED ล่าสุดหรือไม่ (IP เปลี่ยนได้เมื่อเปิดเครื่องใหม่)
- ลอง `ping 192.168.55.1` หรือ `ping <IP>` ถ้า ping ไม่ผ่าน ปัญหาอยู่ที่เครือข่าย ไม่ใช่ SSH

## `ssh` ขึ้น REMOTE HOST IDENTIFICATION HAS CHANGED

เกิดเมื่อเคยต่อหุ่นยนต์ตัวอื่นที่ใช้ IP เดียวกันมาก่อน (เจอบ่อยกับ `192.168.55.1` เมื่อสลับหุ่นยนต์) ให้ลบค่าเก่าออก แล้วต่อใหม่

```bash
ssh-keygen -R 192.168.55.1
```

## ต่อ Wi-Fi ไม่สำเร็จ

- ชื่อ Wi-Fi และรหัสผ่านพิมพ์ถูกต้องตามตัวพิมพ์เล็กใหญ่หรือไม่
- สั่ง `nmcli dev wifi` ดูว่าหุ่นยนต์มองเห็น Wi-Fi นั้นหรือไม่ ถ้าไม่เห็น ลองขยับเข้าใกล้ router
- Wi-Fi ที่ต้อง login ผ่านหน้าเว็บ (เช่น Wi-Fi ของมหาวิทยาลัย) ใช้กับหุ่นยนต์ไม่ได้ ให้ใช้ router ของห้องอบรม

## เปิด `http://<IP>:8888` ไม่ขึ้น

- ใช้ Google Chrome และพิมพ์ `http://` ไม่ใช่ `https://`
- ตรวจ IP กับจอ OLED อีกครั้ง
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
