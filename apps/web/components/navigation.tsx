import Link from "next/link";

const links = [
  { href: "/", label: "Overview" },
  { href: "/documents", label: "Documents" },
  { href: "/chat", label: "Chat" }
];

export function Navigation() {
  return (
    <nav aria-label="Primary navigation" className="flex flex-wrap gap-2">
      {links.map((link) => (
        <Link
          className="rounded-md px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
          href={link.href}
          key={link.href}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
