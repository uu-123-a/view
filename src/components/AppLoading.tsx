import { Sparkles } from "lucide-react";

export default function AppLoading() {
  return (
    <main className="app-loading-page" aria-busy="true" aria-label="应用加载中">
      <section className="app-loading-card">
        <span className="app-loading-brand"><Sparkles size={21} /> MOSS</span>
        <div className="app-loading-line app-loading-line-title" />
        <div className="app-loading-line" />
        <div className="app-loading-line app-loading-line-short" />
        <p>正在加载面试工作台…</p>
      </section>
    </main>
  );
}
