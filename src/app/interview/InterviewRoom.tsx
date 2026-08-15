import type { RefObject } from "react";
import { Bot, ChevronLeft, Mic, MicOff, Send, Volume2 } from "lucide-react";
import CameraPreview from "../../features/mock-interview/CameraPreview";
import { useSpeechRecognition } from "../../features/mock-interview/useSpeechRecognition";
import type { Message } from "../../types/interview";
import { speak } from "../../utils/speech";
import EmotionSignal from "./EmotionSignal";

type Props = { role: string; type: string; messages: Message[]; progress: number; maxQuestions: number; answer: string; setAnswer: (value: string) => void; recording: boolean; setRecording: (value: boolean) => void; seconds: number; thinking: boolean; submit: () => void; onExit: () => void; bottomRef: RefObject<HTMLDivElement | null>; interviewError: string };

export default function InterviewRoom(props: Props) {
  const { role, type, messages, progress, maxQuestions, answer, setAnswer, recording, setRecording, seconds, thinking, submit, onExit, bottomRef, interviewError } = props;
  const speech = useSpeechRecognition({ currentText: answer, onTranscript: setAnswer, onListeningChange: setRecording });
  function submitWithSpeechStop() { if (speech.listening) return speech.stop(); if (!speech.processing) submit(); }
  const questionCount = Math.min(messages.filter(message => message.role === "ai").length, maxQuestions);
  return <div className="interview-page page-interview">
    <div className="interview-top"><button className="ghost" onClick={onExit}><ChevronLeft size={18} />退出面试</button><div><b>{role}</b><span>{type} · 第 {questionCount} / {maxQuestions} 题</span></div><div className="timer"><span className="live-dot" /> {String(Math.floor(seconds / 60)).padStart(2, "0")}:{String(seconds % 60).padStart(2, "0")}</div></div>
    <div className="progress"><i style={{ width: `${progress}%` }} /></div>
    <div className="interview-layout">
      <section className="interviewer-stage"><CameraPreview /><div className="interview-task-card"><div className={thinking ? "task-ai thinking" : "task-ai"}><Bot size={21} /></div><div><span>MOSS 面试官 · 当前任务</span><strong>{thinking ? "正在分析你的回答" : "保持自然表达，清晰回答当前问题"}</strong></div><button className="audio-replay" onClick={() => speak([...messages].reverse().find(message => message.role === "ai")?.text || "")}><Volume2 size={17} />重播</button></div></section>
      <section className="conversation"><div className="chat-scroll">
        {messages.map((message, index) => <div key={index} className={`message ${message.role}`}><span>{message.role === "ai" ? "MOSS" : "你"}</span><p>{message.text}</p>{message.evaluation && <div className="turn-evaluation"><div className="turn-score"><strong>{message.evaluation.score}</strong><span>{message.evaluation.level}<small>{message.evaluation.source === "spark" ? "星火即时评分" : "本地即时评分"}</small></span></div><EmotionSignal value={message.evaluation.emotion} compact /><p>{message.evaluation.feedback}</p><dl><div><dt>回答亮点</dt><dd>{message.evaluation.strength}</dd></div><div><dt>改进建议</dt><dd>{message.evaluation.improvement}</dd></div></dl></div>}</div>)}
        {thinking && <div className="message ai"><span>MOSS</span><p className="typing"><i /><i /><i /></p></div>}<div ref={bottomRef} />
      </div><div className="answer-box">{interviewError && <div className="speech-error" role="alert">{interviewError}</div>}<textarea value={answer} onChange={event => setAnswer(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submitWithSpeechStop(); } }} placeholder="输入回答，或点击麦克风进行语音作答…" /><div className="answer-actions"><button className={recording ? "record active" : "record"} onClick={speech.toggle} disabled={speech.processing} title={speech.supported ? "录音将由本地 Whisper 转写" : "当前浏览器不支持录音"}>{recording ? <MicOff /> : <Mic />}<span>{speech.processing ? "Whisper 正在识别…" : recording ? "录音中，点击停止" : "语音回答"}</span></button><span className="hint">Enter 发送 · Shift + Enter 换行</span><button className="send" disabled={!answer.trim() || thinking || speech.listening || speech.processing} onClick={submitWithSpeechStop}><Send size={18} /></button></div>{speech.error && <div className="speech-error" role="alert">{speech.error}</div>}</div></section>
    </div>
  </div>;
}
