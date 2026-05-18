"use client";

import { useEffect, useState } from "react";

import { DocumentListItem, listDocuments } from "@/lib/api";

type DocumentListProps = {
  refreshKey: number;
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function statusClassName(status: string) {
  if (status === "ready") {
    return "bg-green-50 text-green-700 ring-green-200";
  }

  if (status === "failed") {
    return "bg-red-50 text-red-700 ring-red-200";
  }

  if (status === "processing") {
    return "bg-amber-50 text-amber-700 ring-amber-200";
  }

  return "bg-slate-50 text-slate-700 ring-slate-200";
}

export function DocumentList({ refreshKey }: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    async function loadDocuments() {
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

    loadDocuments();

    return () => {
      isCurrent = false;
    };
  }, [refreshKey]);

  return (
    <section className="mt-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-950">Uploaded documents</h2>
        <p className="text-sm text-slate-500">{documents.length} total</p>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {isLoading ? (
          <div className="p-5 text-sm text-slate-600">Loading documents...</div>
        ) : null}

        {errorMessage ? (
          <div className="border border-red-200 bg-red-50 p-5 text-sm text-red-700">
            {errorMessage}
          </div>
        ) : null}

        {!isLoading && !errorMessage && documents.length === 0 ? (
          <div className="p-5 text-sm text-slate-600">
            No documents found in the database yet.
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
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((document) => (
                  <tr key={document.document_id}>
                    <td className="px-5 py-4">
                      <p className="max-w-md break-words font-medium text-slate-950">
                        {document.filename}
                      </p>
                      <p className="mt-1 text-xs uppercase text-slate-500">
                        {document.file_type}
                      </p>
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${statusClassName(document.status)}`}
                      >
                        {document.status}
                      </span>
                      {document.error_message ? (
                        <p className="mt-2 max-w-xs text-xs text-red-600">
                          {document.error_message}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-5 py-4 text-slate-700">{document.chunks_count}</td>
                    <td className="px-5 py-4 text-slate-600">
                      {formatDate(document.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </section>
  );
}
