import { useEffect, useState } from "react";
import { apiFetch } from "../../services/api";
import PageHead from "../shared/PageHead";

export default function MistakeBook() {
  const [items, setItems] = useState<any[]>([]);
  const [skill, setSkill] = useState("");
  const [answer, setAnswer] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState<number | null>(null);
  const [results, setResults] = useState<Record<number, any>>({});
  const [error, setError] = useState("");
  async function load(selected = skill) { try { const response = await apiFetch(`/api/mistakes?skill=${encodeURIComponent(selected)}`, undefined, 10000); const data = await response.json(); if (!response.ok) throw new Error(data.error || "无法读取错题。"); setItems(data.items || []); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "无法读取错题。"); } }
  useEffect(() => { void load(""); }, []);
  const skills = [...new Set(items.map(item => String(item.skill)))];
  async function retry(id: number) { setLoading(id); try { const response = await apiFetch(`/api/mistakes/${id}/retry`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ answer: answer[id] || "" }) }, 45000); const data = await response.json(); if (response.ok) { setResults(current => ({ ...current, [id]: data.evaluation })); await load(); } else setResults(current => ({ ...current, [id]: { error: data.error } })); } finally { setLoading(null); } }
  return <div className="page narrow page-mistakes"><PageHead eyebrow="RETRY & IMPROVE" title="错题本与智能复盘" description="重答低分问题，比较新旧得分，把薄弱环节练成稳定能力。" />{error && <div className="admin-notice" role="alert">{error}</div>}<div className="mistake-toolbar"><button className={!skill ? "active" : ""} onClick={() => { setSkill(""); void load(""); }}>全部</button>{skills.map(value => <button key={value} className={skill === value ? "active" : ""} onClick={() => { setSkill(value); void load(value); }}>{value}</button>)}<span>{items.length} 道</span></div><div className="mistake-list">{items.length ? items.map(item => <article className={`panel mistake-card ${item.resolved ? "resolved" : ""}`} key={item.id}><header><span>Q · {item.skill}</span><strong>{item.original_score} → {item.best_score}</strong><em>{item.resolved ? "已掌握" : "待复盘"}</em></header><h3>{item.question}</h3><details><summary>查看原回答与建议</summary><div className="mistake-original"><div><small>原回答</small><p>{item.original_answer}</p></div><div><small>改进建议</small><p>{item.improvement || item.feedback}</p></div></div></details><textarea rows={4} value={answer[item.id] || ""} onChange={event => setAnswer(current => ({ ...current, [item.id]: event.target.value }))} placeholder="重新组织答案，建议包含场景、行动、取舍和量化结果…" /><button className="primary" disabled={loading === item.id} onClick={() => retry(item.id)}>{loading === item.id ? "星火正在评分…" : "提交重答"}</button>{results[item.id] && <div className={results[item.id].error ? "retry-result error" : "retry-result"}>{results[item.id].error || <><strong>{results[item.id].score} 分 · {results[item.id].level}</strong><span>{results[item.id].feedback}</span><small>{results[item.id].improvement}</small></>}</div>}</article>) : <div className="panel report-empty">暂无错题。完成面试后，低于 75 分的回答会自动出现在这里。</div>}</div></div>;
}
