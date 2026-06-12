"use client";

import {
  AlertTriangle,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  CircleAlert,
  Database,
  FileText,
  FileType2,
  MessageSquare,
  RefreshCw,
  ThumbsUp,
  Upload,
  UploadCloud
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  type ConversationSummary,
  type DocumentListItem,
  listConversations,
  listDocuments
} from "@/lib/api";

type DashboardData = {
  documents: DocumentListItem[];
  conversations: ConversationSummary[];
};

const emptyDashboardData: DashboardData = {
  documents: [],
  conversations: []
};

const statusStyles: Record<string, string> = {
  ready: "bg-emerald-400/10 text-emerald-400",
  processing: "bg-blue-500/10 text-blue-400",
  pending: "bg-amber-400/10 text-amber-300",
  failed: "bg-red-500/10 text-red-400"
};

function formatCompactNumber(value: number) {
  return new Intl.NumberFormat("en", {
    notation: value >= 1000 ? "compact" : "standard",
    maximumFractionDigits: 1
  }).format(value);
}

function formatRelativeDate(dateValue: string) {
  const date = new Date(dateValue);
  const difference = Date.now() - date.getTime();
  const minutes = Math.floor(difference / 60_000);

  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min${minutes === 1 ? "" : "s"} ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;

  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} day${days === 1 ? "" : "s"} ago`;

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric"
  }).format(date);
}

function getWeeklyDocumentCounts(documents: DocumentListItem[]) {
  const now = new Date();
  const counts = [0, 0, 0, 0];

  for (const document of documents) {
    const ageInDays =
      (now.getTime() - new Date(document.created_at).getTime()) / 86_400_000;

    if (ageInDays >= 0 && ageInDays < 28) {
      const weekFromNow = Math.min(3, Math.floor(ageInDays / 7));
      counts[3 - weekFromNow] += 1;
    }
  }

  return counts;
}

function buildChartPaths(counts: number[]) {
  const width = 600;
  const height = 190;
  const maximum = Math.max(...counts, 1);
  const points = counts.map((count, index) => ({
    x: (index / (counts.length - 1)) * width,
    y: height - (count / maximum) * (height - 24)
  }));
  const line = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
  const area = `${line} L ${width} ${height} L 0 ${height} Z`;

  return { area, line };
}

export function DashboardOverview() {
  const [data, setData] = useState<DashboardData>(emptyDashboardData);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const [documentsResult, conversationsResult] = await Promise.allSettled([
      listDocuments(),
      listConversations()
    ]);

    const documents =
      documentsResult.status === "fulfilled" ? documentsResult.value : [];
    const conversations =
      conversationsResult.status === "fulfilled"
        ? conversationsResult.value.conversations
        : [];

    setData({ documents, conversations });

    if (
      documentsResult.status === "rejected" &&
      conversationsResult.status === "rejected"
    ) {
      setError("Dashboard data could not be loaded. Confirm the API is running.");
    } else if (
      documentsResult.status === "rejected" ||
      conversationsResult.status === "rejected"
    ) {
      setError("Some dashboard data is temporarily unavailable.");
    }

    setIsLoading(false);
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void loadDashboard();
    }, 0);

    return () => window.clearTimeout(timeout);
  }, [loadDashboard]);

  const dashboard = useMemo(() => {
    const totalDocuments = data.documents.length;
    const readyDocuments = data.documents.filter(
      (document) => document.status.toLowerCase() === "ready"
    ).length;
    const failedDocuments = data.documents.filter(
      (document) => document.status.toLowerCase() === "failed"
    ).length;
    const processingDocuments = totalDocuments - readyDocuments - failedDocuments;
    const totalChunks = data.documents.reduce(
      (sum, document) => sum + document.chunks_count,
      0
    );
    const readinessRate =
      totalDocuments === 0 ? 0 : Math.round((readyDocuments / totalDocuments) * 100);
    const recentDocuments = [...data.documents]
      .sort(
        (left, right) =>
          new Date(right.updated_at).getTime() -
          new Date(left.updated_at).getTime()
      )
      .slice(0, 5);
    const weeklyCounts = getWeeklyDocumentCounts(data.documents);

    return {
      totalDocuments,
      readyDocuments,
      failedDocuments,
      processingDocuments,
      totalChunks,
      readinessRate,
      recentDocuments,
      weeklyCounts,
      chartPaths: buildChartPaths(weeklyCounts)
    };
  }, [data.documents]);

  const activity = useMemo(() => {
    const documentActivity = data.documents.slice(0, 4).map((document) => ({
      id: `document-${document.document_id}`,
      timestamp: document.updated_at,
      kind: document.status.toLowerCase() === "failed" ? "error" : "document",
      title:
        document.status.toLowerCase() === "failed"
          ? `Processing needs attention for ${document.filename}.`
          : `${document.filename} is ${document.status.toLowerCase()}.`
    }));
    const conversationActivity = data.conversations.slice(0, 3).map((conversation) => ({
      id: `conversation-${conversation.id}`,
      timestamp: conversation.updated_at,
      kind: "conversation",
      title: `Conversation updated: ${conversation.title}`
    }));

    return [...documentActivity, ...conversationActivity]
      .sort(
        (left, right) =>
          new Date(right.timestamp).getTime() -
          new Date(left.timestamp).getTime()
      )
      .slice(0, 4);
  }, [data]);

  const metrics = [
    {
      label: "Total Documents",
      value: dashboard.totalDocuments,
      icon: FileText,
      detail: "Organization files",
      tone: "default"
    },
    {
      label: "Ready",
      value: dashboard.readyDocuments,
      icon: CheckCircle2,
      detail: `${dashboard.readinessRate}% success rate`,
      tone: "success"
    },
    {
      label: "Failed",
      value: dashboard.failedDocuments,
      icon: CircleAlert,
      detail: "Requires attention",
      tone: "danger"
    },
    {
      label: "Total Chunks",
      value: dashboard.totalChunks,
      icon: Database,
      detail: "Indexed segments",
      tone: "default"
    },
    {
      label: "Conversations",
      value: data.conversations.length,
      icon: MessageSquare,
      detail: "Saved chat sessions",
      tone: "default"
    }
  ] as const;

  return (
    <div className="mx-auto max-w-[1440px] space-y-6">
      <header className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div>
          <h1 className="font-serif text-3xl font-semibold tracking-normal text-zinc-100">
            System Overview
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-zinc-400">
            Monitor the state of your organizational knowledge base and AI
            performance.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            className="inline-flex h-10 items-center gap-2 rounded-md border border-zinc-700 px-4 text-xs font-semibold text-zinc-200 transition hover:border-blue-500/50 hover:bg-white/[0.04]"
            href="/documents"
          >
            <Upload aria-hidden="true" size={16} />
            Upload Document
          </Link>
          <Link
            className="inline-flex h-10 items-center gap-2 rounded-md bg-blue-500 px-4 text-xs font-semibold text-white shadow-lg shadow-blue-500/15 transition hover:bg-blue-600"
            href="/chat"
          >
            <MessageSquare aria-hidden="true" size={16} />
            Ask a Question
          </Link>
        </div>
      </header>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-md border border-amber-400/20 bg-amber-400/[0.06] px-4 py-3 text-sm text-amber-200">
          <span>{error}</span>
          <button
            className="inline-flex items-center gap-2 text-xs font-semibold text-amber-100 transition hover:text-white"
            onClick={() => void loadDashboard()}
            type="button"
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </div>
      )}

      <section
        aria-label="Knowledge metrics"
        className="grid grid-cols-2 gap-4 lg:grid-cols-5"
      >
        {metrics.map(({ detail, icon: Icon, label, tone, value }) => (
          <article
            className="flex min-h-28 flex-col justify-between rounded-lg border border-white/[0.08] bg-[#1a1a1a] p-4 transition hover:bg-[#202020]"
            key={label}
          >
            <div className="flex items-start justify-between gap-3">
              <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
                {label}
              </span>
              <Icon
                className={
                  tone === "success"
                    ? "text-emerald-400"
                    : tone === "danger"
                      ? "text-red-400"
                      : "text-zinc-500"
                }
                size={15}
              />
            </div>
            <div>
              <strong
                className={`block font-serif text-2xl font-semibold ${
                  tone === "danger" ? "text-red-400" : "text-zinc-100"
                }`}
              >
                {isLoading ? "—" : formatCompactNumber(value)}
              </strong>
              <span
                className={`mt-1 flex items-center gap-1 text-xs ${
                  tone === "success"
                    ? "text-emerald-400"
                    : "text-zinc-400"
                }`}
              >
                {tone === "success" && <ArrowUpRight size={13} />}
                {detail}
              </span>
            </div>
          </article>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <article className="min-h-[340px] rounded-lg border border-white/[0.08] bg-[#1a1a1a] p-6 lg:col-span-2">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-serif text-xl font-semibold text-zinc-100">
              Recent Knowledge Growth
            </h2>
            <span className="rounded-md border border-white/10 bg-zinc-900 px-3 py-1.5 font-mono text-[10px] font-semibold uppercase tracking-[0.08em] text-zinc-400">
              Last 30 Days
            </span>
          </div>

          <div className="mt-6 h-[220px]">
            <div className="relative h-[190px] border-b border-l border-white/10">
              <div className="absolute inset-0 flex flex-col justify-between">
                {[0, 1, 2, 3].map((line) => (
                  <span className="h-px w-full bg-white/[0.05]" key={line} />
                ))}
              </div>
              <svg
                aria-label="Documents added across the last four weeks"
                className="absolute inset-0 size-full overflow-visible"
                preserveAspectRatio="none"
                role="img"
                viewBox="0 0 600 190"
              >
                <defs>
                  <linearGradient id="dashboard-chart-fill" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.24" />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d={dashboard.chartPaths.area} fill="url(#dashboard-chart-fill)" />
                <path
                  d={dashboard.chartPaths.line}
                  fill="none"
                  stroke="#3b82f6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            </div>
            <div className="mt-2 flex justify-between font-mono text-[10px] font-semibold uppercase tracking-[0.06em] text-zinc-500">
              <span>Week 1</span>
              <span>Week 2</span>
              <span>Week 3</span>
              <span>Week 4</span>
            </div>
          </div>
        </article>

        <article className="flex min-h-[340px] flex-col rounded-lg border border-white/[0.08] bg-[#1a1a1a] p-6">
          <h2 className="font-serif text-xl font-semibold text-zinc-100">
            Knowledge Health &amp; Feedback
          </h2>
          <div className="mt-7 flex items-end gap-2">
            <strong className="font-serif text-4xl font-semibold leading-none text-emerald-400">
              {dashboard.readinessRate}%
            </strong>
            <span className="pb-1 text-xs text-zinc-400">Readiness score</span>
          </div>

          <div className="mt-8 flex-1 space-y-5">
            {[
              {
                label: "Ready Documents",
                value: dashboard.readyDocuments,
                width: dashboard.readinessRate,
                color: "bg-emerald-400"
              },
              {
                label: "Processing",
                value: dashboard.processingDocuments,
                width:
                  dashboard.totalDocuments === 0
                    ? 0
                    : Math.round(
                        (dashboard.processingDocuments /
                          dashboard.totalDocuments) *
                          100
                      ),
                color: "bg-amber-300"
              },
              {
                label: "Needs Attention",
                value: dashboard.failedDocuments,
                width:
                  dashboard.totalDocuments === 0
                    ? 0
                    : Math.round(
                        (dashboard.failedDocuments / dashboard.totalDocuments) * 100
                      ),
                color: "bg-red-500"
              }
            ].map((item) => (
              <div key={item.label}>
                <div className="mb-1.5 flex justify-between font-mono text-[10px] font-semibold uppercase tracking-[0.06em] text-zinc-300">
                  <span>{item.label}</span>
                  <span className="text-zinc-400">{item.value}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                  <div
                    className={`h-full rounded-full ${item.color}`}
                    style={{ width: `${Math.max(item.width, item.value > 0 ? 3 : 0)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <Link
            className="mt-5 inline-flex h-9 items-center justify-center rounded-md border border-white/10 text-xs font-semibold text-zinc-200 transition hover:border-blue-500/40 hover:bg-white/[0.04]"
            href="/documents"
          >
            View Detailed Report
          </Link>
        </article>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <article className="overflow-hidden rounded-lg border border-white/[0.08] bg-[#1a1a1a]">
          <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-4">
            <h2 className="font-serif text-lg font-semibold text-zinc-100">
              Recent Documents
            </h2>
            <Link
              className="font-mono text-[10px] font-semibold uppercase tracking-[0.08em] text-blue-400 transition hover:text-blue-300"
              href="/documents"
            >
              View All
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[540px] text-left">
              <thead>
                <tr className="font-mono text-[10px] uppercase tracking-[0.08em] text-slate-400">
                  <th className="px-4 py-3 font-semibold">Filename</th>
                  <th className="px-4 py-3 font-semibold">Format</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 text-right font-semibold">Chunks</th>
                </tr>
              </thead>
              <tbody className="text-xs">
                {dashboard.recentDocuments.map((document) => (
                  <tr
                    className="border-t border-white/[0.05] transition hover:bg-zinc-900/70"
                    key={document.document_id}
                  >
                    <td className="max-w-72 px-4 py-4 text-zinc-100">
                      <span className="flex items-center gap-2">
                        <FileType2 className="shrink-0 text-zinc-500" size={15} />
                        <span className="truncate">{document.filename}</span>
                      </span>
                    </td>
                    <td className="px-4 py-4 uppercase text-zinc-400">
                      {document.file_type}
                    </td>
                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex rounded px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-[0.06em] ${
                          statusStyles[document.status.toLowerCase()] ??
                          "bg-zinc-700 text-zinc-300"
                        }`}
                      >
                        {document.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right text-zinc-400">
                      {document.chunks_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!isLoading && dashboard.recentDocuments.length === 0 && (
              <div className="flex min-h-52 flex-col items-center justify-center px-6 text-center">
                <UploadCloud className="text-zinc-600" size={28} />
                <p className="mt-3 text-sm font-medium text-zinc-300">
                  No documents uploaded yet
                </p>
                <Link
                  className="mt-3 text-xs font-semibold text-blue-400 hover:text-blue-300"
                  href="/documents"
                >
                  Upload your first document
                </Link>
              </div>
            )}
          </div>
        </article>

        <article className="rounded-lg border border-white/[0.08] bg-[#1a1a1a] p-4">
          <div className="border-b border-white/[0.06] pb-4">
            <h2 className="font-serif text-lg font-semibold text-zinc-100">
              Recent Activity
            </h2>
          </div>

          <div className="mt-4 space-y-4">
            {activity.map((item) => {
              const Icon =
                item.kind === "error"
                  ? AlertTriangle
                  : item.kind === "conversation"
                    ? Bot
                    : item.title.includes("ready")
                      ? ThumbsUp
                      : UploadCloud;
              const iconTone =
                item.kind === "error"
                  ? "border-red-500/30 bg-red-500/10 text-red-400"
                  : "border-blue-500/30 bg-blue-500/10 text-blue-400";

              return (
                <div className="flex gap-3" key={item.id}>
                  <span
                    className={`flex size-8 shrink-0 items-center justify-center rounded-full border ${iconTone}`}
                  >
                    <Icon aria-hidden="true" size={15} />
                  </span>
                  <div className="min-w-0 pb-2">
                    <p className="text-xs leading-5 text-zinc-200">{item.title}</p>
                    <p className="mt-1 font-mono text-[10px] font-semibold uppercase tracking-[0.06em] text-zinc-500">
                      {formatRelativeDate(item.timestamp)} · Organization
                    </p>
                  </div>
                </div>
              );
            })}

            {!isLoading && activity.length === 0 && (
              <div className="flex min-h-52 flex-col items-center justify-center text-center">
                <RefreshCw className="text-zinc-600" size={27} />
                <p className="mt-3 text-sm font-medium text-zinc-300">
                  Activity will appear here
                </p>
                <p className="mt-1 max-w-xs text-xs leading-5 text-zinc-500">
                  Upload a document or start a conversation to populate the
                  organization feed.
                </p>
              </div>
            )}
          </div>
        </article>
      </section>
    </div>
  );
}
