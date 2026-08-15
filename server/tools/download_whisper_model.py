"""预下载并验证本地 Whisper 模型。"""

from ..modules.whisper_service import WhisperService


if __name__ == "__main__":
    WhisperService()._get_model()
    print("Whisper model ready")
