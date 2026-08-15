import { useEffect, useState, type FormEvent } from "react";
import { Clock3 } from "lucide-react";
import { apiFetch } from "../../services/api";
import PageHead from "../shared/PageHead";

export default function ScheduleCenter({ onInterview }: { onInterview: (item: any) => void }) {
  const [data, setData] = useState<any>({ items: [], pending: 0, completed: 0 });
  const [title, setTitle] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const response = await apiFetch("/api/schedule", undefined, 10000);
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "无法读取日程。");
      setData(result);
      setError("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "无法读取日程。"); }
  }
  useEffect(() => { void load(); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    const response = await apiFetch("/api/schedule", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title, due_at: dueAt, notes }) }, 10000);
    if (!response.ok) return setError((await response.json()).error || "创建日程失败。");
    setTitle(""); setDueAt(""); setNotes(""); await load();
  }
  async function toggle(item: any) { await apiFetch(`/api/schedule/${item.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ completed: !item.completed }) }, 10000); await load(); }
  async function remove(id: number) { await apiFetch(`/api/schedule/${id}`, { method: "DELETE" }, 10000); await load(); }
  function parts(value: string) { const date = new Date(value); return { day: Number.isNaN(date.getTime()) ? "--" : String(date.getDate()).padStart(2, "0"), month: Number.isNaN(date.getTime()) ? "时间" : `${date.getMonth() + 1}月`, text: value.replace("T", " ") }; }

  return <div className="page narrow page-schedule"><PageHead eyebrow="INTERVIEW CALENDAR" title="面试日程中心" description="自动汇总投递看板中的面试时间，并安排岗位研究、项目复盘和模拟面试任务。" />
    {error && <div className="admin-notice" role="alert">{error}</div>}
    <div className="schedule-grid"><aside className="panel schedule-form"><h3>新增准备事项</h3><form onSubmit={create}><label>任务名称<input value={title} onChange={event => setTitle(event.target.value)} placeholder="例如：整理项目性能优化数据" required /></label><label>计划时间<input type="datetime-local" value={dueAt} onChange={event => setDueAt(event.target.value)} required /></label><label>准备说明<textarea rows={4} value={notes} onChange={event => setNotes(event.target.value)} placeholder="记录完成标准和所需材料" /></label><button className="primary">加入日程</button></form></aside>
      <section><div className="schedule-stats"><div><b>{data.pending}</b><span>待完成</span></div><div><b>{data.completed}</b><span>已完成</span></div><div><b>{data.items.length}</b><span>全部日程</span></div></div><div className="schedule-list">{data.items.map((item: any) => { const date = parts(item.due_at); return <article className={`panel schedule-item ${item.completed ? "done" : ""}`} key={item.id}><div className="schedule-date"><b>{date.day}</b><small>{date.month}</small></div><div className="schedule-copy"><h3>{item.title}</h3><p>{item.notes || "按计划完成该项准备任务。"}</p><span>{date.text}{item.company ? ` · ${item.company}` : ""}</span></div><div className="schedule-actions"><button onClick={() => toggle(item)}>{item.completed ? "恢复" : "完成"}</button>{item.task_type === "interview" && item.job_title && <button onClick={() => onInterview(item)}>模拟面试</button>}{item.task_type === "prepare" && <button className="danger" onClick={() => remove(item.id)}>删除</button>}</div></article>; })}{!data.items.length && <div className="panel report-empty schedule-empty"><div><Clock3 size={28} /><p>暂无日程。可在投递管理中设置面试时间，或创建准备事项。</p></div></div>}</div></section></div>
  </div>;
}
