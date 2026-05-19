import { AppShell } from "@/components/app-shell";
import { ChatWorkspace } from "@/components/chat-workspace";
import { PageHeader } from "@/components/page-header";

export default function ChatPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Chat"
        title="Ask company knowledge"
        description="Ask questions against uploaded documents and review source placeholders returned by the chat API."
      />

      <ChatWorkspace />
    </AppShell>
  );
}
