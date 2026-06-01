"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useMemo, useState } from "react";

import {
  getSupabaseBrowserClient,
  getSupabaseSessionSafely
} from "@/lib/supabase";

type AuthGateProps = {
  children: ReactNode;
};

type AuthState = "checking" | "authenticated" | "missing-config";

export function AuthGate({ children }: AuthGateProps) {
  const pathname = usePathname();
  const router = useRouter();
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [authState, setAuthState] = useState<AuthState>(
    supabase ? "checking" : "missing-config"
  );

  useEffect(() => {
    if (!supabase) {
      return;
    }

    const client = supabase;
    let ignore = false;

    async function checkSession() {
      const session = await getSupabaseSessionSafely(client);

      if (ignore) {
        return;
      }

      if (session) {
        setAuthState("authenticated");
        return;
      }

      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }

    const {
      data: { subscription }
    } = client.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setAuthState("authenticated");
        return;
      }

      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    });

    void checkSession();

    return () => {
      ignore = true;
      subscription.unsubscribe();
    };
  }, [pathname, router, supabase]);

  if (authState === "authenticated") {
    return children;
  }

  if (authState === "missing-config") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
        <section className="w-full max-w-md rounded-lg border border-white/10 bg-white p-8 text-slate-950 shadow-2xl">
          <p className="text-sm font-medium text-blue-700">Auth setup required</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-normal">
            Add Supabase frontend env values
          </h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Protected Averion pages need `NEXT_PUBLIC_SUPABASE_URL` and
            `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `apps/web/.env.local`.
          </p>
          <Link
            className="mt-6 inline-flex rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
            href="/login"
          >
            Go to sign in
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
      <section className="w-full max-w-sm rounded-lg border border-white/10 bg-white p-8 text-center text-slate-950 shadow-2xl">
        <p className="text-sm font-medium text-blue-700">Checking session</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal">
          Opening Averion
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Confirming your session before loading the workspace.
        </p>
      </section>
    </main>
  );
}
