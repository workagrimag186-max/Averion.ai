import { AppShell } from "@/components/app-shell";
import { DocumentUpload } from "@/components/document-upload";
import { PageHeader } from "@/components/page-header";

export default function DocumentsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Documents"
        title="Document workspace"
        description="Upload PDF, TXT, and DOCX files so they can enter the knowledge pipeline."
      />

      <DocumentUpload />
    </AppShell>
  );
}
