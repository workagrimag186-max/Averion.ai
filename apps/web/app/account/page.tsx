import { AccountSummary } from "@/components/account-summary";
import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { PageHeader } from "@/components/page-header";

export default function AccountPage() {
  return (
    <AuthGate>
      <AppShell>
        <PageHeader
          eyebrow="Account"
          title="Profile and session"
          description="Review the current signed-in account and manage the active session."
        />

        <AccountSummary />
      </AppShell>
    </AuthGate>
  );
}
