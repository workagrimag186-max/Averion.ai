export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";


export type DocumentUploadResponse = {
  document_id: string;
  filename: string;
  file_type: string;
  status: string;
  storage_path: string;
  metadata_stored: boolean;
  chunks_stored: number;
};


export type DocumentListItem = {
  document_id: string;
  filename: string;
  file_type: string;
  status: string;
  storage_path: string;
  chunks_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};


export type ChatRequest = {
  conversation_id: string | null;
  question: string;
};


export type ChatCitation = {
  document_id: string;
  chunk_index: number;
  chunk_id: string;
  filename: string;
  page_number: number | null;
  snippet: string;
  score: number | null;
};


export type ChatResponse = {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: ChatCitation[];
};


export async function listDocuments(): Promise<DocumentListItem[]> {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: "GET",
    cache: "no-store"
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message =
      typeof body?.detail === "string"
        ? body.detail
        : "Could not load documents.";

    throw new Error(message);
  }

  return response.json() as Promise<DocumentListItem[]>;
}


export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message =
      typeof body?.detail === "string"
        ? body.detail
        : "Document upload failed. Try again.";

    throw new Error(message);
  }

  return response.json() as Promise<DocumentUploadResponse>;
}
