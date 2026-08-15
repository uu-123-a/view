import { useEffect, useRef, useState } from "react";

type Options = {
  currentText: string;
  onTranscript: (text: string) => void;
  onListeningChange: (listening: boolean) => void;
};

function mergeBuffers(buffers: Float32Array[]) {
  const length = buffers.reduce((total, buffer) => total + buffer.length, 0);
  const merged = new Float32Array(length);
  let offset = 0;
  buffers.forEach((buffer) => {
    merged.set(buffer, offset);
    offset += buffer.length;
  });
  return merged;
}

function resample(input: Float32Array, inputRate: number, outputRate = 16000) {
  if (inputRate === outputRate) return input;
  const length = Math.max(1, Math.round(input.length * outputRate / inputRate));
  const output = new Float32Array(length);
  const ratio = inputRate / outputRate;
  for (let index = 0; index < length; index += 1) {
    const position = index * ratio;
    const left = Math.floor(position);
    const right = Math.min(left + 1, input.length - 1);
    const weight = position - left;
    output[index] = input[left] * (1 - weight) + input[right] * weight;
  }
  return output;
}

function encodeWav(samples: Float32Array, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeText = (offset: number, text: string) => {
    for (let index = 0; index < text.length; index += 1) {
      view.setUint8(offset + index, text.charCodeAt(index));
    }
  };

  writeText(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeText(8, "WAVE");
  writeText(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeText(36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  samples.forEach((sample) => {
    const value = Math.max(-1, Math.min(1, sample));
    view.setInt16(offset, value < 0 ? value * 0x8000 : value * 0x7fff, true);
    offset += 2;
  });
  return new Blob([buffer], { type: "audio/wav" });
}

export function useSpeechRecognition({
  currentText,
  onTranscript,
  onListeningChange,
}: Options) {
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const buffersRef = useRef<Float32Array[]>([]);
  const sampleRateRef = useRef(48000);
  const baseTextRef = useRef("");
  const [listening, setListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const supported =
    typeof AudioContext !== "undefined" &&
    Boolean(navigator.mediaDevices?.getUserMedia);

  function updateListening(next: boolean) {
    setListening(next);
    onListeningChange(next);
  }

  function releaseMicrophone() {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    void contextRef.current?.close();
    processorRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;
    contextRef.current = null;
  }

  async function transcribe(blob: Blob) {
    if (blob.size <= 44) {
      setError("没有录到声音，请检查麦克风后重试。");
      return;
    }
    setProcessing(true);
    setError("");
    const form = new FormData();
    form.append("audio", blob, "answer.wav");

    try {
      const response = await fetch("/api/speech/transcribe", {
        method: "POST",
        body: form,
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result.error || `识别服务返回错误：${response.status}`);
      }
      const text = String(result.text || "").trim();
      if (!text) {
        setError("Whisper 没有识别到有效语音，请靠近麦克风后重试。");
        return;
      }
      const prefix = baseTextRef.current ? `${baseTextRef.current}\n` : "";
      onTranscript(`${prefix}${text}`);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "无法连接本地 Whisper，请确认 Flask 后端已经启动。",
      );
    } finally {
      setProcessing(false);
    }
  }

  async function start() {
    if (!supported) {
      setError("当前浏览器不支持本地录音，请使用最新版 Chrome 或 Edge。");
      return;
    }
    if (processing || streamRef.current) return;

    setError("");
    baseTextRef.current = currentText.trim();
    buffersRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      const context = new AudioContext();
      await context.resume();
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1);
      processor.onaudioprocess = (event) => {
        buffersRef.current.push(new Float32Array(event.inputBuffer.getChannelData(0)));
      };
      source.connect(processor);
      processor.connect(context.destination);

      streamRef.current = stream;
      contextRef.current = context;
      sourceRef.current = source;
      processorRef.current = processor;
      sampleRateRef.current = context.sampleRate;
      updateListening(true);
    } catch (reason) {
      releaseMicrophone();
      updateListening(false);
      const denied =
        reason instanceof DOMException &&
        (reason.name === "NotAllowedError" || reason.name === "SecurityError");
      setError(
        denied
          ? "麦克风权限被拒绝，请在浏览器地址栏中允许麦克风。"
          : "无法打开麦克风，请检查系统输入设备。",
      );
    }
  }

  function stop() {
    if (!streamRef.current) return;
    const samples = resample(
      mergeBuffers(buffersRef.current),
      sampleRateRef.current,
    );
    releaseMicrophone();
    updateListening(false);
    void transcribe(encodeWav(samples));
  }

  useEffect(() => {
    return () => releaseMicrophone();
  }, []);

  return {
    supported,
    listening,
    processing,
    error,
    start,
    stop,
    toggle: listening ? stop : start,
  };
}
