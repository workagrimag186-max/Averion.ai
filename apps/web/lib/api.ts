export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";


export type DocumentUploadResponse = {
  document_id: string;
  filename: string;
  file_type: string;
  status: string;
  storage_path: string;
};


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
