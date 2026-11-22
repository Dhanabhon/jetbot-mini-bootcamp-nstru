---
title: ผังบอร์ดขยาย
parent: เอกสารอ้างอิง
nav_order: 3
---

# ผังบอร์ดขยาย (Expansion board)

บอร์ดขยายของ Yahboom เสียบอยู่บนขา 40 pin ของ Jetson Nano ทำหน้าที่จ่ายไฟจากแบตเตอรี่ ขับมอเตอร์ และต่อจอ OLED ใช้ผังนี้ตอนตรวจสัญญาณ boot หรือตอนสายหลุด

[![บอร์ดขยายของ JetBot Mini มองจากด้านบน: ขั้วไฟ T-type และสวิตช์ power ซ้ายล่าง ช่องมอเตอร์ซ้าย M1 ด้านซ้าย ช่องมอเตอร์ขวา M2 ด้านขวา ช่อง OLED ตรงกลาง ขา 40 pin ต่อ Jetson Nano ด้านบน ช่อง servo S1 S2 มุมขวาบน ปุ่ม KEY และไฟ 5V มุมขวาล่าง]({{ '/assets/images/expansion-board.webp' | relative_url }}){: width="1196" height="678" }]({{ '/assets/images/expansion-board.webp' | relative_url }})

แตะที่ภาพเพื่อเปิดขนาดเต็ม

## ชิ้นส่วนบนบอร์ด

| ป้ายในภาพ | ชิ้นส่วน | ใช้ทำอะไร |
| :--- | :--- | :--- |
| Jetson NANO interface | ขา 40 pin แถวบน | เสียบเข้ากับขา GPIO ของ Jetson Nano จ่ายไฟให้ Jetson และคุยกับบอร์ดผ่าน I2C |
| T-type power interface | ขั้วไฟสีแดง (POWER 12.6V) | ต่อแบตเตอรี่ Li-ion 3 เซลล์ เต็มที่ 12.6V |
| Power switch | สวิตช์ ON / OFF | เปิดปิดไฟทั้งคัน สั่ง `sudo shutdown -h now` ก่อนปิดทุกครั้ง |
| Left motor interface | ช่อง M1 | มอเตอร์ล้อซ้าย |
| Right motor interface | ช่อง M2 | มอเตอร์ล้อขวา |
| OLED interface | ช่อง SDA SCL VCC GND | จอ OLED ที่แสดง IP และข้อความจากโค้ดของเรา |
| 2-channel PWM servo | ขา S1, S2 | ต่อ servo ได้ 2 ตัว ไม่ได้ใช้ในการอบรมนี้ |
| Servo indicator light | ไฟข้างช่อง servo | ไฟแสดงสถานะของช่อง servo |
| 3.3V indicator | ไฟ 3.3V | ติดค้างเมื่อบอร์ดมีไฟ |
| Programmable green / blue light | ไฟ LED1, LED2 | ไฟที่โปรแกรมสั่งเปิดปิดได้ ไฟเขียวติดค้างหลัง boot เสร็จ |
| Status indicator light | ไฟ State | กะพริบหลัง boot เสร็จ |
| 5V indicator light | ไฟ 5V | ติดเมื่อวงจรจ่ายไฟ 5V ทำงาน |
| Key | ปุ่ม KEY | ปุ่มกดบนบอร์ด ไม่ได้ใช้ในการอบรมนี้ |

## ตรวจเร็วเมื่อมีปัญหา

- **เปิดสวิตช์แล้วไม่มีไฟสักดวง:** ตรวจขั้ว T-type ว่าเสียบแน่น และแบตเตอรี่ยังมีไฟ
- **ไฟ 3.3V ติด แต่จอ OLED ดับ:** ตรวจสายที่ช่อง OLED ทั้ง 4 เส้น แล้วรอให้ boot ครบ 2–3 นาที
- **สั่งเลี้ยวซ้ายแต่รถเลี้ยวขวา:** สายมอเตอร์อาจสลับช่องกัน ล้อซ้ายต้องอยู่ที่ M1 และล้อขวาอยู่ที่ M2
- **ล้อข้างเดียวไม่หมุน:** ตรวจสายที่ช่อง M1 หรือ M2 ของล้อข้างนั้น

ลำดับไฟตอน boot ดูที่[เปิดและปิดเครื่อง](01-power-on.md)
