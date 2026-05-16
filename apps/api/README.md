# API App

This folder will contain the FastAPI backend and AI service for Averion.ai.

Planned responsibilities:

- Document upload API.
- Text extraction, cleaning, and chunking.
- Embeddings and vector search.
- RAG chat endpoint.
- Feedback API.

## Environment Variables

Copy the example file before running the backend locally:

```bash
cp .env.example .env
```

Current planned variables:

```text
DATABASE_URL
UPLOAD_DIR
VECTOR_DB_PATH
EMBEDDING_MODEL_NAME
RETRIEVAL_TOP_K
LLM_PROVIDER
LLM_PROVIDER_API_KEY
```

Real `.env` files must stay local and must not be committed to Git.
