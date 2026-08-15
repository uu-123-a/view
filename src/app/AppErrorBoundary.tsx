import React from "react";
import { AlertTriangle, RotateCcw, Sparkles } from "lucide-react";
import "../error-boundary.css";

type State = { error: Error | null };

export default class AppErrorBoundary extends React.Component<React.PropsWithChildren, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("MOSS page error", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return <main className="app-error-page">
      <section className="app-error-card">
        <span className="app-error-brand"><Sparkles size={20} /> MOSS</span>
        <div className="app-error-icon"><AlertTriangle size={30} /></div>
        <h1>页面暂时没有正常显示</h1>
        <p>页面组件出现异常，但你的账号和训练记录没有丢失。重新加载即可继续。</p>
        <button onClick={() => window.location.reload()}><RotateCcw size={17} /> 重新加载页面</button>
        <details><summary>查看错误信息</summary><code>{this.state.error.message}</code></details>
      </section>
    </main>;
  }
}
