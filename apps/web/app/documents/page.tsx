import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";

export default function DocumentsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Documents"
        title="Document workspace"
        description="This page will handle file uploads, processing status, and document lists."
      />

      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-medium text-slate-950">Upload UI coming in Issue #9</p>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">
          The upload flow will support PDF, TXT, and DOCX files once the backend upload
          endpoint is ready.
        </p>
      </section>
    </AppShell>
  );
}
