import { cloneElement, type ReactElement } from "react";

export default function AppNavItem({ icon, label, active, onClick }: { icon: ReactElement; label: string; active: boolean; onClick: () => void }) {
  return <button className={active ? "nav-item active" : "nav-item"} onClick={onClick}>{cloneElement(icon, { size: 19 } as Record<string, number>)}<span>{label}</span></button>;
}
