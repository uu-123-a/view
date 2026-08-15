import { Activity, BrainCircuit } from "lucide-react";
import type { EmotionObservation } from "../../types/interview";

export default function EmotionSignal({ value, compact = false }: { value?: EmotionObservation; compact?: boolean }) {
  if (!value) return null;
  return <div className={compact ? "emotion-signal compact" : "emotion-signal"}>
    <header><Activity size={15} /><b>表达状态：{value.label_text}</b><span>文本分析</span></header>
    <div className="emotion-meters">
      <label>自信<i><em style={{ width: `${value.confidence}%` }} /></i><strong>{value.confidence}</strong></label>
      <label>稳定<i><em style={{ width: `${value.stability}%` }} /></i><strong>{value.stability}</strong></label>
      <label>紧张<i className="tension"><em style={{ width: `${value.tension}%` }} /></i><strong>{value.tension}</strong></label>
    </div>
    {!compact && <p><BrainCircuit size={14} />{value.tip}</p>}
  </div>;
}
