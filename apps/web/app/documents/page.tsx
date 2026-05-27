import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { DocumentWorkspace } from "@/components/document-workspace";
import { PageHeader } from "@/components/page-header";

export default function DocumentsPage() {
  return (
    <AuthGate>
      <AppShell>
        <PageHeader
          eyebrow="Documents"
          title="Document workspace"
          description="Upload PDF, TXT, and DOCX files so they can enter the knowledge pipeline."
        />

        <DocumentWorkspace />
      </AppShell>
    </AuthGate>
  );
}
