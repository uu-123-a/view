"""使用本地 faster-whisper 模型完成语音转写。"""

from __future__ import annotations

import os
import sys
import threading
import types
import wave
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from faster_whisper import WhisperModel
    from werkzeug.datastructures import FileStorage


class WhisperService:
    """读取前端生成的 WAV，并延迟加载本地 Whisper 模型。"""

    _model: WhisperModel | None = None
    _load_lock = threading.Lock()

    def _get_model(self) -> WhisperModel:
        if self._model is not None:
            return self._model

        with self._load_lock:
            if self._model is None:
                try:
                    # 当前 Windows 策略会拦截 PyAV DLL。本项目自行读取 WAV，
                    # Whisper 接收 NumPy PCM，因此无需加载 PyAV。
                    sys.modules.setdefault("av", types.ModuleType("av"))
                    from faster_whisper import WhisperModel
                except ImportError as exc:
                    raise RuntimeError(
                        "尚未安装 faster-whisper，请执行 pip install -r requirements.txt"
                    ) from exc

                model_name = os.getenv("WHISPER_MODEL", "small")
                device = os.getenv("WHISPER_DEVICE", "cpu")
                compute_type = os.getenv(
                    "WHISPER_COMPUTE_TYPE",
                    "int8" if device == "cpu" else "float16",
                )
                self._model = WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                )
        return self._model

    @staticmethod
    def _read_wav(audio: FileStorage) -> np.ndarray:
        audio.stream.seek(0)
        try:
            with wave.open(audio.stream, "rb") as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
        except (wave.Error, EOFError) as exc:
            raise RuntimeError("音频不是有效的 WAV 文件") from exc

        if sample_width != 2:
            raise RuntimeError("仅支持 16 位 PCM WAV 音频")
        samples = np.frombuffer(frames, dtype="<i2").astype(np.float32)
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)
        samples /= 32768.0

        if sample_rate != 16000 and samples.size:
            output_length = round(samples.size * 16000 / sample_rate)
            old_positions = np.arange(samples.size)
            new_positions = np.linspace(0, samples.size - 1, output_length)
            samples = np.interp(new_positions, old_positions, samples).astype(np.float32)
        return samples

    def transcribe(self, audio: FileStorage) -> dict[str, object]:
        samples = self._read_wav(audio)
        if samples.size < 1600:
            raise RuntimeError("录音时间太短，请至少说话 1 秒")

        segments, info = self._get_model().transcribe(
            samples,
            language="zh",
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        text = "".join(segment.text for segment in segments).strip()
        return {
            "text": text,
            "language": info.language,
            "duration": round(info.duration, 2),
            "model": os.getenv("WHISPER_MODEL", "small"),
        }
