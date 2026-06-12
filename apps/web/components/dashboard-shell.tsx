"use client";

import {
  Bell,
  Clock3,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Plus,
  Search,
  Settings,
  UserRound,
  Users,
  X
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  getSupabaseBrowserClient,
  getSupabaseSessionSafely
} from "@/lib/supabase";

type DashboardShellProps = {
  children: ReactNode;
  immersive?: boolean;
};

const navigationItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/account", label: "Settings", icon: Settings }
] as const;

export function DashboardShell({
  children,
  immersive = false
}: DashboardShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [displayName, setDisplayName] = useState("Account");
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    const client = supabase;
    let ignore = false;

    async function loadSession() {
      const session = await getSupabaseSessionSafely(client);
      const user = session?.user;
      const name =
        user?.user_metadata?.full_name ??
        user?.user_metadata?.name ??
        user?.email?.split("@")[0] ??
        "Account";

      if (!ignore) {
        setDisplayName(name);
      }
    }

    void loadSession();

    return () => {
      ignore = true;
    };
  }, [supabase]);

  async function handleLogout() {
    setIsSigningOut(true);

    if (supabase) {
      await supabase.auth.signOut();
    }

    router.replace("/login");
  }

  const sidebar = (
    <>
      <div className="border-b border-white/[0.06] px-5 py-5">
        <Link className="flex items-center gap-3" href="/">
          <span className="flex size-9 items-center justify-center rounded-lg bg-blue-500 text-sm font-bold text-white shadow-lg shadow-blue-500/20">
            A
          </span>
          <span>
            <span className="block text-sm font-semibold text-white">
              Averion.ai
            </span>
            <span className="block text-[11px] text-zinc-500">
              Knowledge Copilot
            </span>
          </span>
        </Link>
      </div>

      <div className="px-5 py-5">
        <Link
          className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-blue-500 text-xs font-semibold text-white shadow-lg shadow-blue-500/15 transition hover:bg-blue-600"
          href="/chat"
          onClick={() => setIsMenuOpen(false)}
        >
          <Plus aria-hidden="true" size={16} />
          New Chat
        </Link>
      </div>

      <nav
        aria-label="Workspace navigation"
        className="flex-1 space-y-1 overflow-y-auto px-2"
      >
        {navigationItems.map(({ href, icon: Icon, label }) => {
          const isActive =
            href === "/" ? pathname === href : pathname.startsWith(href);

          return (
            <Link
              className={`flex h-12 items-center gap-3 rounded-r-md border-l-4 px-4 text-xs font-semibold transition ${
                isActive
                  ? "border-blue-500 bg-zinc-800 text-white"
                  : "border-transparent text-zinc-400 hover:bg-zinc-900 hover:text-white"
              }`}
              href={href}
              key={href}
              onClick={() => setIsMenuOpen(false)}
            >
              <Icon
                aria-hidden="true"
                className={isActive ? "text-blue-500" : ""}
                size={19}
              />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/[0.06] p-4">
        <button
          className="flex h-11 w-full items-center gap-3 rounded-md px-4 text-left text-xs font-semibold text-zinc-400 transition hover:bg-zinc-900 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSigningOut}
          onClick={handleLogout}
          type="button"
        >
          <LogOut aria-hidden="true" size={18} />
          {isSigningOut ? "Signing out..." : "Log Out"}
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-[#111111] text-zinc-100">
      <aside className="fixed inset-y-0 left-0 z-50 hidden w-[280px] flex-col border-r border-white/[0.06] bg-[#111111] md:flex">
        {sidebar}
      </aside>

      {isMenuOpen && (
        <div className="fixed inset-0 z-[70] md:hidden">
          <button
            aria-label="Close navigation"
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setIsMenuOpen(false)}
            type="button"
          />
          <aside className="relative flex h-full w-[min(86vw,300px)] flex-col border-r border-white/10 bg-[#111111] shadow-2xl">
            <button
              aria-label="Close navigation"
              className="absolute right-3 top-3 rounded-md p-2 text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
              onClick={() => setIsMenuOpen(false)}
              type="button"
            >
              <X size={18} />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <header
        className={`fixed inset-x-0 top-0 z-40 h-16 items-center border-b border-white/[0.06] bg-[#111111]/90 px-4 backdrop-blur-xl md:left-[280px] md:px-8 ${
          immersive ? "flex md:hidden" : "flex"
        }`}
      >
        <button
          aria-label="Open navigation"
          className="mr-3 rounded-md p-2 text-zinc-400 transition hover:bg-zinc-800 hover:text-white md:hidden"
          onClick={() => setIsMenuOpen(true)}
          type="button"
        >
          <Menu size={20} />
        </button>

        <Link
          className="mr-4 flex items-center gap-2 md:hidden"
          href="/"
          onClick={() => setIsMenuOpen(false)}
        >
          <span className="flex size-8 items-center justify-center rounded-md bg-blue-500 text-xs font-bold text-white">
            A
          </span>
          <span className="text-sm font-semibold">Averion.ai</span>
        </Link>

        <form
          action="/documents"
          className="relative hidden w-72 focus-within:ring-2 focus-within:ring-blue-500/40 lg:block"
        >
          <Search
            aria-hidden="true"
            className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
            size={16}
          />
          <input
            aria-label="Search knowledge base"
            className="h-9 w-full rounded-md border border-white/10 bg-[#0d0d0d] pl-9 pr-3 text-xs text-zinc-200 outline-none transition placeholder:text-zinc-600 focus:border-blue-500/60"
            name="search"
            placeholder="Search knowledge base..."
            type="search"
          />
        </form>

        <div className="ml-auto flex items-center gap-1 sm:gap-2">
          <button
            aria-label="Notifications"
            className="relative rounded-md p-2 text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
            title="Notifications"
            type="button"
          >
            <Bell size={18} />
            <span className="absolute right-2 top-1.5 size-1.5 rounded-full bg-blue-500" />
          </button>
          <Link
            aria-label="Conversation history"
            className="rounded-md p-2 text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
            href="/chat"
            title="Conversation history"
          >
            <Clock3 size={18} />
          </Link>
          <span className="mx-2 hidden h-6 w-px bg-white/10 sm:block" />
          <Link
            className="hidden h-8 items-center gap-2 rounded-md border border-white/10 bg-zinc-900 px-3 text-[11px] font-semibold text-zinc-200 transition hover:border-blue-500/40 hover:bg-zinc-800 sm:flex"
            href="/account"
          >
            <Users size={14} />
            Invite Team
          </Link>
          <Link
            aria-label={`Open ${displayName} account`}
            className="ml-1 flex size-8 items-center justify-center rounded-full border border-white/10 bg-zinc-800 text-zinc-300 transition hover:border-blue-500/50 hover:text-white"
            href="/account"
            title={displayName}
          >
            <UserRound size={15} />
          </Link>
        </div>
      </header>

      <main
        className={
          immersive
            ? "min-h-screen pt-16 md:ml-[280px] md:pt-0"
            : "min-h-screen px-4 pb-12 pt-24 md:ml-[280px] md:px-8"
        }
      >
        {children}
      </main>
    </div>
  );
}
