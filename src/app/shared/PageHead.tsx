type Props = { eyebrow: string; title: string; description: string };

export default function PageHead({ eyebrow, title, description }: Props) {
  return <header className="page-head"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div><div className="head-status"><span className="live-dot" /> AI 服务正常</div></header>;
}
