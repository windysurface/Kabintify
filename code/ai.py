import os
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ดึงค่าความลับจาก Render Environment Variables
API_KEY = os.getenv("GEMINI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✅ ฟังก์ชันสำหรับตรวจสอบกุญแจ (Authorization Header)
def is_authorized(auth_header):
    if not auth_header:
        return False
    # ตรวจสอบว่ากุญแจที่ส่งมาตรงกับ ADMIN_PASS หรือไม่
    return auth_header == f"Bearer {ADMIN_PASS}"

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'aivoice.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    u, p = data.get('username'), data.get('password')
    if u == ADMIN_USER and p == ADMIN_PASS:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "รหัสผ่านไม่ถูกต้อง"}), 401

@app.route('/process', methods=['POST'])
def process_audio():
    # 🛡️ ล็อคประตูที่ 1: เช็กสิทธิ์ก่อนประมวลผล
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400

    audio_file = request.files['file']
    temp_path = "temp_voice.m4a"
    audio_file.save(temp_path)

    try:
        upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={API_KEY}"
        with open(temp_path, 'rb') as f:
            headers = {"X-Goog-Upload-Protocol": "multipart"}
            files = {
                'metadata': (None, '{"file": {"display_name": "kabintify_audio"}}', 'application/json'),
                'file': (temp_path, f, 'audio/x-m4a')
            }
            r_upload = requests.post(upload_url, headers=headers, files=files)
        
        file_data = r_upload.json()['file']
        file_uri, file_name = file_data['uri'], file_data['name']

        for _ in range(20):
            if requests.get(f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={API_KEY}").json().get('state') == 'ACTIVE':
                break
            time.sleep(1)

        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        payload = {"contents": [{"parts": [{"text": "สรุปใจความสำคัญจากเสียงนี้เป็นข้อๆ"}, {"fileData": {"mimeType": "audio/x-m4a", "fileUri": file_uri}}]}]}
        
        r_gen = requests.post(gen_url, json=payload, timeout=25)
        summary_text = r_gen.json()['candidates'][0]['content']['parts'][0]['text']

        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": True, "summary": summary_text})
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/send-line', methods=['POST'])
def send_line():
    # 🛡️ ล็อคประตูที่ 2: เช็กสิทธิ์ก่อนส่ง LINE
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.json
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": f"📢 **สรุปจากวิทยาลัย (Cloud)**\n\n{data.get('message')}"}]}
    resp = requests.post(url, headers=headers, json=payload)
    return jsonify({"success": resp.status_code == 200})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))