import { Activity, ShieldCheck } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function EmotionReport({ summary }: { summary: any }) {
  if (!summary || !Array.isArray(summary.timeline) || !summary.timeline.length) return null;
  return <section className="panel emotion-report">
    <div className="panel-title"><div><span>表达情绪趋势</span><h3>面试状态分析</h3></div><span className="pill"><Activity size={14} /> 主状态：{summary.dominant_text}</span></div>
    <div className="emotion-report-layout">
      <div className="emotion-summary-cards"><div><span>平均自信</span><strong>{summary.average_confidence}</strong></div><div><span>平均稳定</span><strong>{summary.average_stability}</strong></div><div className="tension"><span>紧张信号</span><strong>{summary.average_tension}</strong></div></div>
      <ResponsiveContainer width="100%" height={230}><AreaChart data={summary.timeline}><CartesianGrid strokeDasharray="4 4" stroke="#e6ebef" /><XAxis dataKey="turn" /><YAxis domain={[0, 100]} /><Tooltip /><Area type="monotone" dataKey="confidence" name="自信" stroke="#13a184" fill="#19b99a" fillOpacity={.14} strokeWidth={2} /><Area type="monotone" dataKey="tension" name="紧张" stroke="#e58a62" fill="#e58a62" fillOpacity={.08} strokeWidth={2} /></AreaChart></ResponsiveContainer>
    </div>
    <p className="emotion-suggestion">{summary.suggestion}</p><small className="emotion-disclaimer"><ShieldCheck size={13} /> {summary.disclaimer}</small>
  </section>;
}
