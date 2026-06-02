"use client";

import { useEffect, useState } from "react";

import {
  deleteDocument,
  DocumentListItem,
  getAccountProfile,
  listDocuments
} from "@/lib/api";

type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

type DocumentListProps = {
  refreshKey: number;
};

const STATUS_COPY: Record<DocumentStatus, { label: string; detail: string; className: string }> = {
  uploaded: {
    label: "Uploaded",
    detail: "Waiting for processing",
    className: "bg-slate-50 text-slate-700 ring-slate-200"
  },
  processing: {
    label: "Processing",
    detail: "Extracting and chunking",
    className: "bg-amber-50 text-amber-800 ring-amber-200"
  },
  ready: {
    label: "Ready",
    detail: "Available for chat",
    className: "bg-green-50 text-green-700 ring-green-200"
  },
  failed: {
    label: "Failed",
    detail: "Needs attention",
    className: "bg-red-50 text-red-700 ring-red-200"
  }
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function getStatusCopy(status: string) {
  return STATUS_COPY[status as DocumentStatus] ?? {
    label: status || "Unknown",
    detail: "Status unavailable",
    className: "bg-slate-50 text-slate-700 ring-slate-200"
  };
}

function formatChunkCount(count: number) {
  return `${count} ${count === 1 ? "chunk" : "chunks"}`;
}

function countByStatus(documents: DocumentListItem[], status: DocumentStatus) {
  return documents.filter((document) => document.status === status).length;
}

export function DocumentList({ refreshKey }: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewerRole, setViewerRole] = useState<string | null>(null);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  async function loadDocuments({ showLoader = true } = {}) {
    if (showLoader) {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }

    setErrorMessage(null);

    try {
      const result = await listDocuments();
      setDocuments(result);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not load documents.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }

  async function handleDeleteDocument(document: DocumentListItem) {
    const confirmed = window.confirm(
      `Delete "${document.filename}"? This removes its chunks and embeddings, so chat will no longer use this file.`
    );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(document.document_id);
    setActionMessage(null);
    setErrorMessage(null);

    try {
      await deleteDocument(document.document_id);
      setDocuments((currentDocuments) =>
        currentDocuments.filter(
          (currentDocument) => currentDocument.document_id !== document.document_id
        )
      );
      setActionMessage(`Deleted ${document.filename}. Chat will no longer retrieve it.`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not delete document.");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  useEffect(() => {
    let isCurrent = true;

    async function loadViewerRole() {
      try {
        const profile = await getAccountProfile();

        if (isCurrent) {
          setViewerRole(profile.role);
        }
      } catch {
        if (isCurrent) {
          setViewerRole(null);
        }
      }
    }

    loadViewerRole();

    return () => {
      isCurrent = false;
    };
  }, []);

  useEffect(() => {
    let isCurrent = true;

    async function loadCurrentDocuments() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const result = await listDocuments();

        if (isCurrent) {
          setDocuments(result);
        }
      } catch (error) {
        if (isCurrent) {
          setErrorMessage(error instanceof Error ? error.message : "Could not load documents.");
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    loadCurrentDocuments();

    return () => {
      isCurrent = false;
    };
  }, [refreshKey]);

  useEffect(() => {
    const shouldPoll = documents.some((document) =>
      document.status === "uploaded" || document.status === "processing"
    );

    if (!shouldPoll || isLoading) {
      return;
    }

    const intervalId = window.setInterval(() => {
      loadDocuments({ showLoader: false });
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [documents, isLoading]);

  const readyCount = countByStatus(documents, "ready");
  const processingCount =
    countByStatus(documents, "uploaded") + countByStatus(documents, "processing");
  const failedCount = countByStatus(documents, "failed");

  return (
    <section className="mt-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Uploaded documents</h2>
          <p className="mt-1 text-sm text-slate-500">
            Supabase-backed files and their processing state.
          </p>
        </div>
        <button
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isLoading || isRefreshing}
          onClick={() => loadDocuments({ showLoader: false })}
          type="button"
        >
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {actionMessage ? (
        <div className="mb-4 rounded-md border border-green-200 bg-green-50 p-3 text-sm font-medium text-green-800">
          {actionMessage}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {!isLoading && !errorMessage ? (
          <div className="grid gap-px border-b border-slate-200 bg-slate-200 sm:grid-cols-4">
            <div className="bg-white p-4">
              <p className="text-xs font-medium uppercase tracking-normal text-slate-500">Total</p>
              <p className="mt-1 text-2xl font-semibold text-slate-950">{documents.length}</p>
            </div>
            <div className="bg-white p-4">
              <p className="text-xs font-medium uppercase tracking-normal text-slate-500">Ready</p>
              <p className="mt-1 text-2xl font-semibold text-green-700">{readyCount}</p>
            </div>
            <div className="bg-white p-4">
              <p className="text-xs font-medium uppercase tracking-normal text-slate-500">
                In progress
              </p>
              <p className="mt-1 text-2xl font-semibold text-amber-700">{processingCount}</p>
            </div>
            <div className="bg-white p-4">
              <p className="text-xs font-medium uppercase tracking-normal text-slate-500">Failed</p>
              <p className="mt-1 text-2xl font-semibold text-red-700">{failedCount}</p>
            </div>
          </div>
        ) : null}

        {isLoading ? (
          <div className="space-y-3 p-5" aria-live="polite">
            <p className="text-sm font-medium text-slate-700">Loading documents...</p>
            {[0, 1, 2].map((item) => (
              <div className="rounded-md border border-slate-200 p-4" key={item}>
                <div className="h-4 w-2/3 rounded bg-slate-100" />
                <div className="mt-3 flex flex-wrap gap-3">
                  <div className="h-4 w-20 rounded bg-slate-100" />
                  <div className="h-4 w-28 rounded bg-slate-100" />
                  <div className="h-4 w-32 rounded bg-slate-100" />
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {errorMessage ? (
          <div className="p-5" role="alert">
            <div className="rounded-md border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-semibold text-red-800">Could not load documents</p>
              <p className="mt-1 text-sm leading-6 text-red-700">{errorMessage}</p>
            </div>
          </div>
        ) : null}

        {!isLoading && !errorMessage && documents.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-base font-semibold text-slate-950">No documents yet</p>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">
              Upload a PDF, TXT, or DOCX file above. Once the backend stores it in
              Supabase, it will appear here with processing status and chunk count.
            </p>
          </div>
        ) : null}

        {!isLoading && !errorMessage && documents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-normal text-slate-500">
                <tr>
                  <th className="px-5 py-3">File</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Chunks</th>
                  <th className="px-5 py-3">Uploaded</th>
                  <th className="px-5 py-3">Updated</th>
                  {viewerRole === "owner" ? <th className="px-5 py-3">Actions</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((document) => {
                  const status = getStatusCopy(document.status);

                  return (
                    <tr
                      className="align-top transition hover:bg-slate-50"
                      key={document.document_id}
                    >
                      <td className="px-5 py-4">
                        <p className="max-w-md break-words font-medium text-slate-950">
                          {document.filename}
                        </p>
                        <p className="mt-1 text-xs uppercase text-slate-500">
                          {document.file_type}
                        </p>
                        <p className="mt-2 break-all font-mono text-xs text-slate-400">
                          {document.document_id}
                        </p>
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${status.className}`}
                        >
                          {status.label}
                        </span>
                        <p className="mt-2 text-xs text-slate-500">{status.detail}</p>
                        {document.error_message ? (
                          <div className="mt-3 max-w-sm rounded-md border border-red-200 bg-red-50 p-3">
                            <p className="text-xs font-semibold text-red-800">
                              Processing error
                            </p>
                            <p className="mt-1 text-xs leading-5 text-red-700">
                              {document.error_message}
                            </p>
                          </div>
                        ) : null}
                      </td>
                      <td className="px-5 py-4">
                        <p className="font-medium text-slate-800">
                          {formatChunkCount(document.chunks_count)}
                        </p>
                      </td>
                      <td className="px-5 py-4 text-slate-600">
                        {formatDate(document.created_at)}
                      </td>
                      <td className="px-5 py-4 text-slate-600">
                        {formatDate(document.updated_at)}
                      </td>
                      {viewerRole === "owner" ? (
                        <td className="px-5 py-4">
                          <button
                            className="rounded-md border border-red-200 bg-white px-3 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={deletingDocumentId === document.document_id}
                            onClick={() => handleDeleteDocument(document)}
                            type="button"
                          >
                            {deletingDocumentId === document.document_id ? "Deleting..." : "Delete"}
                          </button>
                        </td>
                      ) : null}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </section>
  );
}
