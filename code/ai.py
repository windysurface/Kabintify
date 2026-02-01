import os
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- ดึงข้อมูลความลับจาก Environment Variables ---
API_KEY = os.getenv("GEMINI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")
# -----------------------------------------------

# ✅ เพิ่มส่วนนี้: สั่งให้แสดงหน้า aivoice.html เมื่อเข้าหน้าแรก
@app.route('/')
def index():
    # เนื่องจากไฟล์ ai.py อยู่ในโฟลเดอร์ code แต่ aivoice.html อยู่ข้างนอก (Root)
    # เราจึงใช้ '../' เพื่อย้อนกลับไปหาไฟล์ที่ Root folder ครับ
    return send_from_directory('../', 'aivoice.html')

@app.route('/process', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400

    audio_file = request.files['file']
    temp_path = "temp_voice.m4a"
    audio_file.save(temp_path)

    try:
        # 1. อัปโหลดไฟล์ไปยัง Google Cloud
        upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={API_KEY}"
        with open(temp_path, 'rb') as f:
            headers = {"X-Goog-Upload-Protocol": "multipart"}
            files = {
                'metadata': (None, '{"file": {"display_name": "kabintify_audio"}}', 'application/json'),
                'file': (temp_path, f, 'audio/x-m4a')
            }
            r_upload = requests.post(upload_url, headers=headers, files=files)
        
        upload_data = r_upload.json()
        file_uri = upload_data['file']['uri']
        file_name = upload_data['file']['name']

        # 2. รอประมวลผล (ACTIVE)
        check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={API_KEY}"
        for _ in range(15):
            if requests.get(check_url).json().get('state') == 'ACTIVE':
                break
            time.sleep(2)

        # 3. สรุปผลด้วย Gemini 2.5 Flash
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "สรุปประกาศวิทยาลัยการอาชีพกบินทร์บุรีเป็นข้อๆ สั้นๆ เน้นเรื่องวันเรียน วันสอบ และการจองชุดนักศึกษา"},
                    {"fileData": {"mimeType": "audio/x-m4a", "fileUri": file_uri}}
                ]
            }]
        }
        
        r_gen = requests.post(gen_url, json=payload)
        summary_text = r_gen.json()['candidates'][0]['content']['parts'][0]['text']

        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": True, "summary": summary_text})

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/send-line', methods=['POST'])
def send_line():
    data = request.json
    message = data.get('message')
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": f"📢 **สรุปโดย Kabintify (Gemini 2.5)**\n\n{message}"}]}
    resp = requests.post(url, headers=headers, json=payload)
    return jsonify({"success": resp.status_code == 200})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)