"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  buildAllowedDomainError,
  getAllowedEmailDomains,
  isEmailDomainAllowed
} from "@/lib/auth-validation";
import {
  getSupabaseBrowserClient,
  getSupabaseSessionSafely
} from "@/lib/supabase";

export default function AuthCallbackPage() {
  const router = useRouter();
  const [message, setMessage] = useState("Completing your sign in...");

  useEffect(() => {
    let ignore = false;

    async function handleCallback() {
      const supabase = getSupabaseBrowserClient();

      if (!supabase) {
        setMessage("Supabase auth is not configured yet.");
        return;
      }

      const session = await getSupabaseSessionSafely(supabase);

      if (ignore) {
        return;
      }

      if (session) {
        const userEmail = session.user.email ?? "";
        const allowedDomains = getAllowedEmailDomains();

        if (!isEmailDomainAllowed(userEmail, allowedDomains)) {
          await supabase.auth.signOut();

          if (!ignore) {
            setMessage(buildAllowedDomainError(allowedDomains));
          }

          return;
        }

        router.replace("/");
        return;
      }

      setMessage("Email confirmed. You can sign in now.");
    }

    void handleCallback();

    return () => {
      ignore = true;
    };
  }, [router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
      <section className="w-full max-w-md rounded-lg border border-white/10 bg-white p-8 text-slate-950 shadow-2xl">
        <p className="text-sm font-medium text-blue-700">Auth callback</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal">Almost there</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{message}</p>
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
