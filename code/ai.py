import os
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ดึงค่าจาก Environment Variables ของ Render
API_KEY = os.getenv("GEMINI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")

# หาตำแหน่งของโฟลเดอร์ Root เพื่อดึงไฟล์ aivoice.html
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'aivoice.html')

@app.route('/process', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400

    audio_file = request.files['file']
    temp_path = "temp_voice.m4a"
    audio_file.save(temp_path)

    try:
        # 1. อัปโหลดไฟล์ไปที่ Google Cloud
        upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={API_KEY}"
        with open(temp_path, 'rb') as f:
            headers = {"X-Goog-Upload-Protocol": "multipart"}
            files = {
                'metadata': (None, '{"file": {"display_name": "kabintify_audio"}}', 'application/json'),
                'file': (temp_path, f, 'audio/x-m4a')
            }
            r_upload = requests.post(upload_url, headers=headers, files=files)
        
        file_data = r_upload.json()['file']
        file_uri = file_data['uri']
        file_name = file_data['name']

        # 2. รอให้ไฟล์พร้อม (ACTIVE)
        check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={API_KEY}"
        for _ in range(15):
            if requests.get(check_url).json().get('state') == 'ACTIVE':
                break
            time.sleep(2)

        # 3. สั่งสรุปผลด้วย Gemini 2.5 Flash
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "สรุปประกาศยามเช้าวิทยาลัยการอาชีพกบินทร์บุรีเป็นข้อๆ สั้นๆ เน้นเรื่อง วันเรียน วันสอบ และการจองชุดนักศึกษา"},
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
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": f"📢 **สรุปโดย Gemini 2.5 (Cloud)**\n\n{message}"}]}
    resp = requests.post(url, headers=headers, json=payload)
    return jsonify({"success": resp.status_code == 200})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)