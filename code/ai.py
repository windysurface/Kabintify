import os
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GEMINI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")
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
        # 1. อัปโหลดไป Google (จุดนี้เน็ตช้าอาจจะติดขัด ต้องรอจนเสร็จ)
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

        # 2. ปรับการรอให้ "เร็วขึ้น" เพื่อแข่งกับเวลา 30 วินาทีของ Render
        # ไฟล์ 20 นาที Gemini มักจะประมวลผลประมาณ 10-15 วินาที
        for _ in range(20): # เช็ค 20 ครั้ง
            status_resp = requests.get(f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={API_KEY}").json()
            if status_resp.get('state') == 'ACTIVE':
                break
            time.sleep(1) # รอแค่ 1 วินาทีต่อรอบ

        # 3. สรุปผล (สั่งให้สรุปแบบกระชับเพื่อลดเวลา Generation)
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "สรุปใจความสำคัญจากเสียงนี้เป็นข้อๆ อย่างรวดเร็วและแม่นยำที่สุด"},
                    {"fileData": {"mimeType": "audio/x-m4a", "fileUri": file_uri}}
                ]
            }]
        }
        
        r_gen = requests.post(gen_url, json=payload, timeout=25) # ตั้ง Timeout ภายในไว้ด้วย
        summary_text = r_gen.json()['candidates'][0]['content']['parts'][0]['text']

        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": True, "summary": summary_text})

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": False, "error": "ระบบใช้เวลานานเกินไปหรือเน็ตช้า กรุณาลองใหม่ด้วยไฟล์ที่สั้นลงเล็กน้อยจั๊ฟ" if "timeout" in str(e).lower() else str(e)}), 500

@app.route('/send-line', methods=['POST'])
def send_line():
    data = request.json
    message = data.get('message')
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": f"📢 **สรุปจากวิทยาลัย (Cloud)**\n\n{message}"}]}
    resp = requests.post(url, headers=headers, json=payload)
    return jsonify({"success": resp.status_code == 200})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)