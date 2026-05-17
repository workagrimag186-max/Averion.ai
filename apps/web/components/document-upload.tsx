"use client";

import { DragEvent, useRef, useState } from "react";

import { DocumentUploadResponse, uploadDocument } from "@/lib/api";

const ACCEPTED_EXTENSIONS = [".pdf", ".txt", ".docx"];
const ACCEPTED_INPUT_TYPES = ".pdf,.txt,.docx";

type UploadState = "idle" | "uploading" | "success" | "error";

function isAcceptedFile(file: File) {
  const lowerName = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
}

function formatBytes(bytes: number) {
  if (bytes === 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** index;

  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

export function DocumentUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);

  function resetResult() {
    setErrorMessage(null);
    setUploadResult(null);
    setUploadState("idle");
  }

  function selectFile(file: File | null) {
    resetResult();

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!isAcceptedFile(file)) {
      setSelectedFile(null);
      setUploadState("error");
      setErrorMessage("Upload a PDF, TXT, or DOCX file.");
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) {
      setUploadState("error");
      setErrorMessage("Choose a document before uploading.");
      return;
    }

    setUploadState("uploading");
    setErrorMessage(null);
    setUploadResult(null);

    try {
      const result = await uploadDocument(selectedFile);
      setUploadResult(result);
      setUploadState("success");
    } catch (error) {
      setUploadState("error");
      setErrorMessage(error instanceof Error ? error.message : "Document upload failed.");
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    selectFile(event.dataTransfer.files.item(0));
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div
        className="rounded-lg border border-dashed border-slate-300 bg-white p-6 shadow-sm"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className="flex min-h-64 flex-col items-center justify-center rounded-md bg-slate-50 px-6 py-10 text-center">
          <div className="flex size-12 items-center justify-center rounded-lg bg-blue-600 text-sm font-semibold text-white">
            UP
          </div>
          <h2 className="mt-5 text-lg font-semibold text-slate-950">Upload a document</h2>
          <p className="mt-2 max-w-md text-sm leading-6 text-slate-600">
            Drop a company document here, or choose a file from your computer.
          </p>

          <input
            accept={ACCEPTED_INPUT_TYPES}
            className="hidden"
            onChange={(event) => selectFile(event.target.files?.item(0) ?? null)}
            ref={inputRef}
            type="file"
          />

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <button
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
              onClick={() => inputRef.current?.click()}
              type="button"
            >
              Choose file
            </button>
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!selectedFile || uploadState === "uploading"}
              onClick={handleUpload}
              type="button"
            >
              {uploadState === "uploading" ? "Uploading..." : "Upload"}
            </button>
          </div>

          <p className="mt-5 text-xs font-medium uppercase tracking-normal text-slate-500">
            PDF, TXT, DOCX
          </p>
        </div>
      </div>

      <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-950">Upload status</h2>

        {selectedFile ? (
          <div className="mt-4 rounded-md bg-slate-50 p-4">
            <p className="break-words text-sm font-medium text-slate-950">
              {selectedFile.name}
            </p>
            <p className="mt-1 text-sm text-slate-600">{formatBytes(selectedFile.size)}</p>
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-slate-600">
            No file selected yet. Choose a supported document to begin.
          </p>
        )}

        {errorMessage ? (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {errorMessage}
          </div>
        ) : null}

        {uploadResult ? (
          <div className="mt-4 space-y-3 rounded-md border border-green-200 bg-green-50 p-4">
            <p className="text-sm font-semibold text-green-800">Upload successful</p>
            <dl className="space-y-2 text-sm text-green-900">
              <div>
                <dt className="font-medium">Document ID</dt>
                <dd className="break-all font-mono text-xs">{uploadResult.document_id}</dd>
              </div>
              <div>
                <dt className="font-medium">Status</dt>
                <dd>{uploadResult.status}</dd>
              </div>
              <div>
                <dt className="font-medium">Type</dt>
                <dd>{uploadResult.file_type}</dd>
              </div>
            </dl>
          </div>
        ) : null}
      </aside>
    </section>
  );
}
