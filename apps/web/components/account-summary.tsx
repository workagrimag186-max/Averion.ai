"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AccountProfile,
  getAccountProfile,
  updateAccountProfile
} from "@/lib/api";
import { getSupabaseBrowserClient } from "@/lib/supabase";

type FormStatus = {
  kind: "idle" | "success" | "error";
  message: string;
};

function displayValue(value: string | null | undefined): string {
  return value?.trim() || "Not set";
}

function formatRole(role: string | null): string {
  if (!role) {
    return "Not assigned";
  }

  return role.charAt(0).toUpperCase() + role.slice(1);
}

export function AccountSummary() {
  const router = useRouter();
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [profile, setProfile] = useState<AccountProfile | null>(null);
  const [name, setName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [status, setStatus] = useState<FormStatus>({
    kind: "idle",
    message: ""
  });

  useEffect(() => {
    let ignore = false;

    async function loadProfile() {
      setIsLoading(true);
      setStatus({ kind: "idle", message: "" });

      try {
        const nextProfile = await getAccountProfile();

        if (ignore) {
          return;
        }

        setProfile(nextProfile);
        setName(nextProfile.name ?? "");
        setJobTitle(nextProfile.job_title ?? "");
      } catch (error) {
        if (ignore) {
          return;
        }

        setStatus({
          kind: "error",
          message:
            error instanceof Error
              ? error.message
              : "Could not load account profile."
        });
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      ignore = true;
    };
  }, []);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setStatus({ kind: "idle", message: "" });

    try {
      const updatedProfile = await updateAccountProfile({
        name: name.trim() || null,
        job_title: jobTitle.trim() || null
      });

      setProfile(updatedProfile);
      setName(updatedProfile.name ?? "");
      setJobTitle(updatedProfile.job_title ?? "");
      setStatus({
        kind: "success",
        message: "Profile updated."
      });
    } catch (error) {
      setStatus({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not update account profile."
      });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLogout() {
    if (!supabase) {
      router.replace("/login");
      return;
    }

    setIsSigningOut(true);
    await supabase.auth.signOut();
    router.replace("/login");
  }

  if (isLoading) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-blue-700">Loading profile</p>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="h-24 rounded-lg bg-slate-100" />
          <div className="h-24 rounded-lg bg-slate-100" />
          <div className="h-44 rounded-lg bg-slate-100 md:col-span-2" />
        </div>
      </section>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-700">Account details</p>
            <h2 className="mt-1 text-xl font-semibold tracking-normal text-slate-950">
              Profile
            </h2>
          </div>
          <button
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSigningOut}
            onClick={handleLogout}
            type="button"
          >
            {isSigningOut ? "Signing out..." : "Logout"}
          </button>
        </div>

        {status.message && (
          <div
            className={`mt-5 rounded-md border px-4 py-3 text-sm ${
              status.kind === "success"
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-red-200 bg-red-50 text-red-800"
            }`}
          >
            {status.message}
          </div>
        )}

        <form className="mt-6 grid gap-5" onSubmit={handleSave}>
          <label className="grid gap-2">
            <span className="text-sm font-semibold text-slate-700">
              Display name
            </span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              maxLength={120}
              onChange={(event) => setName(event.target.value)}
              placeholder="Add your name"
              type="text"
              value={name}
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-semibold text-slate-700">
              Job title
            </span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              maxLength={120}
              onChange={(event) => setJobTitle(event.target.value)}
              placeholder="Knowledge manager, founder, engineer..."
              type="text"
              value={jobTitle}
            />
          </label>

          <div className="flex flex-wrap items-center gap-3">
            <button
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSaving}
              type="submit"
            >
              {isSaving ? "Saving..." : "Save profile"}
            </button>
            <p className="text-sm text-slate-500">
              Email stays read-only for the MVP.
            </p>
          </div>
        </form>
      </section>

      <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Workspace access</h2>
        <dl className="mt-5 grid gap-4">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Email
            </dt>
            <dd className="mt-2 break-words text-sm font-medium text-slate-950">
              {displayValue(profile?.email)}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Organization
            </dt>
            <dd className="mt-2 text-sm font-medium text-slate-950">
              {displayValue(profile?.organization_name)}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Role
            </dt>
            <dd className="mt-2 text-sm font-medium text-slate-950">
              {formatRole(profile?.role ?? null)}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              User ID
            </dt>
            <dd className="mt-2 break-all font-mono text-xs text-slate-600">
              {displayValue(profile?.user_id)}
            </dd>
          </div>
        </dl>
      </aside>
    </div>
  );
}
