import { Sparkles } from "lucide-react";

export default function AuthLoading() {
  return (
    <div className="auth-page">
      <div className="auth-loading">
        <span className="auth-logo"><Sparkles size={24} /></span>
        <b>MOSS</b>
        <p>正在加载你的面试空间…</p>
      </div>
    </div>
  );
}
