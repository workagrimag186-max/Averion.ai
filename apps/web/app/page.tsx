import { AuthGate } from "@/components/auth-gate";
import { DashboardOverview } from "@/components/dashboard-overview";
import { DashboardShell } from "@/components/dashboard-shell";

export default function HomePage() {
  return (
    <AuthGate>
      <DashboardShell>
        <DashboardOverview />
      </DashboardShell>
    </AuthGate>
  );
}
