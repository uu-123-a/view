import { useEffect, useState } from "react";
import { BarChart3, Bell, RotateCcw, Target } from "lucide-react";
import { apiFetch } from "../../services/api";
import type { Stage } from "../../types/interview";
import PageHead from "../shared/PageHead";

export default function NotificationCenter({ onUnread, onNavigate }: { onUnread: (count: number) => void; onNavigate: (target: Stage) => void }) {
  const [items, setItems] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState("");
  async function load() { try { const response = await apiFetch("/api/notifications", undefined, 10000); const data = await response.json(); if (!response.ok) throw new Error(data.error || "无法读取通知。"); setItems(data.items || []); setUnread(data.unread || 0); onUnread(data.unread || 0); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "无法读取通知。"); } }
  useEffect(() => { void load(); }, []);
  async function open(item: any) { if (!item.is_read) await apiFetch(`/api/notifications/${item.id}/read`, { method: "PATCH" }, 10000); await load(); onNavigate(item.target as Stage); }
  async function all() { await apiFetch("/api/notifications/read-all", { method: "POST" }, 10000); await load(); }
  const icon = (kind: string) => kind === "mistake" ? <RotateCcw size={20} /> : kind === "report" ? <BarChart3 size={20} /> : <Target size={20} />;
  return <div className="page narrow page-notifications"><PageHead eyebrow="NOTIFICATION CENTER" title="通知中心" description="集中查看训练任务、错题复盘和面试报告提醒。" />{error && <div className="admin-notice" role="alert">{error}</div>}<div className="notification-toolbar"><button className="secondary" disabled={!unread} onClick={all}>全部标为已读</button></div><div className="notification-list">{items.length ? items.map(item => <article key={item.id} className={`panel notification-item ${item.is_read ? "" : "unread"}`}><div className={`notification-icon ${item.kind}`}>{icon(item.kind)}</div><div className="notification-copy"><h3>{item.title}</h3><p>{item.content}</p><small>{String(item.created_at).replace("T", " ").slice(0, 16)} · {item.is_read ? "已读" : "未读"}</small></div><button className="notification-action" onClick={() => open(item)}>{item.target === "mistakes" ? "去复盘" : item.target === "history" ? "看报告" : "看计划"}</button></article>) : <div className="panel report-empty notification-empty"><div><Bell size={28} /><p>目前没有新的提醒。</p></div></div>}</div></div>;
}
