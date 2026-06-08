"use client";

import { useTranslations } from "next-intl";
import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { DocumentWorkspace } from "@/components/document-workspace";
import { PageHeader } from "@/components/page-header";

export default function DocumentsPage() {
  const t = useTranslations("documents");
  
  return (
    <AuthGate>
      <AppShell>
        <PageHeader
          eyebrow={t("eyebrow")}
          title={t("title")}
          description={t("description")}
        />

        <DocumentWorkspace />
      </AppShell>
    </AuthGate>
  );
}

// Made with Bob
