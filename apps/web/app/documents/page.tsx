import { AuthGate } from "@/components/auth-gate";
import { DashboardShell } from "@/components/dashboard-shell";
import { DocumentWorkspace } from "@/components/document-workspace";

export default function DocumentsPage() {
  return (
    <AuthGate>
      <DashboardShell>
        <DocumentWorkspace />
      </DashboardShell>
    </AuthGate>
  );
}
