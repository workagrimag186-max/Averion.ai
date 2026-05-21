# API App

This folder contains the FastAPI backend and AI service for Averion.ai.

Planned responsibilities:

- Document upload API.
- Text extraction, cleaning, and chunking.
- Embeddings and vector search.
- RAG chat endpoint.
- Feedback API.

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example environment file:

```bash
cp .env.example .env
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

Open the health route:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "averion-api",
  "version": "0.1.0"
}
```

After setting `DATABASE_URL`, check the database connection:

```text
http://127.0.0.1:8000/health/database
```

Expected connected response:

```json
{
  "status": "ok",
  "database": "postgres",
  "connected": true,
  "error": null
}
```

## Environment Variables

Current planned variables:

```text
DATABASE_URL
DEFAULT_ORGANIZATION_ID
UPLOAD_DIR
CORS_ORIGINS
VECTOR_DB_PATH
EMBEDDING_MODEL_NAME
RETRIEVAL_TOP_K
LLM_PROVIDER
LLM_PROVIDER_API_KEY
```

Real `.env` files must stay local and must not be committed to Git.

## Organization Scope

The MVP does not have authentication or organization switching yet. Until that
exists, every API request is scoped through
`app.core.organization.get_current_organization_id()`, which currently returns
`DEFAULT_ORGANIZATION_ID`.

This temporary development path is intentionally isolated in one helper so it
can be replaced later by auth/session-based organization lookup. Documents,
conversations, and vector retrieval all use this organization scope.

## Current API

- `GET /` - service welcome response
- `GET /health` - backend health check
- `GET /health/database` - database connection health check
- `GET /documents` - list uploaded documents from the database
- `POST /documents/upload` - upload PDF, TXT, or DOCX files
- `POST /chat` - planned RAG chat endpoint contract

## Upload API

Use multipart form data with a `file` field:

```bash
curl -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@sample.pdf"
```

Successful response:

```json
{
  "document_id": "generated-uuid",
  "filename": "sample.pdf",
  "file_type": "pdf",
  "status": "uploaded",
  "storage_path": "uploads/generated-uuid/sample.pdf",
  "metadata_stored": true,
  "chunks_stored": 3
}
```

When `DATABASE_URL` is configured, uploads also create a row in the
`documents` table and stores extracted text chunks in `document_chunks`.
During development, the backend uses
`DEFAULT_ORGANIZATION_ID` and creates a temporary `Development Organization`
record automatically.

Vector search results include `document_id`, `chunk_index`, and a stable
`chunk_id` value formatted as `document_id:chunk_index`. That metadata links
Chroma vector results back to the matching Supabase `document_chunks` row.
Vector metadata also includes `organization_id`, and chat retrieval filters
results to the current organization.

## Chat API Contract

Issue 19 defines the request/response contract for the upcoming `POST /chat`
endpoint. The endpoint implementation comes later.

Request:

```json
{
  "conversation_id": null,
  "question": "What is our refund policy?"
}
```

Use `conversation_id: null` to start a new conversation. Send an existing
conversation id for follow-up questions.

Response:

```json
{
  "conversation_id": "conv_123",
  "message_id": "msg_456",
  "answer": "Refund requests are allowed within 30 days.",
  "citations": [
    {
      "document_id": "doc_123",
      "chunk_index": 0,
      "chunk_id": "doc_123:0",
      "filename": "policy.pdf",
      "page_number": 4,
      "snippet": "Refunds are available within 30 days.",
      "score": 0.12
    }
  ]
}
```

The `chunk_id` is formatted as `document_id:chunk_index`, matching the unique
Supabase `document_chunks(document_id, chunk_index)` record and the Chroma
vector metadata from S6.
