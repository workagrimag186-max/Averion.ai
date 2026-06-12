import { AccountSummary } from "@/components/account-summary";
import { AuthGate } from "@/components/auth-gate";
import { DashboardShell } from "@/components/dashboard-shell";

export default function AccountPage() {
  return (
    <AuthGate>
      <DashboardShell>
        <AccountSummary />
      </DashboardShell>
    </AuthGate>
  );
}
