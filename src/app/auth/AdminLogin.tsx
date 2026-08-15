import { useState, type FormEvent } from "react";
import { ArrowRight, LockKeyhole, Mail } from "lucide-react";
import { apiFetch } from "../../services/api";
import type { AuthUser } from "./types";

type Props = {
  onAuthenticated: (admin: AuthUser) => void;
  onBack: () => void;
};

export default function AdminLogin({ onAuthenticated, onBack }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const response = await apiFetch("/api/admin/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      }, 10000);
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || "管理员登录失败。");
      onAuthenticated(result.admin);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "无法连接后端服务。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page admin-login-page">
      <div className="auth-card admin-login-card">
        <span className="auth-logo"><LockKeyhole /></span>
        <span className="auth-welcome">MANAGEMENT CONSOLE</span>
        <h2>管理员独立登录</h2>
        <p>管理员身份来自独立的 admin.db，不与普通用户会话共享。</p>
        <form className="auth-form" onSubmit={submit}>
          <label><span>管理员邮箱</span><div className="auth-input"><Mail /><input type="email" value={email} onChange={event => setEmail(event.target.value)} required autoComplete="username" /></div></label>
          <label><span>管理员密码</span><div className="auth-input"><LockKeyhole /><input type="password" value={password} onChange={event => setPassword(event.target.value)} required autoComplete="current-password" /></div></label>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="auth-submit" disabled={submitting}>{submitting ? "正在登录…" : "进入管理后台"}<ArrowRight /></button>
        </form>
        <button type="button" className="admin-entry" onClick={onBack}>返回普通用户登录</button>
      </div>
    </div>
  );
}
