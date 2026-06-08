"use client";

import { useTranslations } from "next-intl";
import { AccountSummary } from "@/components/account-summary";
import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { PageHeader } from "@/components/page-header";

export default function AccountPage() {
  const t = useTranslations("account");
  
  return (
    <AuthGate>
      <AppShell>
        <PageHeader
          eyebrow={t("eyebrow")}
          title={t("title")}
          description={t("description")}
        />

        <AccountSummary />
      </AppShell>
    </AuthGate>
  );
}

// Made with Bob
