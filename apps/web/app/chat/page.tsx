import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";

export default function ChatPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Chat"
        title="Ask company knowledge"
        description="This page will become the RAG chat interface with citations and feedback."
      />

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 p-5">
          <p className="text-sm font-medium text-slate-950">Chat UI coming in Issue #23</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            For now, this placeholder confirms the route and layout are ready.
          </p>
        </div>
        <div className="p-5">
          <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
            Example prompt: What does the employee handbook say about leave policy?
          </div>
        </div>
      </section>
    </AppShell>
  );
}
