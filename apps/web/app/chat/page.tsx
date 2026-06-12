import { AuthGate } from "@/components/auth-gate";
import { ChatWorkspace } from "@/components/chat-workspace";
import { DashboardShell } from "@/components/dashboard-shell";

export default function ChatPage() {
  return (
    <AuthGate>
      <DashboardShell immersive>
        <ChatWorkspace />
      </DashboardShell>
    </AuthGate>
  );
}
