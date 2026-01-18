import requests
import time
from datetime import datetime

# ================= [ ส่วนที่ต้องแก้ไข ] =================
ACCESS_TOKEN = 'ใส่_CHANNEL_ACCESS_TOKEN_ของคุณตรงนี้'
USER_ID = 'ใส่_USER_ID_ของคุณตรงนี้'
# =====================================================

def get_timetable_flex(day_name, subjects):
    colors = {"Monday": "#FFB800", "Tuesday": "#FF4B91", "Wednesday": "#00B900", "Thursday": "#FF7A00", "Friday": "#0099FF"}
    header_color = colors.get(day_name, "#333333")
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
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [
                {"type": "text", "text": "ตารางเรียน คธ.3/2", "weight": "bold", "color": "#FFFFFF", "size": "xl"},
                {"type": "text", "text": f"ประจำวัน{day_name}", "color": "#FFFFFFCC", "size": "sm"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "วิชาเรียนวันนี้", "weight": "bold", "size": "md"},
                {"type": "separator", "margin": "md"},
                {"type": "box", "layout": "vertical", "margin": "md", "contents": subject_rows}
            ]
        }
    }

def send_line(message_payload):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [message_payload]}
    try:
        res = requests.post(url, headers=headers, json=payload)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ส่งสำเร็จ! (Status {res.status_code})")
    except Exception as e: print(f"Error: {e}")

# --- ข้อมูล Flex Message: รหัสวิชาครบ ชื่อเต็ม ---
day_subjects = {
    "Monday": [
        {"time": "08:00-10:00", "name": "20204-2008 การสร้างเว็บไซต์", "teacher": "ครูวิมณฑา", "room": "432"},
        {"time": "13:00-15:00", "name": "20204-2106 โปรแกรมสำเร็จรูปทางสถิติ", "teacher": "ครูพรพิงค์", "room": "434"},
        {"time": "15:00-16:00", "name": "20204-8501 โครงงาน", "teacher": "ครูวิทยา", "room": "443"}
    ],
    "Tuesday": [
        {"time": "08:00-10:00", "name": "20000-1204 การเขียนภาษาอังกฤษในชีวิตประจำวัน", "teacher": "ครูภาณุพงษ์", "room": "123"},
        {"time": "13:00-14:00", "name": "20000-1502 ประวัติศาสตร์ชาติไทย", "teacher": "ครูสุวรรณา", "room": "136"}
    ],
    "Wednesday": [
        {"time": "08:00-11:00", "name": "20000-1303 วิทยาศาสตร์เพื่อพัฒนาอาชีพธุรกิจและบริการ", "teacher": "ครูนภสร", "room": "137"},
        {"time": "13:00-14:00", "name": "Home Room", "teacher": "ครูวิทยา", "room": "443"},
        {"time": "14:00-16:00", "name": "20000-2007 กิจกรรมส่งเสริมคุณธรรม จริยธรรม", "teacher": "ครูวิทยา", "room": "443"}
    ],
    "Thursday": [
        {"time": "08:00-10:00", "name": "20000-1208 ภาษาอังกฤษเตรียมพร้อมเพื่อการทำงาน", "teacher": "ครูอชิตา", "room": "122"},
        {"time": "10:00-12:00", "name": "20204-2106 โปรแกรมสำเร็จรูปทางสถิติ", "teacher": "ครูพรพิงค์", "room": "434"},
        {"time": "13:00-15:00", "name": "20204-2008 การสร้างเว็บไซต์", "teacher": "ครูวิมณฑา", "room": "432"},
        {"time": "15:00-16:00", "name": "20204-8501 โครงงาน", "teacher": "ครูวิทยา", "room": "443"}
    ],
    "Friday": [
        {"time": "08:00-10:00", "name": "20001-1001 อาชีวะอนามัยและความปลอดภัย", "teacher": "ครูกษาปณ์", "room": "โดม"},
        {"time": "12:00-15:00", "name": "20001-1003 ธุรกิจและการเป็นผู้ประกอบการ", "teacher": "ครูนิติยา", "room": "441"}
    ]
}

# --- แจ้งเตือนรายวิชา: ตัดรหัสวิชาออกแล้ว คงชื่อเต็มและเลขห้องไว้ ---
text_reminders = {
    "Monday": {
        "08:00": "เริ่มเรียนวิชา การสร้างเว็บไซต์ ห้อง 432 (ครูวิมณฑา)",
        "13:00": "เริ่มเรียนวิชา โปรแกรมสำเร็จรูปทางสถิติ ห้อง 434 (ครูพรพิงค์)",
        "15:00": "เริ่มเรียนวิชา โครงงาน ห้อง 443 (ครูวิทยา)"
    },
    "Tuesday": {
        "08:00": "เริ่มเรียนวิชา การเขียนภาษาอังกฤษในชีวิตประจำวัน ห้อง 123 (ครูภาณุพงษ์)",
        "13:00": "เริ่มเรียนวิชา ประวัติศาสตร์ชาติไทย ห้อง 136 (ครูสุวรรณา)"
    },
    "Wednesday": {
        "08:00": "เริ่มเรียนวิชา วิทยาศาสตร์เพื่อพัฒนาอาชีพธุรกิจและบริการ ห้อง 137 (ครูนภสร)",
        "13:00": "เริ่มเข้า Home Room ห้อง 443 (ครูวิทยา)",
        "14:00": "เริ่มเรียนวิชา กิจกรรมส่งเสริมคุณธรรม จริยธรรม ห้อง 443 (ครูวิทยา)"
    },
    "Thursday": {
        "08:00": "เริ่มเรียนวิชา ภาษาอังกฤษเตรียมพร้อมเพื่อการทำงาน ห้อง 122 (ครูอชิตา)",
        "10:00": "เริ่มเรียนวิชา โปรแกรมสำเร็จรูปทางสถิติ ห้อง 434 (ครูพรพิงค์)",
        "13:00": "เริ่มเรียนวิชา การสร้างเว็บไซต์ ห้อง 432 (ครูวิมณฑา)",
        "15:00": "เริ่มเรียนวิชา โครงงาน ห้อง 443 (ครูวิทยา)"
    },
    "Friday": {
        "08:00": "เริ่มเรียนวิชา อาชีวะอนามัยและความปลอดภัย ที่หลังแผนก (ครูกษาปณ์)",
        "12:00": "เริ่มเรียนวิชา ธุรกิจและการเป็นผู้ประกอบการ ห้อง 441 (ครูนิติยา)"
    }
}

if __name__ == "__main__":
    print(">>> บอท Kabintify Pro เริ่มทำงาน...")
    while True:
        now = datetime.now()
        day, hm = now.strftime("%A"), now.strftime("%H:%M")
        if day in day_subjects:
            if hm == "07:40":
                flex = get_timetable_flex(day, day_subjects[day])
                send_line({"type": "flex", "altText": f"ตารางเรียนวัน{day}", "contents": flex})
                time.sleep(60)
            elif day in text_reminders and hm in text_reminders[day]:
                send_line({"type": "text", "text": text_reminders[day][hm]})
                time.sleep(60)
        time.sleep(30)
