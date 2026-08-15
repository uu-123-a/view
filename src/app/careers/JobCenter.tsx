import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { apiFetch } from "../../services/api";
import PageHead from "../shared/PageHead";

export default function JobCenter({ onInterview }: { onInterview: (job: any) => void }) {
  const [items, setItems] = useState<any[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [detail, setDetail] = useState<any>(null);
  const [keyword, setKeyword] = useState("");
  const [city, setCity] = useState("");
  const [notice, setNotice] = useState("");

  async function open(job: any) { setSelected(job); const response = await apiFetch(`/api/jobs/${job.id}`, undefined, 10000); const result = await response.json(); if (response.ok) setDetail(result); else setNotice(result.error); }
  async function load() { const response = await apiFetch(`/api/jobs?search=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}`, undefined, 10000); const result = await response.json(); if (!response.ok) return setNotice(result.error); setItems(result.items || []); setCities(result.cities || []); setNotice(""); if (result.items?.length) await open(result.items[0]); else { setSelected(null); setDetail(null); } }
  useEffect(() => { void load(); }, []);
  async function toggle() { if (!detail) return; const response = await apiFetch(`/api/jobs/${detail.job.id}/save`, { method: "POST" }, 10000); const result = await response.json(); if (response.ok) { setDetail({ ...detail, job: { ...detail.job, saved: result.saved } }); setItems(current => current.map(job => job.id === detail.job.id ? { ...job, saved: result.saved } : job)); } else setNotice(result.error); }

  return <div className="page narrow page-jobs"><PageHead eyebrow="JOB MATCH" title="岗位中心与简历匹配" description="浏览目标岗位，查看技能差距，并一键进入针对性模拟面试。" />
    <div className="job-toolbar"><input value={keyword} onChange={event => setKeyword(event.target.value)} onKeyDown={event => { if (event.key === "Enter") void load(); }} placeholder="搜索岗位、公司或技能" /><select value={city} onChange={event => setCity(event.target.value)}><option value="">全部城市</option>{cities.map(value => <option key={value}>{value}</option>)}</select><button className="secondary" onClick={load}>搜索岗位</button></div>
    {notice && <div className="admin-notice" role="alert">{notice}</div>}
    <div className="job-layout"><section className="job-list">{items.map(job => <button key={job.id} className={`job-item ${selected?.id === job.id ? "active" : ""}`} onClick={() => open(job)}><header><div><h3>{job.title}</h3><p>{job.company} · {job.city} · {job.experience}</p></div><strong>{job.salary}</strong></header><div className="job-tags">{job.skills.slice(0, 4).map((skill: string) => <span key={skill}>{skill}</span>)}{job.saved && <span>已收藏</span>}</div></button>)}{!items.length && <div className="panel report-empty">没有找到符合条件的岗位。</div>}</section>
      {detail && <aside className="panel job-detail"><header><div><span className="eyebrow">{detail.job.company}</span><h2>{detail.job.title}</h2><p>{detail.job.city} · {detail.job.salary} · {detail.job.experience} · {detail.job.education}</p></div><button className={`save-job ${detail.job.saved ? "saved" : ""}`} onClick={toggle}>{detail.job.saved ? "已收藏" : "收藏"}</button></header><p className="job-description">{detail.job.description}</p><div className="job-tags">{detail.job.skills.map((skill: string) => <span key={skill}>{skill}</span>)}</div><div className="match-box"><div className="match-score"><strong>{detail.match.score}%</strong><span>简历技能匹配度<br />{detail.resume ? `基于 ${detail.resume.filename}` : "尚未上传简历"}</span></div><p>{detail.match.advice}</p><div className="match-groups"><div><small>已匹配</small><div className="job-tags">{detail.match.matched.length ? detail.match.matched.map((skill: string) => <span key={skill}>{skill}</span>) : <span>暂无</span>}</div></div><div><small>建议补强</small><div className="job-tags">{detail.match.missing.map((skill: string) => <span key={skill}>{skill}</span>)}</div></div></div></div><div className="job-actions"><button className="primary" onClick={() => onInterview(detail.job)}>针对该岗位面试<ArrowRight size={16} /></button></div></aside>}
    </div>
  </div>;
}
