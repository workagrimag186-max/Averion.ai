# Averion.ai

Averion.ai is an Enterprise AI Knowledge Copilot MVP.

The product lets a company upload internal documents, ask questions, receive source-cited answers, inspect source snippets, and give feedback when an answer is wrong.

## Problem

Companies usually have knowledge scattered across PDFs, handbooks, policy files, onboarding docs, and internal notes. Employees waste time searching, new team members onboard slowly, and answers become inconsistent.

Averion.ai solves this by becoming a single AI-powered place to search company knowledge.

## MVP Scope

Build only these four features first:

1. Document upload for PDF, TXT, and DOCX.
2. Smart chat using RAG.
3. Source citations and snippet highlighting.
4. Feedback with thumbs up/down and correction text.

Do not build Slack, Notion, email, multi-agent systems, or dashboards until the core intelligence works.

## How The MVP Works

```text
User uploads documents
        ↓
Backend extracts text
        ↓
Text is cleaned and split into chunks
        ↓
Chunks are converted into embeddings
        ↓
Embeddings are stored in a vector database
        ↓
User asks a question
        ↓
Relevant chunks are retrieved
        ↓
LLM writes an answer using retrieved context
        ↓
Frontend shows answer, citations, and feedback controls
```

This is called RAG: Retrieval-Augmented Generation. We are not training the LLM on company data for the MVP. Instead, we retrieve relevant company document chunks and give them to the LLM as context.

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui later, if needed

### Backend

- FastAPI
- Python
- Pydantic
- PostgreSQL later for metadata

### AI/ML

- Hugging Face Transformers
- Sentence Transformers
- LangChain
- Chroma or FAISS
- PyTorch later for fine-tuning experiments
- TensorFlow later for classification experiments

### Development

- GitHub Issues for task tracking
- Pull requests for every change
- GitHub Actions later for CI
- Gradio later for AI pipeline testing

## Planning Docs

- [Project Plan](docs/PROJECT_PLAN.md)
- [GitHub Issue Plan](docs/GITHUB_ISSUES.md)
- [Repository Structure](docs/REPO_STRUCTURE.md)

## Repository Structure

```text
Averion.ai/
  apps/
    web/           Next.js frontend
    api/           FastAPI backend and AI service
  packages/
    shared/        Shared API contracts later
  docs/            Planning and architecture
  scripts/         Developer scripts
  .github/
    workflows/     GitHub Actions workflows later
```

## Local Setup

The actual frontend and backend apps will be scaffolded in later issues. For now, this repository only contains the base structure and planning docs.

### Prerequisites

Install these before active development:

- Git
- Node.js LTS
- Python 3.11 or newer
- VS Code

### Clone the repository

```bash
git clone https://github.com/mitra9917/Averion.ai.git
cd Averion.ai
```

### Open in VS Code

```bash
code .
```

### Frontend setup

The frontend will live in:

```text
apps/web
```

After the Next.js app is created, the expected commands will be:

```bash
cd apps/web
npm install
npm run dev
```

### Backend setup

The backend will live in:

```text
apps/api
```

After the FastAPI app is created, the expected commands will be:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Environment Variables

Real environment files must not be committed.

Use example files later:

```text
apps/web/.env.example
apps/api/.env.example
```

Planned backend variables:

```text
DATABASE_URL=
VECTOR_DB_PATH=
EMBEDDING_MODEL_NAME=
LLM_PROVIDER_API_KEY=
```

Planned frontend variables:

```text
NEXT_PUBLIC_API_BASE_URL=
```

## Team Responsibilities

### Shubham

- Frontend app
- Upload UI
- Chat UI
- Citation panel
- Feedback UI
- API integration
- Product polish

### workagrimag186-max

- Text extraction
- Text cleaning
- Chunking
- Embeddings
- Vector database
- Retrieval
- RAG prompt and response quality
- AI evaluation

### Shared

- API contracts
- Database design
- Pull request reviews
- Demo preparation

## Development Workflow

Work through GitHub issues in milestone order:

1. M0 - Project Setup
2. M1 - Document Ingestion
3. M2 - Retrieval
4. M3 - RAG Chat
5. M4 - Citations and Feedback
6. M5 - Demo-Ready Product

Use this workflow for every issue:

1. Pick one issue.
2. Create a new branch from `main`.
3. Make the change locally.
4. Commit the change.
5. Push the branch.
6. Open a pull request.
7. Add `Closes #issue-number` in the PR description.
8. Ask the other person to review when possible.
9. Merge the PR.
10. Confirm the issue is closed.

Example branch names:

```text
issue-2-readme-setup
issue-3-nextjs-frontend
issue-4-fastapi-backend
```

Example PR title:

```text
[M0] Add root README with local setup instructions
```

Example PR description:

```md
Closes #2

What changed:
- Added project overview
- Added local setup instructions
- Added team workflow

Tested:
- Reviewed README locally
```

## Current Status

Current milestone:

```text
M0 - Project Setup
```

Current focus:

```text
Create a beginner-friendly foundation before writing product code.
```

## Important Rules

- Keep each pull request linked to one issue.
- Do not work on too many issues at once.
- Pull the latest `main` before starting a new branch.
- Never commit `.env` files.
- Keep the MVP small until upload, chat, citations, and feedback work end to end.
