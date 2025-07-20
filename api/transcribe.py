from flask import Flask, request, jsonify
import requests
import tempfile
import os

app = Flask(__name__)


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    """语音转文字接口"""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_filename = tmp_file.name

        try:
            # 调用语音转文字API
            url = "https://api.uomn.cn/v1/audio/transcriptions"
            headers = {
                "Authorization": "Bearer sk-9Q11KSLosBdSRvy8164f697c233c41E680F9FeE26dD26084"
            }

            with open(tmp_filename, "rb") as f:
                files = {"file": ("audio.webm", f, "audio/webm")}
                data = {"model": "whisper-1", "language": "zh"}

                response = requests.post(
                    url, headers=headers, files=files, data=data, timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    return jsonify({"text": result.get("text", "")})
                else:
                    return jsonify({"error": "Transcription failed"}), 500

        finally:
            # 清理临时文件
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    except Exception as e:
        print(f"Transcribe error: {e}")
        return jsonify({"error": str(e)}), 500


# Vercel handler
handler = app
