"use client";

import { useEffect, useMemo, useState } from "react";

import { getSupabaseBrowserClient } from "@/lib/supabase";

type AccountState = {
  email: string | null;
  provider: string | null;
  createdAt: string | null;
};

export function AccountSummary() {
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [account, setAccount] = useState<AccountState>({
    email: null,
    provider: null,
    createdAt: null
  });

  useEffect(() => {
    if (!supabase) {
      return;
    }

    const client = supabase;
    let ignore = false;

    async function loadAccount() {
      const { data } = await client.auth.getUser();

      if (ignore || !data.user) {
        return;
      }

      setAccount({
        email: data.user.email ?? null,
        provider: data.user.app_metadata.provider ?? null,
        createdAt: data.user.created_at ?? null
      });
    }

    void loadAccount();

    return () => {
      ignore = true;
    };
  }, [supabase]);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Account</h2>
      <dl className="mt-5 grid gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Email
          </dt>
          <dd className="mt-2 break-words text-sm font-medium text-slate-950">
            {account.email ?? "Loading..."}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Provider
          </dt>
          <dd className="mt-2 text-sm font-medium capitalize text-slate-950">
            {account.provider ?? "Email"}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Created
          </dt>
          <dd className="mt-2 text-sm font-medium text-slate-950">
            {account.createdAt
              ? new Date(account.createdAt).toLocaleDateString()
              : "Loading..."}
          </dd>
        </div>
      </dl>
      <p className="mt-5 text-sm leading-6 text-slate-600">
        Full profile editing comes in issue 42. For now, this page confirms
        that protected account access and session reads are working.
      </p>
    </section>
  );
}
