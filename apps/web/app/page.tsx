import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { PageHeader } from "@/components/page-header";

const focusAreas = [
  {
    title: "Documents",
    description: "Upload internal PDFs, TXT files, and DOCX files for processing."
  },
  {
    title: "Retrieval",
    description: "Prepare chunks, embeddings, and source metadata for accurate answers."
  },
  {
    title: "Chat",
    description: "Ask questions and receive grounded answers with citations."
  }
];

export default function HomePage() {
  return (
    <AuthGate>
      <AppShell>
        <PageHeader
          eyebrow="MVP foundation"
          title="Enterprise knowledge copilot"
          description="A clean frontend skeleton for upload, chat, citations, and feedback workflows."
        />

        <section className="grid gap-4 md:grid-cols-3">
          {focusAreas.map((area) => (
            <article
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
              key={area.title}
            >
              <h2 className="text-base font-semibold text-slate-950">{area.title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{area.description}</p>
            </article>
          ))}
        </section>

        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-950">Current milestone</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            This screen is intentionally simple. The final visual design can be replaced later
            without changing the route structure or product flow.
          </p>
        </section>
      </AppShell>
    </AuthGate>
  );
}
