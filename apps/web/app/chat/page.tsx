"use client";

import { useTranslations } from "next-intl";
import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { ChatWorkspace } from "@/components/chat-workspace";
import { PageHeader } from "@/components/page-header";

export default function ChatPage() {
  const t = useTranslations("chat");
  
  return (
    <AuthGate>
      <AppShell>
        <PageHeader
          eyebrow={t("eyebrow")}
          title={t("title")}
          description={t("description")}
        />

        <ChatWorkspace />
      </AppShell>
    </AuthGate>
  );
}

// Made with Bob
