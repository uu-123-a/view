import { ChevronLeft, History } from "lucide-react";
import PageHead from "../shared/PageHead";

function HistoryRow({ date, role, score, type, duration_seconds, onOpen }: any) {
  const displayDate = /^\d{4}-\d{2}-\d{2}$/.test(date) ? new Date(`${date}T00:00:00`).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" }) : date;
  const minutes = Math.max(1, Math.round(Number(duration_seconds || 0) / 60));
  return <div className="history-row" role="button" tabIndex={0} onClick={onOpen} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") onOpen(); }}><div className="date-box">{displayDate}</div><div className="grow"><b>{role}</b><span>{type} · 约 {minutes} 分钟</span></div><div className="score-ring">{score}</div><ChevronLeft className="right-chevron" size={18} /></div>;
}

export default function HistoryView({ history, onOpenReport }: { history: any[]; onOpenReport: (item: any) => void }) {
  return <div className="page narrow page-history"><PageHead eyebrow="GROWTH TRACK" title="每次练习，都算数。" description="回看面试表现与能力变化，找到下一次最值得投入的训练点。" /><div className="panel history-full"><div className="panel-title"><div><span>训练档案</span><h3>全部模拟面试</h3></div><span className="pill">{history.length} 次记录</span></div><div className="history-list">{history.length ? history.map(item => <HistoryRow key={item.id} {...item} onOpen={() => onOpenReport(item)} />) : <div className="history-empty"><History size={24} /><span>暂无面试记录，先完成一次模拟面试吧。</span></div>}</div></div></div>;
}
