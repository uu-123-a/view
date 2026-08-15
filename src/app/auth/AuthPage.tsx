import { useState, type FormEvent } from "react";
import { ArrowRight, Bot, CheckCircle2, Eye, EyeOff, LockKeyhole, Mail, Sparkles, UserRound } from "lucide-react";
import { apiFetch } from "../../services/api";
import type { AuthUser } from "./types";

type Props = {
  onAuthenticated: (user: AuthUser) => void;
  onAdminMode: () => void;
};

export default function AuthPage({ onAuthenticated, onAdminMode }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const response = await apiFetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || "请求失败，请稍后重试。");
      onAuthenticated(result.user);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "无法连接后端服务。");
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(next: "login" | "register") {
    setMode(next);
    setError("");
    setPassword("");
  }

  return <div className="auth-page">
    <div className="auth-aurora auth-aurora-one" /><div className="auth-aurora auth-aurora-two" />
    <section className="auth-story">
      <div className="auth-brand"><span><Sparkles size={22} /></span><div><b>MOSS</b><small>AI INTERVIEW</small></div></div>
      <div className="auth-story-copy"><span className="auth-kicker">沉浸式 AI 模拟面试</span><h1>把每一次练习，<br />变成下一次面试的<strong>底气。</strong></h1><p>从岗位定制、语音作答到能力复盘，在安静、专注的空间里持续进步。</p></div>
      <div className="auth-features"><span><CheckCircle2 /> 本地 Whisper 语音识别</span><span><CheckCircle2 /> 个性化追问与反馈</span><span><CheckCircle2 /> 训练记录持续沉淀</span></div>
      <div className="auth-visual" aria-hidden="true"><div className="auth-ring ring-a" /><div className="auth-ring ring-b" /><div className="auth-core"><Bot size={38} /><i /><i /><i /></div></div>
    </section>
    <section className="auth-panel-wrap">
      <div className="auth-card">
        <div className="auth-mobile-brand"><Sparkles size={20} /> MOSS</div>
        <span className="auth-welcome">{mode === "login" ? "欢迎回来" : "创建训练档案"}</span>
        <h2>{mode === "login" ? "继续你的面试训练" : "从今天开始稳定进步"}</h2>
        <p>{mode === "login" ? "登录后继续上一次训练进度。" : "注册后即可进入你的专属面试空间。"}</p>
        <div className="auth-tabs" role="tablist"><button className={mode === "login" ? "active" : ""} onClick={() => switchMode("login")} type="button">登录</button><button className={mode === "register" ? "active" : ""} onClick={() => switchMode("register")} type="button">注册</button></div>
        <form className="auth-form" onSubmit={submit}>
          {mode === "register" && <label><span>昵称</span><div className="auth-input"><UserRound /><input value={name} onChange={event => setName(event.target.value)} placeholder="例如：林默" autoComplete="name" required minLength={2} maxLength={24} /></div></label>}
          <label><span>邮箱</span><div className="auth-input"><Mail /><input type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="name@example.com" autoComplete="email" required /></div></label>
          <label><span>密码</span><div className="auth-input"><LockKeyhole /><input type={showPassword ? "text" : "password"} value={password} onChange={event => setPassword(event.target.value)} placeholder={mode === "register" ? "至少 8 个字符" : "请输入密码"} autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={8} /><button type="button" onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? "隐藏密码" : "显示密码"}>{showPassword ? <EyeOff /> : <Eye />}</button></div></label>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="auth-submit" disabled={submitting}>{submitting ? "请稍候…" : mode === "login" ? "登录并进入 MOSS" : "注册并开始训练"}<ArrowRight /></button>
        </form>
        <small className="auth-security"><LockKeyhole /> 密码经过加密后保存在本机数据库中</small>
        <button type="button" className="admin-entry" onClick={onAdminMode}>管理员独立入口</button>
      </div>
    </section>
  </div>;
}
