"use client";

import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  CloudUpload,
  FileText,
  Filter,
  LoaderCircle,
  MessageSquare,
  RefreshCw,
  Search,
  Trash2,
  Upload,
  X
} from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  DragEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import {
  deleteDocument,
  DocumentListItem,
  getAccountProfile,
  listDocuments,
  uploadDocument
} from "@/lib/api";

const ACCEPTED_EXTENSIONS = [".pdf", ".txt", ".docx"];
const ACCEPTED_INPUT_TYPES = ".pdf,.txt,.docx";

function isAcceptedFile(file: File) {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((extension) => name.endsWith(extension));
}

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );
  const value = bytes / 1024 ** index;
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function statusClasses(status: string) {
  if (status === "ready") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
  }
  if (status === "failed") {
    return "border-red-500/30 bg-red-500/10 text-red-400";
  }
  return "border-amber-500/30 bg-amber-500/10 text-amber-400";
}

export function DocumentWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inputRef = useRef<HTMLInputElement>(null);
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(
    searchParams.get("document")
  );
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [viewerRole, setViewerRole] = useState<string | null>(null);
  const [query, setQuery] = useState(searchParams.get("search") ?? "");
  const [statusFilter, setStatusFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = useCallback(async (quiet = false) => {
    quiet ? setIsRefreshing(true) : setIsLoading(true);
    setError(null);
    try {
      const result = await listDocuments();
      setDocuments(result);
      setSelectedDocumentId((current) => {
        if (current && result.some((item) => item.document_id === current)) {
          return current;
        }
        return result[0]?.document_id ?? null;
      });
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Could not load documents."
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function loadInitialData() {
      setIsLoading(true);
      setError(null);
      try {
        const [result, profile] = await Promise.all([
          listDocuments(),
          getAccountProfile()
        ]);
        if (!active) return;
        setDocuments(result);
        setViewerRole(profile.role);
        setSelectedDocumentId((current) => {
          if (current && result.some((item) => item.document_id === current)) {
            return current;
          }
          return result[0]?.document_id ?? null;
        });
      } catch (loadError) {
        if (!active) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Could not load documents."
        );
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void loadInitialData();
    return () => {
      active = false;
    };
  }, [loadDocuments]);

  useEffect(() => {
    if (
      !documents.some(
        (document) =>
          document.status === "uploaded" || document.status === "processing"
      )
    ) {
      return;
    }
    const timer = window.setInterval(() => void loadDocuments(true), 5000);
    return () => window.clearInterval(timer);
  }, [documents, loadDocuments]);

  const selectedDocument = useMemo(
    () =>
      documents.find(
        (document) => document.document_id === selectedDocumentId
      ) ?? null,
    [documents, selectedDocumentId]
  );

  const filteredDocuments = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return documents.filter((document) => {
      const matchesQuery =
        !normalizedQuery ||
        document.filename.toLowerCase().includes(normalizedQuery) ||
        document.file_type.toLowerCase().includes(normalizedQuery);
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "processing"
          ? ["uploaded", "processing"].includes(document.status)
          : document.status === statusFilter);
      return matchesQuery && matchesStatus;
    });
  }, [documents, query, statusFilter]);

  const stats = useMemo(
    () => ({
      total: documents.length,
      ready: documents.filter((item) => item.status === "ready").length,
      processing: documents.filter((item) =>
        ["uploaded", "processing"].includes(item.status)
      ).length,
      failed: documents.filter((item) => item.status === "failed").length,
      chunks: documents.reduce((total, item) => total + item.chunks_count, 0)
    }),
    [documents]
  );

  function chooseFile(file: File | null) {
    setError(null);
    setMessage(null);
    if (!file) {
      setSelectedFile(null);
      return;
    }
    if (!isAcceptedFile(file)) {
      setSelectedFile(null);
      setError("Choose a PDF, TXT, or DOCX document.");
      return;
    }
    setSelectedFile(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    chooseFile(event.dataTransfer.files.item(0));
  }

  async function handleUpload() {
    if (!selectedFile || isUploading) return;
    setIsUploading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await uploadDocument(selectedFile);
      setMessage(`${result.filename} was uploaded and queued for indexing.`);
      setSelectedFile(null);
      if (inputRef.current) inputRef.current.value = "";
      await loadDocuments(true);
      setSelectedDocumentId(result.document_id);
    } catch (uploadError) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "Document upload failed."
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(document: DocumentListItem) {
    if (
      !window.confirm(
        `Delete "${document.filename}"? Its chunks and embeddings will also be removed from chat retrieval.`
      )
    ) {
      return;
    }
    setDeletingId(document.document_id);
    setError(null);
    setMessage(null);
    try {
      await deleteDocument(document.document_id);
      setDocuments((current) =>
        current.filter((item) => item.document_id !== document.document_id)
      );
      setSelectedDocumentId((current) =>
        current === document.document_id ? null : current
      );
      setMessage(
        `${document.filename} and its searchable knowledge were deleted.`
      );
    } catch (deleteError) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "Could not delete document."
      );
    } finally {
      setDeletingId(null);
    }
  }

  function askAboutDocument(document: DocumentListItem) {
    const params = new URLSearchParams({
      document: document.document_id,
      filename: document.filename
    });
    router.push(`/chat?${params.toString()}`);
  }

  return (
    <div className="mx-auto max-w-[1480px]">
      <div className="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-blue-400">
            Knowledge sources
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-white">Documents</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">
            Manage organization-wide files and monitor their indexing health.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md border border-white/10 bg-zinc-900 px-4 text-sm font-semibold text-zinc-200 transition hover:bg-zinc-800 disabled:opacity-50"
            disabled={isLoading || isRefreshing}
            onClick={() => void loadDocuments(true)}
            type="button"
          >
            <RefreshCw
              className={isRefreshing ? "animate-spin" : ""}
              size={16}
            />
            Refresh
          </button>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md bg-blue-500 px-4 text-sm font-semibold text-white transition hover:bg-blue-600"
            onClick={() => inputRef.current?.click()}
            type="button"
          >
            <Upload size={16} />
            Upload document
          </button>
        </div>
      </div>

      {(message || error) && (
        <div
          className={`mb-5 flex items-start gap-3 rounded-md border px-4 py-3 text-sm ${
            error
              ? "border-red-500/30 bg-red-500/10 text-red-200"
              : "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
          }`}
          role={error ? "alert" : "status"}
        >
          {error ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
          <span className="flex-1">{error ?? message}</span>
          <button
            aria-label="Dismiss message"
            className="text-current opacity-70 hover:opacity-100"
            onClick={() => {
              setError(null);
              setMessage(null);
            }}
            type="button"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-5">
        {[
          ["Total documents", stats.total, "text-white"],
          ["Ready", stats.ready, "text-emerald-400"],
          ["Processing", stats.processing, "text-amber-400"],
          ["Failed", stats.failed, "text-red-400"],
          ["Total chunks", stats.chunks.toLocaleString(), "text-white"]
        ].map(([label, value, color], index) => (
          <div
            className={`rounded-md border border-white/[0.08] bg-[#1a1a1a] p-4 ${
              index === 4 ? "col-span-2 xl:col-span-1" : ""
            }`}
            key={label}
          >
            <p className="text-[11px] font-semibold uppercase text-zinc-500">
              {label}
            </p>
            <p className={`mt-3 text-2xl font-semibold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 space-y-6">
          <div
            className="rounded-md border border-dashed border-white/15 bg-[#1a1a1a] p-6 text-center transition hover:border-blue-500/50"
            onDragOver={(event) => event.preventDefault()}
            onDrop={handleDrop}
          >
            <input
              accept={ACCEPTED_INPUT_TYPES}
              className="hidden"
              onChange={(event) =>
                chooseFile(event.target.files?.item(0) ?? null)
              }
              ref={inputRef}
              type="file"
            />
            <button
              className="mx-auto flex size-14 items-center justify-center rounded-full border border-white/10 bg-zinc-900 text-blue-400 transition hover:border-blue-500/40"
              onClick={() => inputRef.current?.click()}
              type="button"
            >
              <CloudUpload size={25} />
            </button>
            <h2 className="mt-4 text-base font-semibold text-white">
              Drop a document here or browse your computer
            </h2>
            <p className="mt-2 text-sm text-zinc-500">
              PDF, TXT, and DOCX files are supported.
            </p>

            {selectedFile && (
              <div className="mx-auto mt-5 flex max-w-xl items-center gap-3 rounded-md border border-white/10 bg-[#0d0d0d] p-3 text-left">
                <FileText className="shrink-0 text-zinc-400" size={19} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-zinc-200">
                    {selectedFile.name}
                  </p>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {formatBytes(selectedFile.size)}
                  </p>
                  {isUploading && (
                    <div className="mt-2 h-1 overflow-hidden rounded-full bg-zinc-800">
                      <div className="h-full w-2/3 animate-pulse rounded-full bg-blue-500" />
                    </div>
                  )}
                </div>
                <button
                  aria-label="Remove selected file"
                  className="rounded-md p-2 text-zinc-500 hover:bg-zinc-800 hover:text-white"
                  disabled={isUploading}
                  onClick={() => chooseFile(null)}
                  type="button"
                >
                  <X size={16} />
                </button>
                <button
                  className="inline-flex h-9 items-center gap-2 rounded-md bg-blue-500 px-3 text-xs font-semibold text-white hover:bg-blue-600 disabled:opacity-50"
                  disabled={isUploading}
                  onClick={() => void handleUpload()}
                  type="button"
                >
                  {isUploading ? (
                    <LoaderCircle className="animate-spin" size={15} />
                  ) : (
                    <Upload size={15} />
                  )}
                  {isUploading ? "Uploading" : "Upload"}
                </button>
              </div>
            )}
          </div>

          <section className="overflow-hidden rounded-md border border-white/[0.08] bg-[#1a1a1a]">
            <div className="flex flex-col gap-3 border-b border-white/[0.08] p-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-semibold text-white">Organization documents</h2>
                <p className="mt-1 text-xs text-zinc-500">
                  {filteredDocuments.length} of {documents.length} shown
                </p>
              </div>
              <div className="flex gap-2">
                <label className="relative min-w-0 flex-1 sm:w-64">
                  <Search
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600"
                    size={15}
                  />
                  <input
                    className="h-9 w-full rounded-md border border-white/10 bg-[#0d0d0d] pl-9 pr-3 text-xs text-white outline-none focus:border-blue-500/60"
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search documents..."
                    value={query}
                  />
                </label>
                <label className="relative">
                  <Filter
                    className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600"
                    size={14}
                  />
                  <select
                    aria-label="Filter documents by status"
                    className="h-9 rounded-md border border-white/10 bg-[#0d0d0d] pl-9 pr-7 text-xs text-zinc-300 outline-none focus:border-blue-500/60"
                    onChange={(event) => setStatusFilter(event.target.value)}
                    value={statusFilter}
                  >
                    <option value="all">All statuses</option>
                    <option value="ready">Ready</option>
                    <option value="processing">Processing</option>
                    <option value="failed">Failed</option>
                  </select>
                </label>
              </div>
            </div>

            {isLoading ? (
              <div className="flex min-h-64 items-center justify-center text-sm text-zinc-500">
                <LoaderCircle className="mr-2 animate-spin" size={17} />
                Loading documents
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="flex min-h-64 flex-col items-center justify-center px-6 text-center">
                <FileText className="text-zinc-700" size={34} />
                <p className="mt-3 text-sm font-semibold text-zinc-300">
                  No matching documents
                </p>
                <p className="mt-1 text-xs text-zinc-600">
                  Upload a file or adjust the current filters.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-[#131313] text-[11px] uppercase text-zinc-500">
                    <tr>
                      <th className="px-4 py-3">Filename</th>
                      <th className="px-4 py-3">Type</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Chunks</th>
                      <th className="px-4 py-3">Updated</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06]">
                    {filteredDocuments.map((document) => (
                      <tr
                        className={`cursor-pointer transition hover:bg-white/[0.03] ${
                          selectedDocumentId === document.document_id
                            ? "bg-white/[0.04]"
                            : ""
                        }`}
                        key={document.document_id}
                        onClick={() =>
                          setSelectedDocumentId(document.document_id)
                        }
                      >
                        <td className="max-w-xs px-4 py-3.5">
                          <div className="flex items-center gap-2.5">
                            <FileText
                              className="shrink-0 text-zinc-500"
                              size={17}
                            />
                            <span className="truncate font-semibold text-zinc-200">
                              {document.filename}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-zinc-500">
                          {document.file_type.toUpperCase()}
                        </td>
                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex rounded-md border px-2 py-1 text-[11px] font-semibold capitalize ${statusClasses(
                              document.status
                            )}`}
                          >
                            {document.status}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-zinc-400">
                          {document.chunks_count.toLocaleString()}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 text-xs text-zinc-500">
                          {formatDate(document.updated_at)}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <div className="flex justify-end gap-1">
                            <button
                              aria-label={`Ask about ${document.filename}`}
                              className="rounded-md p-2 text-zinc-500 hover:bg-blue-500/10 hover:text-blue-400"
                              onClick={(event) => {
                                event.stopPropagation();
                                askAboutDocument(document);
                              }}
                              title="Ask about this document"
                              type="button"
                            >
                              <MessageSquare size={16} />
                            </button>
                            {viewerRole === "owner" && (
                              <button
                                aria-label={`Delete ${document.filename}`}
                                className="rounded-md p-2 text-zinc-500 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
                                disabled={deletingId === document.document_id}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  void handleDelete(document);
                                }}
                                title="Delete document"
                                type="button"
                              >
                                {deletingId === document.document_id ? (
                                  <LoaderCircle
                                    className="animate-spin"
                                    size={16}
                                  />
                                ) : (
                                  <Trash2 size={16} />
                                )}
                              </button>
                            )}
                            <ChevronRight className="mt-2 text-zinc-700" size={16} />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>

        <aside className="h-fit rounded-md border border-white/[0.08] bg-[#1a1a1a] xl:sticky xl:top-24">
          <div className="border-b border-white/[0.08] px-5 py-4">
            <h2 className="font-semibold text-white">Document details</h2>
          </div>
          {selectedDocument ? (
            <div className="p-5">
              <div className="flex items-start gap-3">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-md border border-white/10 bg-zinc-900 text-zinc-400">
                  <FileText size={20} />
                </span>
                <div className="min-w-0">
                  <p className="break-words text-sm font-semibold text-white">
                    {selectedDocument.filename}
                  </p>
                  <p className="mt-1 break-all font-mono text-[10px] text-zinc-600">
                    {selectedDocument.document_id}
                  </p>
                </div>
              </div>

              <dl className="mt-6 grid grid-cols-2 gap-5 text-sm">
                <div>
                  <dt className="text-xs text-zinc-500">Status</dt>
                  <dd className="mt-2">
                    <span
                      className={`inline-flex rounded-md border px-2 py-1 text-[11px] font-semibold capitalize ${statusClasses(
                        selectedDocument.status
                      )}`}
                    >
                      {selectedDocument.status}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-zinc-500">Type</dt>
                  <dd className="mt-2 font-semibold text-zinc-200">
                    {selectedDocument.file_type.toUpperCase()}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-zinc-500">Chunks</dt>
                  <dd className="mt-2 font-semibold text-zinc-200">
                    {selectedDocument.chunks_count.toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-zinc-500">Updated</dt>
                  <dd className="mt-2 text-xs leading-5 text-zinc-300">
                    {formatDate(selectedDocument.updated_at)}
                  </dd>
                </div>
              </dl>

              <div className="mt-6 border-t border-white/[0.08] pt-5">
                <p className="text-xs font-semibold uppercase text-zinc-500">
                  Retrieval state
                </p>
                <p className="mt-2 text-sm leading-6 text-zinc-400">
                  {selectedDocument.status === "ready"
                    ? `${selectedDocument.chunks_count.toLocaleString()} indexed chunks are available to everyone in this organization.`
                    : selectedDocument.status === "failed"
                      ? "This document is not available to chat until its processing error is resolved."
                      : "The document is still being indexed. This panel refreshes automatically."}
                </p>
                {selectedDocument.error_message && (
                  <div className="mt-4 rounded-md border border-red-500/25 bg-red-500/10 p-3 text-xs leading-5 text-red-200">
                    {selectedDocument.error_message}
                  </div>
                )}
              </div>

              <button
                className="mt-6 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-white/10 bg-zinc-900 text-sm font-semibold text-zinc-200 transition hover:border-blue-500/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                disabled={selectedDocument.status !== "ready"}
                onClick={() => askAboutDocument(selectedDocument)}
                type="button"
              >
                <MessageSquare size={16} />
                Ask about this document
              </button>
            </div>
          ) : (
            <div className="p-8 text-center text-sm text-zinc-600">
              Select a document to inspect its current database state.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
