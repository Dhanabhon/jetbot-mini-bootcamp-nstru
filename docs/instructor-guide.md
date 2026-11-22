---
title: คู่มือผู้สอน
nav_order: 6
---

# คู่มือผู้สอนและทีมจัดงาน

## สไลด์บรรยาย

- [ดาวน์โหลดสไลด์ (PDF)]({{ '/assets/slides/jetbot-mini-bootcamp-lecture.pdf' | relative_url }}) ไม่มี speaker notes ใช้แจกผู้เข้าอบรมหรือเปิดสำรองถ้าไม่มี internet
- ต้นฉบับพร้อม speaker notes อยู่ใน `slides/lecture-deck/` ของ repo วิธีแก้และสร้าง PDF ใหม่ดูใน `slides/README.md`

## ก่อนวันอบรม (Pre-flight)

- [ ] หุ่นยนต์ทั้ง 10 ตัว boot ได้ และเข้า Jupyter Lab ได้
- [ ] ติดสติ๊กเกอร์หมายเลขหุ่นยนต์ (01–10) ที่ตัวรถทุกตัว ไม่ต้องเขียน IP เพราะทุกตัวใช้ `10.42.0.1` ตาม[เครือข่ายในห้องอบรม](#network)
- [ ] เตรียมจอ HDMI คีย์บอร์ด และเมาส์ สำหรับ[ขั้นที่ 0](setup/00-first-setup.md) ถ้ามีไม่ครบทุกตัว ให้แบ่งผู้เข้าอบรมเป็นรอบ
- [ ] ตั้งค่าหุ่นยนต์ตัวสาธิตของผู้สอนครบทุกขั้นไว้ก่อน แล้วทดสอบเปิดหุ่นยนต์ที่ตั้งค่าแล้ว 3–4 ตัวพร้อมกัน แต่ละตัวต่อ notebook ของตัวเอง และเปิดภาพกล้องใน Jupyter ทุกตัว ภาพต้องไม่กระตุกจนใช้งานไม่ได้
- [ ] รัน `python3 tools/robot_setup.py --check-only` บนหุ่นยนต์ทุกตัว ตาม[โปรแกรมตั้งค่าหุ่นยนต์](#robot-setup) แล้วแก้ตัวที่ไม่ผ่านก่อนวันอบรม
- [ ] คัดลอกไฟล์รหัส hotspot ลงทุกตัวพร้อมกับ repo ตาม[ไฟล์รหัส hotspot](#hotspot-conf)
- [ ] เตรียมสาย micro USB ที่ส่งข้อมูลได้ อย่างน้อย 2–3 เส้นไว้แก้ปัญหา
- [ ] คัดลอก repo ลงทุกตัวด้วย flash drive ตาม[คัดลอก repo ลงหุ่นยนต์](#usb-copy) และรัน notebook 01–02 ผ่าน
- [ ] ทำ Motor Trim เบื้องต้นไว้ทุกตัว
- [ ] ชาร์จแบตเตอรี่เต็ม และมีแผนชาร์จช่วงพักเที่ยง
- [ ] รัน reference solution จบสนามได้ภายใน 90 วินาที
- [ ] พิมพ์เสาป้ายและสติ๊กเกอร์ครบ พร้อมชุดสำรอง
- [ ] พิมพ์กติกา 1 หน้าสำหรับแจกตอน Briefing
- [ ] บันทึกสไลด์ฉบับ PDF ลงเครื่องฉาย เพราะเครื่องฉายจะไม่มี internet ระหว่างต่อ Wi-Fi ของหุ่นยนต์ตัวสาธิต

## ก่อนวันแข่ง

- [ ] ชาร์จแบตเตอรี่เต็มทุกตัว และมีแบตเตอรี่หรือจุดชาร์จสำรอง
- [ ] แจ้งผู้เข้าอบรมให้นำหุ่นยนต์ สายชาร์จ และโค้ดล่าสุดมาในวันแข่ง
- [ ] มีหุ่นยนต์หรือ SD card image สำรอง เผื่อเครื่องที่นำกลับไปมีปัญหา
- [ ] สนามและสภาพแสงเหมือนวันอบรมมากที่สุด
- [ ] เตรียมแผนผังวางป้ายใน `competition/layouts/` และใบบันทึกคะแนน 20 ใบ (10 คน x 2 รอบ)
- [ ] เตรียมนาฬิกาจับเวลา และ sheet คำนวณ Net Time

## เครือข่ายในห้องอบรม
{: #network }

ห้องอบรมไม่ใช้ router หุ่นยนต์แต่ละตัวเปิด Wi-Fi ของตัวเองชื่อ `JETBOT-NN` (`NN` คือหมายเลขหุ่นยนต์) ที่อยู่ `10.42.0.1` และแจก IP `10.42.0.x` ให้คอมพิวเตอร์ที่ต่อเข้ามา ผู้เข้าอบรมแต่ละคนต่อ Wi-Fi ของหุ่นยนต์ตัวเองเท่านั้น ขั้นที่ 5 ของ[โปรแกรมตั้งค่า](#robot-setup)สร้าง Wi-Fi นี้ให้

แผนนี้แทนแผนเดิมที่ใช้ router กลาง เพราะ

- ไม่ต้องหา router ตั้ง DHCP reservation หรือเขียน IP บนสติ๊กเกอร์ ทุกคนเปิด `http://10.42.0.1:8888` เหมือนกัน
- หุ่นยนต์ 10 ตัวไม่ต้องส่งภาพกล้องผ่าน access point ตัวเดียวกัน โปรแกรมตั้งค่ากระจายหุ่นยนต์ไปตามช่อง 5 GHz ที่ไม่ต้องตรวจเรดาร์ 8 ช่อง (36, 40, 44, 48, 149, 153, 157, 161) ตามหมายเลข หุ่นยนต์หมายเลข 1 กับ 9 และ 2 กับ 10 จึงใช้ช่องเดียวกัน ถ้า dongle เปิด AP ที่ 5 GHz ไม่ได้ จะใช้ช่อง 1, 6, 11 แทน
- hotspot `jetbot-mini` เดิมของ Yahboom ที่ทุกตัวใช้ชื่อเดียวกันถูกปิดไปในขั้นเดียวกัน
- หุ่นยนต์จำ Wi-Fi อื่นที่เคยต่อไว้ประมาณ 20 ชื่อ แต่ `nstru-hotspot` ตั้ง `autoconnect-priority` ไว้ 100 เปิดเครื่องเมื่อไรจึงกลับมาเป็น hotspot เสมอ ทดสอบด้วยการ reboot บนหุ่นยนต์จริงแล้ว

รหัส Wi-Fi มาจาก[ไฟล์รหัส hotspot](#hotspot-conf) และแสดงบนจอ OLED บรรทัดที่ 2

### ข้อจำกัดที่ต้องบอกผู้เข้าอบรม

- **ระหว่างต่อ Wi-Fi ของหุ่นยนต์ คอมพิวเตอร์ใช้ internet ไม่ได้** ให้ติดตั้ง Google Chrome และเปิดเว็บคู่มือทิ้งไว้ก่อน เครื่องฉายของผู้สอนก็เช่นกัน ให้เปิดสไลด์จากไฟล์ PDF ในเครื่อง
- **ทุกตัวใช้ `10.42.0.1` เหมือนกัน** คันที่ควบคุมจึงขึ้นกับ Wi-Fi ที่คอมพิวเตอร์ต่ออยู่ ถ้าต่อผิดคันจะสั่งรถของคนอื่นวิ่ง ให้เทียบชื่อ Wi-Fi กับจอ OLED ทุกครั้ง
- **คอมพิวเตอร์ต้องเห็น Wi-Fi 5 GHz** เครื่องรุ่นเก่าบางเครื่องเห็นแค่ 2.4 GHz ดูวิธีย้ายหุ่นยนต์ตัวนั้นไป 2.4 GHz ด้านล่าง
- notebook บางเครื่องเห็นว่า Wi-Fi ไม่มี internet แล้วสลับไป Wi-Fi อื่นเอง วิธีแก้อยู่ใน[ทางสำรอง Wi-Fi](setup/03-wifi.md#auto-switch)
- SSH ไปที่ `10.42.0.1` จากเครื่องที่เคยต่อหุ่นยนต์ตัวอื่นมาก่อน อาจขึ้น `REMOTE HOST IDENTIFICATION HAS CHANGED` แก้ตาม[แก้ปัญหาการเชื่อมต่อ](setup/troubleshooting.md#host-key-changed)

### ย้ายหุ่นยนต์บางตัวไป 2.4 GHz
{: #force-24ghz }

ใช้เมื่อคอมพิวเตอร์ของผู้เข้าอบรมมองไม่เห็น Wi-Fi 5 GHz สั่งใน Terminal ของหุ่นยนต์ตัวนั้น (ต่อจอ HDMI หรือ SSH ผ่าน[สาย USB](setup/02-usb-ssh.md) เพราะ Wi-Fi จะหลุดระหว่างเปลี่ยน) ใช้ช่องตามหมายเลขหุ่นยนต์: หมายเลข 1, 4, 7, 10 ใช้ช่อง `1` หมายเลข 2, 5, 8 ใช้ช่อง `6` หมายเลข 3, 6, 9 ใช้ช่อง `11`

```bash
sudo nmcli con modify nstru-hotspot 802-11-wireless.band bg 802-11-wireless.channel 6
sudo nmcli con up nstru-hotspot
```

ใช้ช่องตามตารางนี้ เพราะเป็นช่องสำรองที่ขั้นที่ 5 ยอมรับอยู่แล้ว รันโปรแกรมตั้งค่าซ้ำภายหลังจะขึ้น `✓` และไม่ย้ายกลับไป 5 GHz

### ให้หุ่นยนต์ออก internet ชั่วคราว

dongle มีวิทยุตัวเดียว ขณะเป็น hotspot จึงต่อ Wi-Fi อื่นพร้อมกันไม่ได้ ถ้าต้อง `git pull` หรือติดตั้งอะไรเพิ่ม ให้ต่อจอ HDMI แล้วสลับไป Wi-Fi ที่มี internet ซึ่งหุ่นยนต์เคยจำไว้ (คอมพิวเตอร์ที่ต่อ hotspot อยู่จะหลุด)

```bash
nmcli con up <ชื่อ Wi-Fi>
```

เสร็จแล้วกลับเป็น hotspot ด้วย `sudo nmcli con up nstru-hotspot` หรือ reboot ในวันอบรมให้คัดลอก repo ด้วย flash drive แทน ตามหัวข้อถัดไป

## คัดลอก repo ลงหุ่นยนต์ด้วย flash drive
{: #usb-copy }

ทำหลังแก้ repo เสร็จทั้งหมดแล้ว วิธีนี้ไม่ต้องให้หุ่นยนต์ออก internet ใช้ `git bundle` ซึ่งรวมทั้ง repo ไว้ในไฟล์เดียว (ประมาณ 5 MB) แล้ว clone จากไฟล์นั้นบนหุ่นยนต์

- หุ่นยนต์ได้ git repo ที่สมบูรณ์ ผู้เข้าอบรมสั่ง `git checkout` คืน notebook ที่แก้จนเสียได้ ตาม[ขั้นที่ 1 ใช้งาน Jupyter Lab](setup/04-jupyter-lab.md)
- ไม่ต้อง copy ทั้ง folder ถ้า copy ผ่าน drive แบบ FAT32 หรือ exFAT สิทธิ์ของไฟล์จะหาย และถ้า copy ด้วย `sudo` เจ้าของไฟล์จะเป็น root ทำให้ Jupyter บันทึกไฟล์ไม่ได้

### เตรียม flash drive (ครั้งเดียว บนคอมพิวเตอร์ของทีมงาน)

```bash
cd jetbot-mini-bootcamp-nstru
git pull
git bundle create /Volumes/<ชื่อ drive>/jetbot-mini-bootcamp-nstru.bundle --all
git bundle verify /Volumes/<ชื่อ drive>/jetbot-mini-bootcamp-nstru.bundle
```

บน Windows ใช้ path ของ drive แทน เช่น `E:/jetbot-mini-bootcamp-nstru.bundle` จด commit ล่าสุดจาก `git log --oneline -1` ไว้เทียบกับหุ่นยนต์

### คัดลอกลงหุ่นยนต์ (ทำทีละตัว)

1. เสียบ flash drive ที่ช่อง USB-A แล้วหาว่า drive อยู่ที่ไหน

   ```bash
   lsblk -o NAME,SIZE,LABEL,MOUNTPOINT
   ```

   ถ้าต่อจอและ login desktop อยู่ drive จะ mount เองที่ `/media/jetson/<ชื่อ drive>` ถ้าแถวของ flash drive ไม่มี MOUNTPOINT ให้ mount เอง

   ```bash
   sudo mount /dev/sdX1 /mnt
   ```

   ดูชื่อ `sdX1` จากขนาดและชื่อ drive ให้ดี หุ่นยนต์ที่ระบบหลักอยู่บน USB drive จะมี `sda` เป็นดิสก์ของระบบอยู่แล้ว flash drive จึงมักเป็น `sdb`

2. clone จาก bundle ด้วยผู้ใช้ `jetson` ห้ามใช้ `sudo` แล้วชี้ origin กลับไปที่ GitHub เพื่อให้ `git pull` ได้เมื่อมี internet

   ```bash
   git clone /media/jetson/<ชื่อ drive>/jetbot-mini-bootcamp-nstru.bundle ~/jetbot-mini-bootcamp-nstru
   cd ~/jetbot-mini-bootcamp-nstru
   git remote set-url origin https://github.com/Dhanabhon/jetbot-mini-bootcamp-nstru.git
   git log --oneline -1
   ```

   commit ที่ได้ต้องตรงกับที่จดไว้ ถ้าขึ้น `destination path ... already exists` แปลว่ามี folder เก่าอยู่ ให้ย้ายออกก่อนด้วย `mv ~/jetbot-mini-bootcamp-nstru ~/jetbot-mini-bootcamp-nstru.old`

3. ถอด drive ถ้า mount เองให้สั่ง `sudo umount /mnt` ถ้า mount อัตโนมัติให้กด Eject ใน desktop แล้วค่อยดึงออก
4. เปิด Jupyter Lab แล้วตรวจว่าเห็น folder `jetbot-mini-bootcamp-nstru`

### อัปเดตโค้ดหลังคัดลอกไปแล้ว

สร้าง bundle ใหม่ลง flash drive แล้วสั่งบนหุ่นยนต์

```bash
cd ~/jetbot-mini-bootcamp-nstru
git pull /media/jetson/<ชื่อ drive>/jetbot-mini-bootcamp-nstru.bundle main
```

ทำก่อนผู้เข้าอบรมเริ่มแก้ notebook ถ้ามีการแก้แล้ว `git pull` อาจชนกับไฟล์ที่แก้ไว้

## โปรแกรมตั้งค่าหุ่นยนต์
{: #robot-setup }

`tools/robot_setup.py` ตั้งค่าหุ่นยนต์ทีละขั้น ผู้เข้าอบรมรันเองในห้อง โดยต่อจอ HDMI คีย์บอร์ด และเมาส์ไว้ ส่วนทีมงานใช้โหมดตรวจอย่างเดียวก่อนวันอบรม ทุกขั้นตรวจก่อนว่าทำไว้แล้วหรือยัง จึงรันซ้ำได้ และใช้ซ่อมหุ่นยนต์ที่ค่าเพี้ยนได้ด้วย

รันเป็น user `jetson` ไม่ต้องใส่ `sudo` โปรแกรมจะขอรหัสผ่านเอง

```bash
cd ~/jetbot-mini-bootcamp-nstru
python3 tools/robot_setup.py
```

| ตัวเลือก | ใช้ตอนไหน |
| :--- | :--- |
| ไม่ใส่ | ผู้เข้าอบรมตั้งค่าครบทุกขั้นตามผู้สอน |
| `--check-only` | ทีมงานตรวจล่วงหน้า: รันเฉพาะขั้นที่ 1 และ 9 และไม่แก้อะไรในเครื่อง |
| `--step 7` | รันซ้ำเฉพาะขั้นที่ระบุ เช่น หลังแก้ปัญหา |
| `--dry-run` | แสดงคำสั่งที่จะรันโดยไม่รันจริง ใช้บนคอมพิวเตอร์ได้ |

ผลทุกครั้งบันทึกต่อท้ายไว้ที่ `~/robot_setup.log`

| ขั้น | ทำอะไร |
| :---: | :--- |
| 1 | ตรวจรุ่นบอร์ด, RAM, L4T, พื้นที่ดิสก์, แบตเตอรี่, Thai font และ Wi-Fi dongle (มี `wlan0` หรือไม่ เปิด AP ได้หรือไม่ และเปิด AP ที่ช่อง 5 GHz ใดได้บ้าง) |
| 2 | ถามหมายเลขหุ่นยนต์ ตั้ง hostname เป็น `jetbot-NN` และแก้ `/etc/hosts` แล้วบันทึกหมายเลขไว้ที่ `~/.jetbot-nstru/robot.conf` |
| 3 | ตั้งเขตเวลาเป็น Asia/Bangkok และตั้งวันเวลาใหม่ถ้าผิด |
| 4 | ปิด `jetbotmini_start` (APP มือถือ) และ `jetbotmini_stats` (OLED ที่ crash เมื่อไม่มี `wlan0`) ถาวร |
| 5 | ปิดการเปิดอัตโนมัติของ hotspot `jetbot-mini` เดิม (หาจาก connection ที่เป็น AP mode เพราะชื่อ connection ไม่ตรงกับชื่อ Wi-Fi บนหุ่นทดสอบชื่อ `Wi-Fi connection 1`) แล้วสร้าง connection `nstru-hotspot` ชื่อ Wi-Fi `JETBOT-NN` รหัสจาก[ไฟล์รหัส](#hotspot-conf) ที่อยู่ `10.42.0.1` เลือกช่อง 5 GHz ถ้า dongle เปิด AP ที่นั่นได้ ถ้าเปิดไม่ขึ้นจะลองช่อง 1/6/11 แทน ทดสอบบนหุ่นจริงแล้ว ได้ช่อง 44 (5 GHz) |
| 6 | ตั้ง power mode เป็น MAXN |
| 7 | ให้ Jupyter เปิดที่ folder ของ repo โดยเขียน systemd drop-in ไว้ที่ `/etc/systemd/system/<service>.service.d/nstru.conf` drop-in นี้ใส่ `--notebook-dir` ในคำสั่งเปิด Jupyter เพราะ `~/.jupyter/jupyter_notebook_config.py` ของ Yahboom ตั้ง `notebook_dir` เป็น `~/Notebooks` ไว้ ค่าจากคำสั่งชนะค่าในไฟล์ config ผู้เรียนจะเปิด folder `Notebooks` ของ Yahboom จาก Jupyter ไม่ได้อีก ถ้าจะย้อนกลับ ให้ลบไฟล์นี้แล้วสั่ง `sudo systemctl daemon-reload` |
| 8 | ติดตั้ง service `nstru_status`: Buzzer ดัง 3 ครั้งเมื่อ boot เสร็จ และจอ OLED แสดงชื่อ Wi-Fi รหัส IP และแบต |
| 9 | ทดสอบกล้อง (บันทึกภาพไว้ที่ `~/setup_camera.jpg`), Buzzer, ล้อซ้ายและขวา, จอ OLED และปุ่ม KEY1 ต้องยกล้อให้ลอยก่อน |
| 10 | สรุปผล แล้วถามว่าจะ shutdown หรือไม่ |

- หลังขั้นที่ 4 Buzzer จะไม่ดัง 3 ครั้งตอน boot จนกว่าจะผ่านขั้นที่ 8 เพราะเสียงเดิมมาจาก `jetbotmini_start`
- ขั้นที่ 9 หยุด service ที่ใช้มอเตอร์ กล้อง และจอ OLED อยู่ไว้ชั่วคราว แล้วเปิดกลับเมื่อทดสอบเสร็จ `--check-only` จึงใช้กับหุ่นยนต์ที่ยังไม่ได้ตั้งค่าได้

### ไฟล์รหัส hotspot
{: #hotspot-conf }

hotspot ทุกตัวใช้รหัสรูปแบบเดียวกัน แต่ห้ามเก็บรหัสไว้ใน repo เพราะ repo นี้เปิดเป็น public ให้เขียนรูปแบบรหัสไว้ 1 บรรทัดในไฟล์ `hotspot.conf` บน flash drive แล้วใส่ `{num}` ตรงที่จะให้แทนด้วยหมายเลขหุ่นยนต์ 2 หลัก เช่น รูปแบบ `abcd{num}xy` ของหุ่นยนต์หมายเลข 7 จะได้รหัส `abcd07xy` รหัสต้องยาว 8–63 ตัวอักษร

คัดลอกลงหุ่นยนต์ทุกตัวในรอบเดียวกับที่[คัดลอก repo](#usb-copy)

```bash
mkdir -p ~/.jetbot-nstru
cp /media/jetson/<ชื่อ drive>/hotspot.conf ~/.jetbot-nstru/
chmod 600 ~/.jetbot-nstru/hotspot.conf
```

จอ OLED จะแสดงรหัสก็ต่อเมื่อหุ่นยนต์ปล่อย Wi-Fi ชื่อ `JETBOT-NN` ของตัวเองอยู่ ขั้นที่ 5 ไม่แสดงรหัสในหน้าจอ Terminal และใน log

image ของ Yahboom จำ Wi-Fi ไว้ราว 20 วง ทุกวงตั้งให้ต่ออัตโนมัติ ขั้นที่ 5 ไม่ลบวงเหล่านี้ แต่ตั้ง `nstru-hotspot` ให้มี priority สูงกว่า (100) ตอน boot หุ่นจึงเปิด hotspot ก่อน ถ้าทีมงานต้องการให้หุ่นต่อ internet ชั่วคราว เช่น เพื่อ `git pull` ให้สั่ง `nmcli con up "<ชื่อ Wi-Fi>"` แล้วสั่ง `nmcli con up nstru-hotspot` เพื่อกลับมาเป็น hotspot

## ตรวจโค้ดกับหุ่นยนต์จริง

โค้ดใน `jetbot_nstru/hardware.py` เขียนจากเอกสารของ Yahboom และ NVIDIA แต่ยังไม่ได้ทดสอบกับรถจริง จุดที่ติด `VERIFY ON ROBOT` ต้องลองบนรถ 1 คันก่อนวันอบรม:

- [ ] `open_robot()` import `jetbotmini.Robot` ได้ (ถ้าไม่ได้ ดูชื่อ package ใน image ของ Yahboom)
- [ ] `CsiCamera(lock_exposure=True)` เปิดกล้องได้ ถ้า L4T เก่ากว่า 32.4 จะ fallback ไปใช้ auto exposure และขึ้น warning
- [ ] `Oled().show("TEST")` แสดงผลหลังหยุด `nstru_status` หรือ `jetbotmini_stats` แล้ว
- [ ] `read_battery_voltage()` ได้ค่าใกล้กับที่มิเตอร์วัด (ปรับ `BATTERY_SCALE` ถ้าต่าง)
- [ ] `beep(robot)` มีเสียง `beep()` เขียนค่า 1/0 ลง register `0x06` ของบอร์ดขยาย ตามโค้ด APP ของ Yahboom (`Robot` ของ Yahboom ไม่มี `.buzzer`) ขั้นที่ 9 ของ[โปรแกรมตั้งค่า](#robot-setup)ทดสอบให้แล้ว
- [ ] Module 4 วิ่งได้อย่างน้อย 15 FPS พร้อมเปิด stream

## แก้ notebook

notebook ทั้งในโฟลเดอร์ `notebooks/` และ `notebooks/solutions/` สร้างจากไฟล์ต้นฉบับใน `notebooks/src/` อย่าแก้ไฟล์ `.ipynb` โดยตรง:

1. แก้ `notebooks/src/NN_*.py` โค้ดเฉลยอยู่ระหว่าง `# BEGIN SOLUTION: คำใบ้` กับ `# END SOLUTION`
2. รัน `python3 tools/build_notebooks.py` จะได้ทั้งฉบับผู้เข้าอบรม (ช่องเฉลยกลายเป็น `TODO`) และฉบับเฉลย
3. รัน `python3 -m pytest tests -q` test จะ fail ถ้าลืม build หรือโค้ดใน notebook มี syntax error

## การเตรียมสนาม

- ขึงไวนิลให้ตึงเรียบด้วยเทปกาว ลดรอยยับเป็นคลื่น
- ให้ผู้เข้าอบรมปิด Auto Exposure ของกล้องในโค้ด กันภาพสว่าง/มืดวูบวาบจากเงาสะท้อนไฟห้องบนพื้นไวนิล

## Run-of-show

> คาดการณ์จากเนื้อหาใน notebook ยังไม่ได้มาจากการสอนจริง ทดลองสอนแล้วให้แก้ตารางนี้ตามที่เจอ

ทุก module มีทางลัดเดียวกัน: ถ้าคนส่วนใหญ่ยังไม่เสร็จเมื่อหมดเวลา ให้เปิดเฉลยใน `notebooks/solutions/` แล้วไปต่อ เพราะ module ถัดไป import โค้ดจาก `jetbot_nstru/` ไม่ได้ใช้โค้ดที่ผู้เข้าอบรมเขียน และค่าของรถแต่ละคันอยู่ใน `my_params.json`

| Module | จุดที่มักติด | แผนสำรอง |
| :--- | :--- | :--- |
| 1 | เปิด `http://10.42.0.1:8888` ไม่ได้ (คอมพิวเตอร์สลับไป Wi-Fi อื่น หรือหุ่นยนต์ไม่ได้เปิด hotspot), จอ OLED ไม่เปลี่ยนเพราะยังไม่หยุด `nstru_status`, กล้องไม่ว่างเพราะ notebook อื่นถือไว้ | ให้นั่งคู่ 2 คนต่อรถ 1 คันจนกว่าจะต่อได้ครบ ข้าม cell OLED ไปก่อนแล้วกลับมาทำใน Module 6 แก้กล้องด้วย `sudo systemctl restart nvargus-daemon` |
| 2 | วัดระยะเบี้ยวกันนาน, รถเบี้ยวไม่เท่ากันที่ความเร็วต่างกัน, ลืมรัน cell `save_params` | ยอมรับเบี้ยวไม่เกิน 5 ซม. แล้วให้ PID ใน Module 4 ช่วยแก้ อย่างน้อยต้องบันทึก trim ไว้ แม้จะเป็น 1.0 ทั้งคู่ |
| 3 | ค่า `black_v_max` ที่ตั้งได้ใช้ไม่ได้เมื่อแสงห้องหรือเงาเปลี่ยน, มุมก้มกล้องสูงไปจนเห็นนอกสนามใน ROI, หาสี่เหลี่ยมเขียวไม่เจอ | ใช้ `detect_line()` จาก `jetbot_nstru.line` แทนฟังก์ชันที่เขียนเอง และลอง `use_adaptive=True` ถ้าแสงไม่สม่ำเสมอ |
| 4 | เครื่องหมายของ `steer` กลับด้านทำให้รถเลี้ยวหนีเส้น, ตั้ง `Kp` สูงจนส่าย, จูนตามภาพใน browser ที่ช้ากว่ารถจริง | ใช้ค่าในเฉลย `Kp 0.6`, `Kd 0.05` และลด `MAX_SPEED` เหลือ 0.4 ให้วิ่งจบรอบก่อน แล้วค่อยเร่ง ย้ำว่าภาพ stream ช้ากว่าจริง 0.1–0.2 วินาที |
| 5 | สีป้ายใต้ไฟห้องต่างจากค่า HSV เริ่มต้น, สับสนป้ายซ้ายกับขวา, อ่านป้ายจากไกลเกินจนกรอบเล็กกว่า `min_area` | ใช้ `detect_sign()` จาก `jetbot_nstru.signs` ข้ามส่วนเก็บ dataset และให้ Deep Learning เป็นการบ้าน (ยังไม่มี model ที่เทรนไว้แจก) |
| 6 | เลี้ยวก่อนถึงกลางจุดตัด, เลี้ยวซ้ำที่จุดตัดเดิม, Buzzer ไม่ดังเพราะชื่อคำสั่งของ Yahboom ไม่ตรง | เปิด `06_fsm_mission_integration_solution.ipynb` แล้วจูนเฉพาะ `MissionConfig` ตามตารางอาการใน notebook |
| 7 | รอคิวสนามจริงนาน, แบตตกจนรถช้าลง, Run All แล้วหยุดที่ `NotImplementedError` ที่ยังเหลือ | จัดคิวคนละ 5 นาทีวนไป ชาร์จแบตสำรองไว้ตลอด ใช้ `07_competition_template_solution.ipynb` ถ้ายังทำ TODO ไม่เสร็จ |
| 8 | เวลาเหลือไม่พอสำหรับ briefing | ตัดให้เหลือ 5 นาที แล้วให้อ่านกติกาเองใน [competition-rules.md](competition-rules.md) แต่ต้องแน่ใจว่าทุกคันบันทึก `my_params.json` แล้ว |
