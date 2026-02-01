import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ================= [ ตั้งค่า API ] =================
API_KEY = os.getenv("GEMINI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")
# =================================================

@app.route('/process', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "ไม่พบไฟล์"}), 400

    audio_file = request.files['file']
    temp_path = "temp_voice.m4a"
    audio_file.save(temp_path)

    try:
        # 1. อัปโหลดไฟล์ (ใช้ v1beta เหมือนเดิม แต่รองรับรุ่นใหม่)
        print("📦 1. กำลังส่งไฟล์ไปที่ Google Cloud...")
        upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={API_KEY}"
        
        with open(temp_path, 'rb') as f:
            headers = {"X-Goog-Upload-Protocol": "multipart"}
            files = {
                'metadata': (None, '{"file": {"display_name": "kabintify_audio"}}', 'application/json'),
                'file': (temp_path, f, 'audio/x-m4a')
            }
            r_upload = requests.post(upload_url, headers=headers, files=files)
        
        if r_upload.status_code != 200:
            raise Exception(f"Upload Failed: {r_upload.text}")
            
        upload_data = r_upload.json()
        file_uri = upload_data['file']['uri']
        file_name = upload_data['file']['name']

        # 2. รอให้ไฟล์พร้อม (ACTIVE)
        print("⏳ 2. รอให้ AI ประมวลผลไฟล์เสียง...")
        check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={API_KEY}"
        for _ in range(15):
            status_resp = requests.get(check_url).json()
            if status_resp.get('state') == 'ACTIVE':
                print("✅ ไฟล์พร้อมแล้ว!")
                break
            time.sleep(2)

        # 3. สั่งสรุปผลด้วย Gemini 2.5 Flash (ตัวใหม่ล่าสุด Jan 2026)
        print("🤖 3. กำลังใช้ Gemini 2.5 Flash สรุป...")
        
        # ใช้โมเดลใหม่ gemini-2.5-flash
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": "คุณคือผู้สรุปประกาศยามเช้าของวิทยาลัยการอาชีพกบินทร์บุรี สรุปเป็นข้อๆ สั้นๆ ไม่ยาวเกินไป ให้นักเรียนสามารถอ่านได้ง่ายๆ"},
                    {
                        # ต้องใช้ fileData (camelCase) เท่านั้นสำหรับ REST API
                        "fileData": { 
                            "mimeType": "audio/x-m4a", 
                            "fileUri": file_uri
                        }
                    }
                ]
            }]
        }
        
        r_gen = requests.post(gen_url, json=payload)
        gen_json = r_gen.json()
        
        if 'candidates' not in gen_json:
            error_msg = gen_json.get('error', {}).get('message', 'AI ทำงานไม่สำเร็จ')
            raise Exception(f"Google API Error: {error_msg}")

        summary_text = gen_json['candidates'][0]['content']['parts'][0]['text']

        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": True, "summary": summary_text})

    except Exception as e:
        print(f"❌ พังเพราะ: {str(e)}")
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/send-line', methods=['POST'])
def send_line():
    data = request.json
    message = data.get('message')
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": f"📢 **สรุปโดย Gemini 2.5**\n\n{message}"}]}
    resp = requests.post(url, headers=headers, json=payload)
    return jsonify({"success": resp.status_code == 200})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)