import Link from "next/link";
import type { ReactNode } from "react";
import { Navigation } from "@/components/navigation";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <Link className="flex items-center gap-3" href="/">
            <span className="flex size-9 items-center justify-center rounded-lg bg-blue-600 text-sm font-semibold text-white">
              A
            </span>
            <span>
              <span className="block text-sm font-semibold text-slate-950">Averion.ai</span>
              <span className="block text-xs text-slate-500">Knowledge Copilot</span>
            </span>
          </Link>
          <Navigation />
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
