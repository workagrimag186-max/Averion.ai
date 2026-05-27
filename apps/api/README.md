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
SUPABASE_URL
SUPABASE_JWT_SECRET
ALLOWED_EMAIL_DOMAINS
AUTH_REQUIRED
UPLOAD_DIR
CORS_ORIGINS
VECTOR_DB_PATH
EMBEDDING_MODEL_NAME
RETRIEVAL_TOP_K
LLM_PROVIDER
LLM_PROVIDER_API_KEY
```

Real `.env` files must stay local and must not be committed to Git.
The Supabase auth variables are prepared for the upcoming authentication issues.
See [Supabase Auth Setup](../../docs/AUTH_SETUP.md) before filling them in.

## Organization And Auth Scope

API requests can include a Supabase access token:

```http
Authorization: Bearer <supabase-access-token>
```

The backend validates the token with `SUPABASE_JWT_SECRET`, maps the Supabase
Auth user to an Averion `users` profile, and resolves the organization scope
from that profile. Documents, conversations, and vector retrieval all use this
organization scope.

When a request is authenticated:

- Uploaded documents store `uploaded_by_user_id`.
- New conversations store `user_id`.
- Feedback stores the authenticated `user_id`.
- Feedback can only be attached to assistant messages inside the current organization.

For local development, `AUTH_REQUIRED=false` keeps the old
`DEFAULT_ORGANIZATION_ID` fallback when no bearer token is sent. Set
`AUTH_REQUIRED=true` when you want the API to reject unauthenticated requests.

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
