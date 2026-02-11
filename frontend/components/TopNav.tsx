import Link from "next/link";

const navItems = [
  { href: "/", label: "主页" },
  { href: "/assets", label: "财产记录" },
  { href: "/tasks", label: "任务栏" },
  { href: "/knowledge", label: "知识库" },
  { href: "/settings", label: "选项" }
];

export function TopNav() {
  return (
    <nav className="top-nav">
      <Link className="brand" href="/">
        AI LIFE NOTEBOOK
      </Link>
      <div className="nav-links">
        {navItems.map((item) => (
          <Link className="nav-link" href={item.href} key={item.href}>
            {item.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
