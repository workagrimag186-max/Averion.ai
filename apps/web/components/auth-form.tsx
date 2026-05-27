"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { validateEmail, validatePassword } from "@/lib/auth-validation";
import { getAuthRedirectUrl, getSupabaseBrowserClient } from "@/lib/supabase";

type AuthMode = "login" | "signup";

type AuthFormProps = {
  mode: AuthMode;
};

type FormStatus = {
  kind: "idle" | "success" | "error";
  message: string;
};

const copy = {
  login: {
    eyebrow: "Welcome back",
    title: "Sign in to Averion",
    description: "Use your work email to continue to your knowledge workspace.",
    button: "Sign in",
    pending: "Signing in...",
    alternatePrompt: "New to Averion?",
    alternateLabel: "Create an account",
    alternateHref: "/signup"
  },
  signup: {
    eyebrow: "Create account",
    title: "Start your Averion workspace",
    description: "Create your account with a valid email address. Gmail-only rules can be enabled from env config later.",
    button: "Create account",
    pending: "Creating account...",
    alternatePrompt: "Already have an account?",
    alternateLabel: "Sign in",
    alternateHref: "/login"
  }
} satisfies Record<AuthMode, Record<string, string>>;

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isOAuthSubmitting, setIsOAuthSubmitting] = useState(false);
  const [status, setStatus] = useState<FormStatus>({
    kind: "idle",
    message: ""
  });

  const formCopy = copy[mode];
  const isSignup = mode === "signup";

  useEffect(() => {
    let ignore = false;

    async function redirectAuthenticatedUser() {
      if (!supabase) {
        return;
      }

      const { data } = await supabase.auth.getSession();

      if (!ignore && data.session) {
        router.replace("/");
      }
    }

    void redirectAuthenticatedUser();

    return () => {
      ignore = true;
    };
  }, [router, supabase]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const emailError = validateEmail(email);
    const passwordError = validatePassword(password);

    if (emailError || passwordError) {
      setStatus({
        kind: "error",
        message: emailError ?? passwordError ?? "Check your login details."
      });
      return;
    }

    if (isSignup && password !== confirmPassword) {
      setStatus({
        kind: "error",
        message: "Passwords must match."
      });
      return;
    }

    if (!supabase) {
      setStatus({
        kind: "error",
        message: "Supabase auth is not configured yet. Add the frontend Supabase env values first."
      });
      return;
    }

    setIsSubmitting(true);
    setStatus({ kind: "idle", message: "" });

    try {
      if (isSignup) {
        const { error } = await supabase.auth.signUp({
          email: email.trim().toLowerCase(),
          password,
          options: {
            emailRedirectTo: getAuthRedirectUrl(),
            data: {
              full_name: name.trim() || null
            }
          }
        });

        if (error) {
          throw error;
        }

        setStatus({
          kind: "success",
          message: "Account created. Check your email to verify your account before signing in."
        });
        setPassword("");
        setConfirmPassword("");
        return;
      }

      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password
      });

      if (error) {
        throw error;
      }

      setStatus({
        kind: "success",
        message: "Signed in. Opening your workspace..."
      });
      router.replace("/");
    } catch (error) {
      setStatus({
        kind: "error",
        message: error instanceof Error ? error.message : "Authentication failed. Try again."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGoogleSignIn() {
    if (!supabase) {
      setStatus({
        kind: "error",
        message: "Supabase auth is not configured yet. Add the frontend Supabase env values first."
      });
      return;
    }

    setIsOAuthSubmitting(true);
    setStatus({ kind: "idle", message: "" });

    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: getAuthRedirectUrl(),
        queryParams: {
          access_type: "offline",
          prompt: "consent"
        }
      }
    });

    if (error) {
      setIsOAuthSubmitting(false);
      setStatus({
        kind: "error",
        message: error.message
      });
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center justify-center">
        <div className="grid w-full overflow-hidden rounded-lg border border-white/10 bg-white/[0.03] shadow-2xl shadow-blue-950/30 lg:grid-cols-[0.95fr_1.05fr]">
          <section className="hidden border-r border-white/10 bg-slate-900/80 p-10 lg:block">
            <Link className="flex items-center gap-3" href="/">
              <span className="flex size-10 items-center justify-center rounded-lg bg-blue-500 text-sm font-semibold text-white">
                A
              </span>
              <span>
                <span className="block text-base font-semibold">Averion.ai</span>
                <span className="block text-xs uppercase tracking-[0.18em] text-slate-400">
                  Knowledge Copilot
                </span>
              </span>
            </Link>

            <div className="mt-20 max-w-md">
              <p className="text-sm font-medium text-cyan-300">{formCopy.eyebrow}</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-normal text-white">
                Secure access for your company knowledge.
              </h1>
              <p className="mt-5 text-sm leading-6 text-slate-300">
                Sign in before uploading documents, asking questions, or saving
                feedback. Supabase Auth handles sessions while Averion keeps your
                product data scoped to your organization.
              </p>
            </div>
          </section>

          <section className="bg-white p-6 text-slate-950 sm:p-10">
            <div className="mx-auto max-w-md">
              <div className="lg:hidden">
                <Link className="flex items-center gap-3" href="/">
                  <span className="flex size-10 items-center justify-center rounded-lg bg-blue-600 text-sm font-semibold text-white">
                    A
                  </span>
                  <span>
                    <span className="block text-base font-semibold">Averion.ai</span>
                    <span className="block text-xs text-slate-500">Knowledge Copilot</span>
                  </span>
                </Link>
              </div>

              <div className="mt-10 lg:mt-0">
                <p className="text-sm font-medium text-blue-700">{formCopy.eyebrow}</p>
                <h2 className="mt-2 text-3xl font-semibold tracking-normal">
                  {formCopy.title}
                </h2>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  {formCopy.description}
                </p>
              </div>

              <button
                className="mt-8 flex w-full items-center justify-center gap-3 rounded-md border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isSubmitting || isOAuthSubmitting}
                onClick={handleGoogleSignIn}
                type="button"
              >
                <span
                  aria-hidden="true"
                  className="flex size-5 items-center justify-center rounded-full border border-slate-200 text-xs font-bold text-blue-600"
                >
                  G
                </span>
                {isOAuthSubmitting ? "Opening Google..." : "Continue with Google"}
              </button>

              <div className="mt-6 flex items-center gap-3">
                <span className="h-px flex-1 bg-slate-200" />
                <span className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
                  or
                </span>
                <span className="h-px flex-1 bg-slate-200" />
              </div>

              <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
                {isSignup && (
                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">Full name</span>
                    <input
                      autoComplete="name"
                      className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-3 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Shubham Mitra"
                      type="text"
                      value={name}
                    />
                  </label>
                )}

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Email</span>
                  <input
                    autoComplete="email"
                    className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-3 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@company.com"
                    required
                    type="email"
                    value={email}
                  />
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Password</span>
                  <input
                    autoComplete={isSignup ? "new-password" : "current-password"}
                    className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-3 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="At least 8 characters"
                    required
                    type="password"
                    value={password}
                  />
                </label>

                {isSignup && (
                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Confirm password
                    </span>
                    <input
                      autoComplete="new-password"
                      className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-3 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                      onChange={(event) => setConfirmPassword(event.target.value)}
                      placeholder="Repeat your password"
                      required
                      type="password"
                      value={confirmPassword}
                    />
                  </label>
                )}

                {status.kind !== "idle" && (
                  <div
                    className={
                      status.kind === "success"
                        ? "rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
                        : "rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                    }
                    role="status"
                  >
                    {status.message}
                  </div>
                )}

                <button
                  className="w-full rounded-md bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                  disabled={isSubmitting || isOAuthSubmitting}
                  type="submit"
                >
                  {isSubmitting ? formCopy.pending : formCopy.button}
                </button>
              </form>

              <p className="mt-6 text-center text-sm text-slate-600">
                {formCopy.alternatePrompt}{" "}
                <Link className="font-semibold text-blue-700 hover:text-blue-800" href={formCopy.alternateHref}>
                  {formCopy.alternateLabel}
                </Link>
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
