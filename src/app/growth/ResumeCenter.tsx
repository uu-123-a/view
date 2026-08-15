import { useEffect, useState } from "react";
import { apiFetch } from "../../services/api";
import PageHead from "../shared/PageHead";

export default function ResumeCenter() {
  const [resumes, setResumes] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [selected, setSelected] = useState("");
  const [jobId, setJobId] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");

  async function load() {
    try {
      const [resumeResponse, jobResponse, historyResponse] = await Promise.all([apiFetch("/api/resumes", undefined, 10000), apiFetch("/api/jobs", undefined, 10000), apiFetch("/api/resumes/optimizations", undefined, 10000)]);
      const [resumeData, jobData, historyData] = await Promise.all([resumeResponse.json(), jobResponse.json(), historyResponse.json()]);
      if (!resumeResponse.ok || !jobResponse.ok || !historyResponse.ok) throw new Error(resumeData.error || jobData.error || historyData.error || "无法读取简历资料。");
      setResumes(resumeData.items || []); setJobs(jobData.items || []); setHistory(historyData.items || []);
      if (!selected && resumeData.items?.length) setSelected(resumeData.items[0].id);
      if (!jobId && jobData.items?.length) setJobId(String(jobData.items[0].id));
    } catch (reason) { setNotice(reason instanceof Error ? reason.message : "无法读取简历资料。"); }
  }
  useEffect(() => { void load(); }, []);
  async function optimize() { if (!selected || !jobId) return; setLoading(true); setNotice(""); try { const response = await apiFetch(`/api/resumes/${selected}/optimize`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_id: Number(jobId) }) }, 60000); const data = await response.json(); if (response.ok) { setResult(data.optimization.result); await load(); } else setNotice(data.error); } finally { setLoading(false); } }
  async function rename(item: any) { const name = window.prompt("请输入新的简历名称", item.filename); if (!name) return; const response = await apiFetch(`/api/resumes/${item.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename: name }) }, 10000); if (response.ok) await load(); }
  async function remove(item: any) { if (!window.confirm(`确定删除 ${item.filename} 吗？`)) return; const response = await apiFetch(`/api/resumes/${item.id}`, { method: "DELETE" }, 10000); if (response.ok) { if (selected === item.id) setSelected(""); setResult(null); await load(); } }
  function copy() { navigator.clipboard?.writeText(result?.optimized_summary || "").then(() => setNotice("优化文本已复制。")); }

  return <div className="page narrow page-resume-center"><PageHead eyebrow="AI RESUME LAB" title="简历优化中心" description="选择一份简历和目标岗位，由星火分析关键词差距并生成忠于原经历的优化文本。" /><div className="resume-center-layout"><aside className="panel resume-library"><div className="panel-title"><div><span>简历库</span><h3>我的简历</h3></div><span className="pill">{resumes.length} 份</span></div><div className="resume-library-list">{resumes.map(item => <div key={item.id} className={`resume-library-item ${selected === item.id ? "active" : ""}`} onClick={() => { setSelected(item.id); setResult(null); }}><b>{item.filename}</b><small>{String(item.file_type).toUpperCase()} · {String(item.created_at).slice(0, 10)}</small><div className="resume-library-actions"><button onClick={event => { event.stopPropagation(); void rename(item); }}>重命名</button><button className="danger" onClick={event => { event.stopPropagation(); void remove(item); }}>删除</button></div></div>)}{!resumes.length && <div className="report-empty compact">请先在模拟面试设置中上传简历。</div>}</div></aside><section className="panel resume-workspace"><div className="panel-title"><div><span>岗位定向优化</span><h3>匹配分析与改写建议</h3></div></div><div className="resume-optimizer-form"><label>目标岗位<select value={jobId} onChange={event => setJobId(event.target.value)}>{jobs.map(job => <option value={job.id} key={job.id}>{job.title} · {job.company}</option>)}</select></label><button className="primary" disabled={!selected || !jobId || loading} onClick={optimize}>{loading ? "星火正在分析…" : "开始优化"}</button></div>{notice && <div className="profile-notice" role="status">{notice}</div>}{result && <><div className="optimization-score"><strong>{result.match_score}%</strong><span>岗位匹配度<br />{result.source === "spark" ? "讯飞星火分析" : "本地降级分析"}</span></div><div className="keyword-groups"><div className="keyword-group"><h4>已匹配关键词</h4><div className="job-tags">{result.matched_keywords.map((text: string) => <span key={text}>{text}</span>)}</div></div><div className="keyword-group"><h4>建议补强关键词</h4><div className="job-tags">{result.missing_keywords.map((text: string) => <span key={text}>{text}</span>)}</div></div></div><ul className="optimization-suggestions">{result.suggestions.map((text: string) => <li key={text}>{text}</li>)}</ul><div className="optimized-copy"><header><h3>优化文本</h3><button className="secondary" onClick={copy}>复制文本</button></header><textarea value={result.optimized_summary} readOnly /></div></>}</section></div><section className="panel optimization-history"><div className="panel-title"><div><span>优化记录</span><h3>最近岗位匹配</h3></div><span className="pill">{history.length} 次</span></div>{history.map(item => <div className="optimization-history-row" key={item.id}><div><b>{item.target_role}</b><small>{item.filename} · {String(item.created_at).slice(0, 16)}</small></div><strong>{item.match_score}%</strong></div>)}{!history.length && <div className="report-empty compact">完成第一次岗位定向优化后，记录会出现在这里。</div>}</section></div>;
}
