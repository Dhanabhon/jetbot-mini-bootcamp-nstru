---
title: แก้ปัญหาการเชื่อมต่อ
parent: เอกสารอ้างอิง
nav_order: 2
---

# แก้ปัญหาการเชื่อมต่อ

## เปิดเครื่องแล้วไม่มีสัญญาณ boot

- รอให้ครบ 2–3 นาทีก่อน
- ตรวจว่า SD card (รุ่น 2GB) หรือ USB drive (รุ่น 4GB) เสียบแน่น
- ตรวจระดับแบตเตอรี่ แล้วปิดเปิดเครื่องใหม่

## Buzzer ดังไม่หยุด และจอ HDMI ค้างที่โลโก้ NVIDIA หรือขึ้น `bash: no job control in this shell`
{: #boot-root-not-found }

**อาการ:** Buzzer ดังไม่หยุด จอ OLED ว่าง ถ้าต่อจอ HDMI จะเห็นค้างที่โลโก้ NVIDIA หรือขึ้นข้อความ `bash: no job control in this shell` ตามด้วย prompt `bash-4.3#`

**สาเหตุ:** kernel ทำงานแล้ว แต่หา root filesystem ซึ่งเป็นที่อยู่ของระบบหลักไม่เจอ จึงหยุดอยู่ที่ shell สำรองของ initrd และไม่ได้เข้าสู่ Ubuntu โปรแกรมที่สั่งให้ Buzzer หยุดและแสดง IP บน OLED จึงไม่ได้ทำงาน หุ่นยนต์รุ่น 4GB ตั้งค่าให้ระบบหลักอยู่บน USB drive (`root=/dev/sda1`) อาการนี้จึงเกิดเมื่อ USB drive หลุด ไม่ได้เสียบ หรือเสีย

**ผู้เข้าอบรมทำได้:** ปิดสวิตช์ เสียบ USB drive ให้แน่นที่ช่อง USB-A แล้วเปิดเครื่องใหม่ ถ้ายังไม่หาย ให้เรียกทีมงาน

### สำหรับทีมงาน: หาสาเหตุจาก shell `bash-4.3#`

ต่อจอ HDMI และคีย์บอร์ด USB แล้วพิมพ์

```bash
cat /proc/cmdline
ls /dev/sd* /dev/mmcblk*
```

- `root=` ตัว**สุดท้าย**ใน `/proc/cmdline` คือที่ที่ kernel ใช้หา root filesystem
- ไม่มี `/dev/sda1`: ระบบไม่เห็น USB drive
- ข้อความเหนือ prompt มี `critical medium error, dev sda` หรือ `can't read superblock`: USB drive เสียทางฮาร์ดแวร์ ให้เปลี่ยนตัวใหม่แล้วเขียน image ของ Yahboom ลงไป
- ข้อความ `imx219 ... board setup failed` ไม่ได้ทำให้ boot ไม่ผ่าน ข้อความนี้แปลว่ากล้องไม่ตอบ ให้ตรวจสายแพกล้องทีหลัง

### สำหรับทีมงาน: boot จาก SD card แทน USB drive ที่เสีย

ใช้ได้เมื่อ SD card (`mmcblk0p1`) มีระบบครบอยู่แล้ว ตรวจก่อนว่า `/mnt/home` มีโฟลเดอร์ `jetson` และ `df` แสดงว่าใช้พื้นที่ไปหลาย GB

```bash
mount /dev/mmcblk0p1 /mnt
ls /mnt/home && df -h /mnt
cp /mnt/boot/extlinux/extlinux.conf /mnt/boot/extlinux/extlinux.conf.bak
sed -i 's#root=/dev/sda1#root=/dev/mmcblk0p1#' /mnt/boot/extlinux/extlinux.conf
grep root= /mnt/boot/extlinux/extlinux.conf
umount /mnt
```

ก่อนพิมพ์ `umount` ตรวจผลของ `grep` ให้แน่ว่าเป็น `root=/dev/mmcblk0p1` ตัวสะกด **mmc** ผิดเพียงตัวเดียวก็ boot ไม่ผ่าน จากนั้นถอด USB drive ที่เสียออกแล้วปิดเปิดสวิตช์

- shell นี้ไม่มีคำสั่ง `sync` และ `clear` ไม่ต้องกังวล เพราะ `umount` จะเขียนข้อมูลที่ค้างอยู่ลง SD card ให้เอง ระวังพิมพ์เป็น `unmount` ที่ถูกคือ `umount`
- อย่าพิมพ์ `exit` ใน shell นี้ จะทำให้ kernel panic
- ถ้าต้องย้อนกลับ ให้ `cp` ไฟล์ `extlinux.conf.bak` ทับไฟล์เดิม

## boot เสร็จแล้ว (Buzzer ดัง 3 ครั้ง) แต่จอ OLED ว่าง
{: #oled-blank }

**สาเหตุที่พบบ่อย:** ไม่มี Wi-Fi interface `wlan0` เช่น ถอด USB Wi-Fi dongle ออก โปรแกรม `jetbotmini_stats` ที่แสดง IP บน OLED จะ crash แล้วเปิดใหม่วนไปเรื่อยๆ จอจึงว่าง ทั้งที่จอปกติ

**ผู้เข้าอบรมทำได้:** ตรวจว่า USB Wi-Fi dongle เสียบอยู่ ภายในไม่กี่วินาทีหลังเสียบ OLED ควรแสดงข้อมูล ไม่ต้องรีสตาร์ตเครื่อง

**สำหรับทีมงาน:** ถ้ายังว่าง ให้ตรวจตามลำดับ

```bash
ip link show wlan0
journalctl -u jetbotmini_stats -n 30 --no-pager
i2cdetect -y -r 0
```

- `ip link` ขึ้น `Device "wlan0" does not exist`: ระบบไม่เห็น Wi-Fi ให้ตรวจ dongle หรือการ์ด M.2
- log ขึ้น `cat /sys/class/net/wlan0/operstate: No such file or directory`: เป็นสาเหตุเดียวกัน คือไม่มี `wlan0`
- `i2cdetect -y -r 0` ไม่มี `3c` ในตาราง: บอร์ดมองไม่เห็นจอ OLED ให้ปิดเครื่องแล้วตรวจสาย 4 เส้นที่ช่อง OLED จอ OLED อยู่บน I2C bus **0** ส่วน `1b` บน bus 1 คือ chip บนบอร์ดขยาย

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
