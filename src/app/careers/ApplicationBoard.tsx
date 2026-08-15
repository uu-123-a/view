import { useEffect, useState } from "react";
import { BriefcaseBusiness } from "lucide-react";
import { apiFetch } from "../../services/api";
import PageHead from "../shared/PageHead";

const labels: Record<string, string> = { wishlist: "待投递", applied: "已投递", written: "笔试", interview: "面试", offer: "Offer", closed: "已结束" };
const statuses = Object.keys(labels);

export default function ApplicationBoard({ onInterview }: { onInterview: (item: any) => void }) {
  const [data, setData] = useState<any>({ items: [], counts: {} });
  const [filter, setFilter] = useState("all");
  const [editing, setEditing] = useState<any>(null);
  const [notes, setNotes] = useState("");
  const [interviewAt, setInterviewAt] = useState("");
  const [error, setError] = useState("");

  async function load() { try { const response = await apiFetch("/api/applications", undefined, 10000); const result = await response.json(); if (!response.ok) throw new Error(result.error || "无法读取投递记录。"); setData(result); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "无法读取投递记录。"); } }
  useEffect(() => { void load(); }, []);
  async function update(item: any, status: string) { await apiFetch(`/api/applications/${item.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status, notes: item.notes || "", interview_at: item.interview_at || "" }) }, 10000); await load(); }
  function edit(item: any) { setEditing(item); setNotes(item.notes || ""); setInterviewAt(item.interview_at || ""); }
  async function save() { await apiFetch(`/api/applications/${editing.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: editing.status, notes, interview_at: interviewAt }) }, 10000); setEditing(null); await load(); }
  async function remove(id: number) { if (!window.confirm("确定移除这条投递记录吗？")) return; await apiFetch(`/api/applications/${id}`, { method: "DELETE" }, 10000); await load(); }
  const items = filter === "all" ? data.items : data.items.filter((item: any) => item.status === filter);

  return <div className="page narrow page-applications"><PageHead eyebrow="APPLICATION TRACKER" title="求职投递管理" description="集中管理岗位进度、面试时间和准备备注，并从面试阶段快速进入针对性训练。" />
    {error && <div className="admin-notice" role="alert">{error}</div>}
    <div className="application-summary"><button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}><b>{data.total || 0}</b><span>全部</span></button>{statuses.map(status => <button key={status} className={filter === status ? "active" : ""} onClick={() => setFilter(status)}><b>{data.counts?.[status] || 0}</b><span>{labels[status]}</span></button>)}</div>
    <div className="application-board">{items.map((item: any) => <article className="panel application-card" key={item.id}><div><h3>{item.title}</h3><p>{item.company} · {item.city} · {item.salary}</p><span className="application-meta">更新于 {String(item.updated_at).slice(0, 16)}{item.interview_at ? ` · 面试 ${item.interview_at.replace("T", " ")}` : ""}</span>{item.notes && <p>{item.notes}</p>}</div><select value={item.status} onChange={event => update(item, event.target.value)}>{statuses.map(status => <option value={status} key={status}>{labels[status]}</option>)}</select><div className="application-actions"><button onClick={() => edit(item)}>备注与时间</button>{["written", "interview"].includes(item.status) && <button onClick={() => onInterview(item)}>模拟面试</button>}<button className="danger" onClick={() => remove(item.id)}>移除</button></div>{editing?.id === item.id && <div className="application-editor"><label>面试时间<input type="datetime-local" value={interviewAt} onChange={event => setInterviewAt(event.target.value)} /></label><label>准备备注<textarea value={notes} onChange={event => setNotes(event.target.value)} placeholder="记录联系人、面试轮次、重点准备内容…" /></label><button className="primary" onClick={save}>保存</button></div>}</article>)}{!items.length && <div className="panel report-empty application-empty"><div><BriefcaseBusiness size={28} /><p>当前分类暂无记录。请先在岗位中心选择岗位加入投递。</p></div></div>}</div>
  </div>;
}
