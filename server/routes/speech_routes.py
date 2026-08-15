"""本地语音识别接口。"""

from flask import Blueprint, current_app, jsonify, request

from ..modules.whisper_service import WhisperService
from ..db.system_repository import SystemRepository

speech_api = Blueprint("speech_api", __name__)
service = WhisperService()
system = SystemRepository()


@speech_api.post("/transcribe")
def transcribe():
    if not system.enabled("whisper_enabled"):
        return jsonify({"error":"管理员已暂停本地 Whisper 服务。"}), 503
    audio = request.files.get("audio")
    if audio is None or not audio.filename:
        return jsonify({"error": "缺少 audio 音频文件"}), 400

    try:
        return jsonify(service.transcribe(audio))
    except RuntimeError as exc:
        system.log("whisper", str(exc))
        return jsonify({"error": str(exc)}), 503
    except Exception:
        system.log("whisper", "Whisper 转写发生未预期错误")
        current_app.logger.exception("Whisper transcription failed")
        return jsonify({"error": "本地 Whisper 转写失败，请查看 Flask 终端日志。"}), 500
