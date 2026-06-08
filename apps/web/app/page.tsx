"use client";

import { useTranslations } from "next-intl";
import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { PageHeader } from "@/components/page-header";

export default function HomePage() {
  const t = useTranslations("home");
  
  const focusAreas = [
    {
      title: t("focusAreas.documents.title"),
      description: t("focusAreas.documents.description")
    },
    {
      title: t("focusAreas.retrieval.title"),
      description: t("focusAreas.retrieval.description")
    },
    {
      title: t("focusAreas.chat.title"),
      description: t("focusAreas.chat.description")
    }
  ];

  return (
    <AuthGate>
      <AppShell>
        <PageHeader
          eyebrow={t("eyebrow")}
          title={t("title")}
          description={t("description")}
        />

        <section className="grid gap-4 md:grid-cols-3">
          {focusAreas.map((area) => (
            <article
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
              key={area.title}
            >
              <h2 className="text-base font-semibold text-slate-950">{area.title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{area.description}</p>
            </article>
          ))}
        </section>

        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-950">{t("milestone.title")}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            {t("milestone.description")}
          </p>
        </section>
      </AppShell>
    </AuthGate>
  );
}

// Made with Bob
