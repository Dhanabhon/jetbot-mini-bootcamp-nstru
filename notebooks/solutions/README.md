# Solutions และ Checkpoint

เฉลยของแต่ละ module ตั้งชื่อไฟล์ให้ตรงกับ notebook ต้นฉบับ เช่น `04_pid_line_following_solution.ipynb`

ไฟล์ `.ipynb` ในโฟลเดอร์นี้สร้างอัตโนมัติจาก `notebooks/src/` ด้วย `python3 tools/build_notebooks.py` อย่าแก้ตรงนี้

ถ้าตามไม่ทันใน module ไหน ให้เปิดเฉลยของ module นั้นแล้วไปต่อ module ถัดไปได้เลย

## Module 3 แบบสคริปต์: จูนค่าผ่านหน้าเว็บ

`03_line_tuner.py` ทำงานเหมือนเฉลย Module 3 แต่จูนค่าผ่านหน้าเว็บที่มี slider และภาพสดจากกล้อง ไม่ต้องรัน cell ซ้ำทุกครั้งที่ขยับรถ เหมาะกับตอนวางรถบนสนามจริง

1. ปิด kernel ของ notebook Module 3 ก่อน (เมนู **Kernel > Shut Down Kernel**) เพราะ notebook ยังจับกล้องอยู่
2. เปิด Terminal ใน Jupyter Lab (**File > New > Terminal**) แล้วสั่ง

   ```bash
   cd ~/jetbot-mini-bootcamp-nstru
   python3 notebooks/solutions/03_line_tuner.py
   ```

3. เปิด `http://10.42.0.1:8080` ใน Chrome อีกแท็บหนึ่ง
4. เลื่อน `roi_top` ให้กรอบส้มครอบพื้นถนนหน้ารถ แล้วเลื่อน `black_v_max` จนภาพ mask ด้านล่างเห็นเส้นเต็ม ๆ แต่ไม่มีจุดขาวบนพื้น สลับไปดู **mask สีเขียว** ตอนวางรถหน้าจุดตัดเพื่อตรวจว่าเห็นสี่เหลี่ยมเขียว
5. กด **บันทึกลง my_params.json** ค่าจะถูกใช้ต่อใน Module 4, 6 และ 7 เหมือนบันทึกจาก notebook
6. กลับไปที่ Terminal แล้วกด `Ctrl` + `C` เพื่อหยุด กล้องจะว่างให้ notebook ใช้ต่อ

## Module 4 แบบสคริปต์: จูน PID ผ่านหน้าเว็บ

`04_pid_tuner.py` ทำงานเหมือนเฉลย Module 4 แต่ปรับ `Kp`, `Kd`, `max_speed` และ `min_speed` ได้ระหว่างรถวิ่ง ไม่ต้องหยุดแล้วรัน cell ใหม่ทุกรอบ ค่า `roi_top`, `black_v_max` และ trim ของล้อโหลดจาก `my_params.json` ที่บันทึกไว้ใน Module 2 และ 3

1. ปิด kernel ของ notebook ทุกตัวก่อน (เมนู **Kernel > Shut Down All Kernels**) เพราะ notebook อาจจับกล้องหรือ port 8080 อยู่
2. เปิด Terminal ใน Jupyter Lab แล้วสั่ง

   ```bash
   cd ~/jetbot-mini-bootcamp-nstru
   python3 notebooks/solutions/04_pid_tuner.py
   ```

3. เปิด `http://10.42.0.1:8080` ใน Chrome วางรถบนเส้น แล้วกด **Start** รถเริ่มต้นในสถานะหยุดเสมอ
4. ปรับ slider ระหว่างรถวิ่งได้เลย ลำดับการจูนเหมือนใน notebook: เพิ่ม `Kp` จนเข้าโค้งทัน เพิ่ม `Kd` จนหายส่าย แล้วค่อยเพิ่ม `max_speed`
5. กด **Stop** หรือ `Space` เพื่อหยุด เวลาที่วิ่งจะค้างไว้บนจอให้จดลงตาราง
6. กด **บันทึกลง my_params.json** ค่าจะถูกใช้ต่อใน Module 6 และ 7
7. กลับไปที่ Terminal แล้วกด `Ctrl` + `C` เพื่อจบโปรแกรม

รถจะหยุดเองเมื่อ

- ปิดแท็บ หรือคอมพิวเตอร์หลุดจาก Wi-Fi ของหุ่นยนต์เกิน 1.5 วินาที
- มองไม่เห็นเส้นติดต่อกันเกิน 2 วินาที
- กด `Ctrl` + `C` หรือปิดแท็บ Terminal ที่รันโปรแกรมอยู่
