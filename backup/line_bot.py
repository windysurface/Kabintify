import requests
import os
from datetime import datetime, timedelta

# ดึงค่าจาก GitHub Secrets
ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

def get_flex(day, subjects):
    colors = {"Monday": "#FFB800", "Tuesday": "#FF4B91", "Wednesday": "#00B900", "Thursday": "#FF7A00", "Friday": "#0099FF"}
    subject_rows = []
    for s in subjects:
        subject_rows.append({
            "type": "box", "layout": "horizontal", "margin": "md",
            "contents": [
                {"type": "text", "text": s['time'], "size": "xs", "color": "#888888", "flex": 2},
                {"type": "text", "text": f"{s['name']}\n{s['teacher']}\nห้อง {s['room']}", "size": "sm", "weight": "bold", "wrap": True, "flex": 5}
            ]
        })
    return {
        "type": "bubble",
        "header": {"type": "box", "layout": "vertical", "backgroundColor": colors.get(day, "#333333"), "contents": [{"type": "text", "text": "ตารางเรียน คธ.3/2", "weight": "bold", "color": "#FFFFFF", "size": "xl"}, {"type": "text", "text": f"ประจำวัน{day}", "color": "#FFFFFFCC", "size": "sm"}]},
        "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "วิชาเรียนวันนี้", "weight": "bold", "size": "md"}, {"type": "separator", "margin": "md"}, {"type": "box", "layout": "vertical", "margin": "md", "contents": subject_rows}]}
    }

day_subjects = {
    "Monday": [{"time": "08:00-10:00", "name": "20204-2008 การสร้างเว็บไซต์", "teacher": "ครูวิมณฑา", "room": "432"}, {"time": "13:00-15:00", "name": "20204-2106 โปรแกรมสำเร็จรูปทางสถิติ", "teacher": "ครูพรพิงค์", "room": "434"}, {"time": "15:00-16:00", "name": "20204-8501 โครงงาน", "teacher": "ครูวิทยา", "room": "443"}],
    "Tuesday": [{"time": "08:00-10:00", "name": "20000-1204 การเขียนภาษาอังกฤษในชีวิตประจำวัน", "teacher": "ครูภาณุพงษ์", "room": "123"}, {"time": "13:00-14:00", "name": "20000-1502 ประวัติศาสตร์ชาติไทย", "teacher": "ครูสุวรรณา", "room": "136"}],
    "Wednesday": [{"time": "08:00-11:00", "name": "20000-1303 วิทยาศาสตร์เพื่อพัฒนาอาชีพธุรกิจและบริการ", "teacher": "ครูนภสร", "room": "137"}, {"time": "13:00-14:00", "name": "Home Room", "teacher": "ครูวิทยา", "room": "443"}, {"time": "14:00-16:00", "name": "20000-2007 กิจกรรมส่งเสริมคุณธรรม จริยธรรม", "teacher": "ครูวิทยา", "room": "443"}],
    "Thursday": [{"time": "08:00-10:00", "name": "20000-1208 ภาษาอังกฤษเตรียมพร้อมเพื่อการทำงาน", "teacher": "ครูอชิตา", "room": "122"}, {"time": "10:00-12:00", "name": "20204-2106 โปรแกรมสำเร็จรูปทางสถิติ", "teacher": "ครูพรพิงค์", "room": "434"}, {"time": "13:00-15:00", "name": "20204-2008 การสร้างเว็บไซต์", "teacher": "ครูวิมณฑา", "room": "432"}, {"time": "15:00-16:00", "name": "20204-8501 โครงงาน", "teacher": "ครูวิทยา", "room": "443"}],
    "Friday": [{"time": "08:00-10:00", "name": "20001-1001 อาชีวะอนามัยและความปลอดภัย", "teacher": "ครูกษาปณ์", "room": "โดม"}, {"time": "12:00-15:00", "name": "20001-1003 ธุรกิจและการเป็นผู้ประกอบการ", "teacher": "ครูนิติยา", "room": "441"}]
}

if __name__ == "__main__":
    now_th = datetime.utcnow() + timedelta(hours=7)
    day, hm = now_th.strftime("%A"), now_th.strftime("%H:%M")
    if day in day_subjects and "07:35" <= hm <= "07:55":
        payload = {"to": USER_ID, "messages": [{"type": "flex", "altText": f"ตารางเรียนวัน{day}", "contents": get_flex(day, day_subjects[day])}]}
        requests.post("https://api.line.me/v2/bot/message/push", headers={"Content-Type": "application/json", "Authorization": f"Bearer {ACCESS_TOKEN}"}, json=payload)
