# API App

This folder will contain the FastAPI backend and AI service for Averion.ai.

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

## Current API

- `GET /` - service welcome response
- `GET /health` - backend health check
