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
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use `--reload` only when actively editing backend Python files. The reloader
starts an additional process and can noticeably increase memory usage once the
embedding model is loaded.

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

The backend validates Supabase access tokens with the current JWT signing key
system. Tokens signed with asymmetric signing keys are verified through the
project JWKS endpoint derived from `SUPABASE_URL`. Legacy `HS256` tokens are
still verified with `SUPABASE_JWT_SECRET`. After validation, the backend maps
the Supabase Auth user to an Averion `users` profile and resolves the
organization scope from that profile. Documents, conversations, and vector
retrieval all use this organization scope.

New authenticated users are created in their own private organization and become
the owner of that workspace. Existing authenticated users keep their current
organization on later logins.

When a request is authenticated:

- Uploaded documents store `uploaded_by_user_id`.
- New conversations store `user_id`.
- Feedback stores the authenticated `user_id`.
- Feedback can only be attached to assistant messages inside the current organization.
- Account endpoints return the current user's organization and role.
- Organization owners can rename their workspace and update other members' roles.
- Organization owners can create invite records and remove other members.
- Removed members are moved into a new private workspace where they are owner.

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
- `GET /users/me` - get the current account profile
- `PATCH /users/me` - update editable profile fields
- `GET /users/team` - list members in the current organization
- `PATCH /users/organization` - owner-only organization rename
- `PATCH /users/team/{user_id}/role` - owner-only member role update
- `POST /users/invitations` - owner-only invitation creation
- `GET /users/invitations` - list current user's pending invitations
- `POST /users/invitations/{invitation_id}/accept` - accept a pending invitation
- `DELETE /users/team/{user_id}` - owner-only member removal

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
shared Supabase pgvector results back to the matching Supabase
`document_chunks` row. Vector metadata also includes `organization_id`, and
chat retrieval filters results to the current organization.

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
Supabase `document_chunks(document_id, chunk_index)` record and the shared
`document_embeddings` pgvector metadata.
