"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  getSupabaseBrowserClient,
  getSupabaseSessionSafely
} from "@/lib/supabase";

const links = [
  { href: "/", label: "Overview" },
  { href: "/documents", label: "Documents" },
  { href: "/chat", label: "Chat" },
  { href: "/account", label: "Account" }
];

export function Navigation() {
  const router = useRouter();
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [email, setEmail] = useState<string | null>(null);
  const [isSigningOut, setIsSigningOut] = useState(false);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    const client = supabase;
    let ignore = false;

    async function loadSession() {
      const session = await getSupabaseSessionSafely(client);

      if (!ignore) {
        setEmail(session?.user.email ?? null);
      }
    }

    const {
      data: { subscription }
    } = client.auth.onAuthStateChange((_event, session) => {
      setEmail(session?.user.email ?? null);
    });

    void loadSession();

    return () => {
      ignore = true;
      subscription.unsubscribe();
    };
  }, [supabase]);

  async function handleLogout() {
    if (!supabase) {
      router.replace("/login");
      return;
    }

    setIsSigningOut(true);
    await supabase.auth.signOut();
    router.replace("/login");
  }

  return (
    <nav
      aria-label="Primary navigation"
      className="flex flex-wrap items-center gap-2"
    >
      <div className="flex flex-wrap gap-2">
        {links.map((link) => (
          <Link
            className="rounded-md px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
            href={link.href}
            key={link.href}
          >
            {link.label}
          </Link>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-slate-200 pt-2 sm:border-l sm:border-t-0 sm:pl-3 sm:pt-0">
        {email && (
          <span className="max-w-44 truncate rounded-md bg-slate-100 px-3 py-2 text-xs font-medium text-slate-600">
            {email}
          </span>
        )}
        <button
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSigningOut}
          onClick={handleLogout}
          type="button"
        >
          {isSigningOut ? "Signing out..." : "Logout"}
        </button>
      </div>
    </nav>
  );
}
