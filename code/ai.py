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

def is_authorized(auth_header):
    if not auth_header: return False
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
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400

    audio_file = request.files['file']
    temp_path = "temp_voice.m4a"
    audio_file.save(temp_path)

    try:
        # 1. อัปโหลดไฟล์ไปยัง Gemini API
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

        # 2. รอจนกว่าสถานะจะเป็น ACTIVE
        for _ in range(20):
            if requests.get(f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={API_KEY}").json().get('state') == 'ACTIVE':
                break
            time.sleep(1)

        # 3. สั่งให้ถอดความและสรุปผลแยกส่วนกัน
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "จงถอดข้อความจากเสียงนี้ทั้งหมดอย่างละเอียด (Transcription) จากนั้นคั่นด้วยคำว่า [SUMMARY_START] แล้วสรุปใจความสำคัญเป็นข้อๆ (Summary)"},
                    {"fileData": {"mimeType": "audio/x-m4a", "fileUri": file_uri}}
                ]
            }]
        }
        
        r_gen = requests.post(gen_url, json=payload, timeout=25)
        full_result = r_gen.json()['candidates'][0]['content']['parts'][0]['text']

        # แยกข้อความดิบออกจากบทสรุป
        if "[SUMMARY_START]" in full_result:
            raw_text, summary_text = full_result.split("[SUMMARY_START]")
        else:
            raw_text = "ไม่สามารถแยกข้อความดิบได้"
            summary_text = full_result

        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({
            "success": True, 
            "summary": summary_text.strip(), 
            "raw": raw_text.strip()
        })
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/send-line', methods=['POST'])
def send_line():
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