# ใช้ Python Image มาตรฐาน
FROM python:3.9-slim

# ตั้งค่าโฟลเดอร์ทำงาน
WORKDIR /app

# ก๊อปปี้ไฟล์ทั้งหมดเข้าเครื่อง Server
COPY . .

# ติดตั้ง Library
RUN pip install --no-cache-dir -r requirements.txt

# HF Spaces บังคับให้ใช้ Port 7860 เท่านั้น
ENV PORT=7860

# สั่งรันแอป
CMD ["python", "code/ai.py"]