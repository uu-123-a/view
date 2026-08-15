import React, { useEffect, useMemo, useRef, useState } from "react";
import { BarChart3, Bell, BookOpen, Bot, BriefcaseBusiness, Clock3, FileText, History, Home, LockKeyhole, LogOut, RotateCcw, Sparkles, Target, TrendingUp, UserRound } from "lucide-react";
import { questions } from "../data/interview";
import type { Message, Stage } from "../types/interview";
import { speak } from "../utils/speech";
import "../speech.css";
import "../auth.css";
import "../persistence.css";
import "../resume.css";
import "../mistakes.css";
import "../jobs.css";
import "../profile.css";
import "../admin-jobs.css";
import "../notifications.css";
import "../resume-center.css";
import "../career.css";
import "../knowledge.css";
import "../applications.css";
import "../schedule.css";
import "../review-notes.css";
import { apiFetch } from "../services/api";
import AuthLoading from "./auth/AuthLoading";
import type { AuthUser } from "./auth/types";
import AppNavItem from "./shared/AppNavItem";

const AuthPage = React.lazy(() => import("./auth/AuthPage"));
const AdminLogin = React.lazy(() => import("./auth/AdminLogin"));
const ScheduleCenter = React.lazy(() => import("./careers/ScheduleCenter"));
const ApplicationBoard = React.lazy(() => import("./careers/ApplicationBoard"));
const JobCenter = React.lazy(() => import("./careers/JobCenter"));
const KnowledgeGraph = React.lazy(() => import("./growth/KnowledgeGraph"));
const CareerAssistant = React.lazy(() => import("./growth/CareerAssistant"));
const ResumeCenter = React.lazy(() => import("./growth/ResumeCenter"));
const ProfileCenter = React.lazy(() => import("./records/ProfileCenter"));
const NotificationCenter = React.lazy(() => import("./records/NotificationCenter"));
const MistakeBook = React.lazy(() => import("./records/MistakeBook"));
const ReviewNotes = React.lazy(() => import("./records/ReviewNotes"));
const QuestionAdmin = React.lazy(() => import("./admin/QuestionAdmin"));
const JobAdmin = React.lazy(() => import("./admin/JobAdmin"));
const SystemAdmin = React.lazy(() => import("./admin/SystemAdmin"));
const AnalyticsDashboard = React.lazy(() => import("./admin/AnalyticsDashboard"));
const Setup = React.lazy(() => import("./interview/InterviewSetup"));
const Interview = React.lazy(() => import("./interview/InterviewRoom"));
const Report = React.lazy(() => import("./interview/InterviewReport"));
const EmotionReport = React.lazy(() => import("./interview/EmotionReport"));
const HistoryView = React.lazy(() => import("./interview/HistoryView"));
const Dashboard = React.lazy(() => import("./home/HomeDashboard"));

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [admin, setAdmin] = useState<AuthUser | null>(null);
  const [adminLogin, setAdminLogin] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [stage, setStage] = useState<Stage>("home");
  const [role, setRole] = useState("多模态算法工程师");
  const [level, setLevel] = useState("校招 / 初级");
  const [interviewType, setInterviewType] = useState("技术面");
  const [difficulty, setDifficulty] = useState("中等");
  const [questionStrategy, setQuestionStrategy] = useState("spark_first");
  const [resume, setResume] = useState("熟悉 Python、PyTorch 与 Transformer；有视觉语言模型微调、RAG 应用开发和模型部署经验。");
  const [messages, setMessages] = useState<Message[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [maxQuestions, setMaxQuestions] = useState(5);
  const [answer, setAnswer] = useState("");
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [thinking, setThinking] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [report, setReport] = useState<any>(null);
  const [interviewError, setInterviewError] = useState("");
  const [history, setHistory] = useState<any[]>([]);
  const [practiceProgress, setPracticeProgress] = useState<any[]>([]);
  const [trainingPlan, setTrainingPlan] = useState<any>({plan:null,tasks:[]});
  const [notificationCount,setNotificationCount]=useState(0);
  const [sessionMode, setSessionMode] = useState<"interview" | "practice">("interview");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([apiFetch("/api/auth/me",undefined,8000).then(r=>r.ok?r.json():{user:null}).catch(()=>({user:null})),apiFetch("/api/admin/auth/me",undefined,8000).then(r=>r.ok?r.json():{admin:null}).catch(()=>({admin:null}))]).then(([u,a])=>{setUser(u.user);setAdmin(a.admin);if(a.admin)setStage("analytics")}).finally(()=>setAuthLoading(false));
  }, []);

  useEffect(() => {
    if (!user) return;
    apiFetch("/api/interviews/history", undefined, 10000)
      .then(async (response) => response.ok ? response.json() : { items: [] })
      .then((result) => setHistory(Array.isArray(result.items) ? result.items : []))
      .catch(() => setHistory([]));
  }, [user]);

  useEffect(()=>{if(!user)return;apiFetch('/api/training-plan',undefined,10000).then(async r=>r.ok?r.json():{plan:null,tasks:[]}).then(setTrainingPlan).catch(()=>setTrainingPlan({plan:null,tasks:[]}))},[user]);
  useEffect(()=>{if(!user)return;apiFetch('/api/notifications',undefined,10000).then(async r=>r.ok?r.json():{unread:0}).then(j=>setNotificationCount(j.unread||0)).catch(()=>setNotificationCount(0))},[user,stage]);

  async function saveTrainingPlan(values:any){const r=await apiFetch('/api/training-plan',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)},10000);const j=await r.json();if(!r.ok)throw new Error(j.error);setTrainingPlan(j)}
  async function toggleTrainingTask(id:number,completed:boolean){const r=await apiFetch(`/api/training-plan/tasks/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({completed})},10000);const j=await r.json();if(r.ok)setTrainingPlan(j.data)}

  useEffect(() => {
    if (!user) return;
    apiFetch("/api/interviews/practice-progress", undefined, 10000)
      .then(async response => response.ok ? response.json() : { items: [] })
      .then(result => setPracticeProgress(Array.isArray(result.items) ? result.items : []))
      .catch(() => setPracticeProgress([]));
  }, [user]);

  useEffect(() => {
    if (!recording) return;
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [recording]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const progress = useMemo(() => Math.min(100, ((questionIndex + 1) / maxQuestions) * 100), [questionIndex, maxQuestions]);

  async function startInterviewSession(options?: { initialQuestion?: string; focusSkill?: string }) {
    const practice = Boolean(options?.initialQuestion);
    setSessionMode(practice ? "practice" : "interview");
    setQuestionIndex(0);
    setMaxQuestions(practice ? 3 : 5);
    setSeconds(0);
    setReport(null);
    setInterviewError("");
    setMessages([]);
    setThinking(true);
    setStage("interview");
    try {
      const response = await apiFetch("/api/interviews/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role, level, interview_type: practice ? "专项训练" : interviewType, resume,
          mode: practice ? "practice" : "interview",
          initial_question: options?.initialQuestion || "",
          focus_skill: options?.focusSkill || "",
          difficulty,
          question_strategy: questionStrategy,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "无法创建面试会话。");
      setSessionId(result.session_id);
      setMaxQuestions(Number(result.max_questions) || (practice ? 3 : 5));
      setInterviewError(result.source === "fallback" ? "讯飞星火未连接，当前使用本地题库。" : "");
      setMessages([{ role: "ai", text: result.question }]);
      speak(result.question);
    } catch (reason) {
      setSessionId("");
      setInterviewError(reason instanceof Error ? reason.message : "星火服务连接失败，已使用本地题库。");
      setMessages([{ role: "ai", text: questions[0] }]);
      speak(questions[0]);
    } finally {
      setThinking(false);
    }
  }

  function beginInterview() {
    return startInterviewSession();
  }

  function beginPractice(question: string, focusSkill: string) {
    return startInterviewSession({ initialQuestion: question, focusSkill });
  }

  async function submitAnswer() {
    if (!answer.trim() || thinking) return;
    const current = answer.trim();
    setMessages((m) => [...m, { role: "user", text: current }]);
    setAnswer("");
    setRecording(false);
    setThinking(true);
    try {
      if (sessionId) {
        const response = await apiFetch(`/api/interviews/sessions/${sessionId}/answers`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answer: current, duration_seconds: seconds }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "提交回答失败。");
        if (result.evaluation) {
          setMessages((currentMessages) => {
            const nextMessages = [...currentMessages];
            for (let index = nextMessages.length - 1; index >= 0; index -= 1) {
              if (nextMessages[index].role === "user" && !nextMessages[index].evaluation) {
                nextMessages[index] = { ...nextMessages[index], evaluation: result.evaluation };
                break;
              }
            }
            return nextMessages;
          });
        }
        if (result.complete) {
          const reportResponse = await apiFetch(`/api/interviews/sessions/${sessionId}/report`, undefined, 45000);
          const generatedReport = await reportResponse.json();
          if (!reportResponse.ok) throw new Error(generatedReport.error || "生成报告失败。");
          setReport(generatedReport);
          if (sessionMode === "interview") {
            setHistory((h) => [{ id: sessionId, date: new Date().toISOString().slice(0, 10), role, score: generatedReport.score, type: interviewType, duration_seconds: seconds }, ...h]);
          } else {
            apiFetch("/api/interviews/practice-progress", undefined, 10000)
              .then(async progressResponse => progressResponse.ok ? progressResponse.json() : { items: [] })
              .then(progressResult => setPracticeProgress(Array.isArray(progressResult.items) ? progressResult.items : []))
              .catch(() => undefined);
          }
          setStage("report");
          return;
        }
        setQuestionIndex(result.question_number - 1);
        setInterviewError(result.source === "fallback" ? "讯飞星火未连接，当前使用本地题库。" : "");
        setMessages((m) => [...m, { role: "ai", text: result.next_question }]);
        speak(result.next_question);
        return;
      }

      if (questionIndex >= questions.length - 1) {
        setStage("report");
        return;
      }
      const next = questionIndex + 1;
      setQuestionIndex(next);
      setMessages((m) => [...m, { role: "ai", text: questions[next] }]);
      speak(questions[next]);
    } catch (reason) {
      setInterviewError(reason instanceof Error ? reason.message : "AI 面试服务暂时不可用。");
      const next = Math.min(questionIndex + 1, questions.length - 1);
      if (next === questionIndex) setStage("report");
      else {
        setQuestionIndex(next);
        setMessages((m) => [...m, { role: "ai", text: questions[next] }]);
      }
    } finally {
      setThinking(false);
    }
  }

  async function logout() {
    await apiFetch(admin ? "/api/admin/auth/logout" : "/api/auth/logout", { method: "POST" }, 8000).catch(() => undefined);
    setUser(null);
    setAdmin(null);
    setStage("home");
  }

  async function openHistoryReport(item: any) {
    try {
      const response = await apiFetch(`/api/interviews/sessions/${item.id}/report`, undefined, 15000);
      const savedReport = await response.json();
      if (!response.ok) throw new Error(savedReport.error || "无法读取报告。");
      setRole(item.role);
      setReport(savedReport);
      setStage("report");
    } catch (reason) {
      setInterviewError(reason instanceof Error ? reason.message : "无法读取历史报告。");
    }
  }

  if (authLoading) return <AuthLoading />;
  if (!user && !admin) return adminLogin ? <AdminLogin onAuthenticated={a=>{setAdmin(a);setStage("analytics")}} onBack={()=>setAdminLogin(false)}/> : <AuthPage onAuthenticated={setUser} onAdminMode={()=>setAdminLogin(true)}/>;
  const identity=(admin||user)!;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setStage("home")}>
          <span className="brand-mark"><Sparkles size={20} /></span>
          <span><b>MOSS</b><small>AI INTERVIEW</small></span>
        </button>
        <nav>
          <AppNavItem icon={<Home />} label="首页" active={stage === "home"} onClick={() => setStage("home")} />
          {user && <AppNavItem icon={<UserRound />} label="个人中心" active={stage === "profile"} onClick={() => setStage("profile")} />}
          {user && <AppNavItem icon={<BookOpen />} label="复盘笔记" active={stage === "reviewNotes"} onClick={() => setStage("reviewNotes")} />}
          {user && <AppNavItem icon={<Clock3 />} label="面试日程" active={stage === "schedule"} onClick={() => setStage("schedule")} />}
          {user && <AppNavItem icon={<BriefcaseBusiness />} label="投递管理" active={stage === "applications"} onClick={() => setStage("applications")} />}
          {user && <AppNavItem icon={<Target />} label="知识图谱" active={stage === "knowledge"} onClick={() => setStage("knowledge")} />}
          {user && <AppNavItem icon={<Sparkles />} label="职业助手" active={stage === "career"} onClick={() => setStage("career")} />}
          {user && <AppNavItem icon={<FileText />} label="简历优化" active={stage === "resumeCenter"} onClick={() => setStage("resumeCenter")} />}
          {user && <div className="notification-nav"><AppNavItem icon={<Bell />} label="通知中心" active={stage === "notifications"} onClick={() => setStage("notifications")} />{notificationCount>0&&<i className="notification-badge">{notificationCount>99?"99+":notificationCount}</i>}</div>}
          {user && <AppNavItem icon={<BriefcaseBusiness />} label="岗位中心" active={stage === "jobs"} onClick={() => setStage("jobs")} />}
          <AppNavItem icon={<Bot />} label="模拟面试" active={stage === "setup" || stage === "interview"} onClick={() => setStage("setup")} />
          <AppNavItem icon={<BarChart3 />} label="面试报告" active={stage === "report"} onClick={() => setStage("report")} />
          <AppNavItem icon={<History />} label="成长轨迹" active={stage === "history"} onClick={() => setStage("history")} />
          {user && <AppNavItem icon={<RotateCcw />} label="错题本" active={stage === "mistakes"} onClick={() => setStage("mistakes")} />}
          {admin && <AppNavItem icon={<BookOpen />} label="题库管理" active={stage === "admin"} onClick={() => setStage("admin")} />}
          {admin && <AppNavItem icon={<BriefcaseBusiness />} label="岗位管理" active={stage === "adminJobs"} onClick={() => setStage("adminJobs")} />}
          {admin && <AppNavItem icon={<LockKeyhole />} label="系统设置" active={stage === "system"} onClick={() => setStage("system")} />}
          {admin && <AppNavItem icon={<TrendingUp />} label="数据统计" active={stage === "analytics"} onClick={() => setStage("analytics")} />}
        </nav>
        <div className="side-tip">
          <span><Sparkles size={16} /> 今日建议</span>
          <p>用 STAR 法则描述项目，比罗列技术栈更有说服力。</p>
        </div>
        <div className="profile"><div className="avatar">{identity.name.slice(0, 1)}</div><span><b>{identity.name}</b><small>{admin ? "管理员 · " : ""}{identity.email}</small></span><button className="logout-button" onClick={logout} title="退出登录" aria-label="退出登录"><LogOut size={17} /></button></div>
      </aside>

      <main>
        {stage === "home" && user && <Dashboard onStart={() => setStage("setup")} onShowAll={() => setStage("history")} onOpenReport={openHistoryReport} history={history} user={user} trainingPlan={trainingPlan} onSavePlan={saveTrainingPlan} onToggleTask={toggleTrainingTask} />}
        {stage === "profile" && user && <ProfileCenter currentUser={user} onUserChanged={setUser} />}
        {stage === "reviewNotes" && user && <ReviewNotes onOpenReport={openHistoryReport} />}
        {stage === "schedule" && user && <ScheduleCenter onInterview={(item:any)=>{setRole(item.job_title);setStage("setup")}} />}
        {stage === "applications" && user && <ApplicationBoard onInterview={(item:any)=>{setRole(item.title);setResume(current=>`${current}\n目标岗位：${item.title}`);setStage("setup")}} />}
        {stage === "knowledge" && user && <KnowledgeGraph onPractice={beginPractice} />}
        {stage === "career" && user && <CareerAssistant />}
        {stage === "resumeCenter" && user && <ResumeCenter />}
        {stage === "notifications" && user && <NotificationCenter onUnread={setNotificationCount} onNavigate={(target:Stage)=>setStage(target)} />}
        {stage === "jobs" && user && <JobCenter onInterview={(job:any)=>{setRole(job.title);setResume(current=>`${current}\n目标岗位：${job.title}；岗位技能：${job.skills.join("、")}。`);setStage("setup")}} />}
        {stage === "setup" && (
          <Setup
            role={role} setRole={setRole} level={level} setLevel={setLevel}
            interviewType={interviewType} setInterviewType={setInterviewType}
            difficulty={difficulty} setDifficulty={setDifficulty}
            questionStrategy={questionStrategy} setQuestionStrategy={setQuestionStrategy}
            resume={resume} setResume={setResume} onStart={beginInterview}
          />
        )}
        {stage === "interview" && (
          <Interview
            role={role} type={sessionMode === "practice" ? "专项训练" : interviewType} messages={messages} progress={progress} maxQuestions={maxQuestions}
            answer={answer} setAnswer={setAnswer} recording={recording}
            setRecording={setRecording} seconds={seconds}
            thinking={thinking} submit={submitAnswer} onExit={() => setStage("setup")}
            bottomRef={bottomRef} interviewError={interviewError}
          />
        )}
        {stage === "report" && <><Report role={role} report={report} onAgain={() => setStage("setup")} onPractice={beginPractice} practiceProgress={practiceProgress} /><div className="emotion-report-shell"><EmotionReport summary={report?.emotion_summary} /></div></>}
        {stage === "history" && <HistoryView history={history} onOpenReport={openHistoryReport} />}
        {stage === "mistakes" && user && <MistakeBook />}
        {stage === "admin" && admin && <QuestionAdmin />}
        {stage === "adminJobs" && admin && <JobAdmin />}
        {stage === "system" && admin && <SystemAdmin currentUser={admin} />}
        {stage === "analytics" && admin && <AnalyticsDashboard />}
      </main>
    </div>
  );
}
