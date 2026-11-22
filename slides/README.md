# Slides

slide ประกอบการสอน แยกไฟล์ตาม module (module ละ 5–8 หน้า เน้นภาพประกอบ)

## สไลด์บรรยายสำหรับวิทยากร

`lecture-deck/` เก็บต้นฉบับสไลด์บรรยาย 28 หน้า (ฟอนต์ Google Sans) ที่สร้างใน Claude Slides

- เปิดดูและนำเสนอ: <https://claude.ai/artifact/XKu2n6Nyc2n9MxyhGNdRVB> (เปิดได้เฉพาะคนที่เจ้าของแชร์ให้)
- `deck.json` ลำดับสไลด์และ section, `deck.css` สไตล์ที่ใช้ร่วมกัน, `slides/<id>.html` สไลด์ละไฟล์ พร้อม speaker notes ใน `<aside>`
- ภาพใน `mission.html` อ้างถึง asset ที่อัปโหลดไว้ใน Slides (`/_blob/...`) ไฟล์ต้นฉบับคือ `docs/assets/video/jetbot-mission-poster.jpg`
- ไฟล์ในโฟลเดอร์นี้เป็นสำเนา ถ้าแก้สไลด์ใน Slides ต้องคัดลอกกลับมาเองให้ตรงกัน
- ฉบับ PDF (ไม่มี speaker notes) อยู่ที่ `docs/assets/slides/jetbot-mini-bootcamp-lecture.pdf` และดาวน์โหลดได้จากหน้าแรกของเว็บคู่มือ แก้สไลด์แล้วให้สร้างใหม่ด้วย `python3 slides/build_pdf.py` จาก root ของ repo (ต้องมี Google Chrome และ internet)
