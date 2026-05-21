"use client";

import { useState } from "react";

import { ChatCitation } from "@/lib/api";

type CitationSourcePanelProps = {
  citations: ChatCitation[];
  errorMessage?: string | null;
  isLoading?: boolean;
};

function getCitationTitle(citation: ChatCitation) {
  return citation.filename || citation.document_id || "Unknown source";
}

function getCitationLocation(citation: ChatCitation) {
  const parts = [`Chunk ${citation.chunk_index}`];

  if (citation.page_number) {
    parts.unshift(`Page ${citation.page_number}`);
  }

  return parts.join(" · ");
}

export function CitationSourcePanel({
  citations,
  errorMessage,
  isLoading = false
}: CitationSourcePanelProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  if (isLoading) {
    return (
      <div className="space-y-2" aria-live="polite">
        {[0, 1].map((item) => (
          <div className="rounded-md border border-slate-200 bg-white p-3" key={item}>
            <div className="h-4 w-2/3 rounded bg-slate-100" />
            <div className="mt-2 h-3 w-1/3 rounded bg-slate-100" />
          </div>
        ))}
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 p-3" role="alert">
        <p className="text-sm font-medium text-red-800">Sources could not be loaded</p>
        <p className="mt-1 text-sm leading-5 text-red-700">{errorMessage}</p>
      </div>
    );
  }

  if (!citations.length) {
    return (
      <div className="rounded-md border border-slate-200 bg-white p-3">
        <p className="text-sm font-medium text-slate-700">No sources returned</p>
        <p className="mt-1 text-sm leading-5 text-slate-500">
          The answer did not include source citations. Try asking a more specific question
          about an uploaded document.
        </p>
      </div>
    );
  }

  function toggleCitation(citationId: string) {
    setExpandedIds((current) => {
      const next = new Set(current);

      if (next.has(citationId)) {
        next.delete(citationId);
      } else {
        next.add(citationId);
      }

      return next;
    });
  }

  return (
    <div className="space-y-2">
      {citations.map((citation, index) => {
        const sourceKey = citation.chunk_id || `${citation.document_id}:${citation.chunk_index}:${index}`;
        const isExpanded = expandedIds.has(sourceKey);

        return (
          <div className="rounded-md border border-slate-200 bg-white" key={sourceKey}>
            <button
              aria-expanded={isExpanded}
              className="flex w-full items-start justify-between gap-3 px-3 py-3 text-left transition hover:bg-slate-50"
              onClick={() => toggleCitation(sourceKey)}
              type="button"
            >
              <span>
                <span className="block text-sm font-semibold text-slate-950">
                  {getCitationTitle(citation)}
                </span>
                <span className="mt-1 block text-xs text-slate-500">
                  {getCitationLocation(citation)}
                </span>
              </span>
              <span className="shrink-0 rounded-full bg-slate-100 px-2 py-1 font-mono text-xs text-slate-600">
                {citation.chunk_id || "missing-chunk-id"}
              </span>
            </button>

            {isExpanded ? (
              <div className="border-t border-slate-100 px-3 py-3">
                <dl className="grid gap-2 text-xs text-slate-500 sm:grid-cols-2">
                  <div>
                    <dt className="font-medium text-slate-700">Document ID</dt>
                    <dd className="mt-1 break-all font-mono">{citation.document_id || "Unknown"}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-slate-700">Score</dt>
                    <dd className="mt-1">
                      {typeof citation.score === "number" ? citation.score.toFixed(4) : "Not available"}
                    </dd>
                  </div>
                </dl>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                  {citation.snippet || "No source snippet was returned."}
                </p>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
