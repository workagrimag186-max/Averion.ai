# Repository Structure

This structure keeps the project understandable for beginners while leaving room to grow into a real SaaS product.

```text
Averion.ai/
  apps/
    web/
      app/
      components/
      lib/
      public/
      tests/
      package.json
    api/
      app/
        main.py
        api/
        core/
        db/
        models/
        schemas/
        services/
        ai/
      tests/
      pyproject.toml
  packages/
    shared/
      api-contracts/
  docs/
    PROJECT_PLAN.md
    GITHUB_ISSUES.md
    REPO_STRUCTURE.md
  scripts/
    seed_demo_data.py
    export_feedback.py
  .github/
    workflows/
      ci.yml
  README.md
```

## Folder Purposes

### apps/web

The user-facing web application.

Important areas:

- `app/`: pages and routes.
- `components/`: reusable UI components.
- `lib/`: API clients, helpers, constants.
- `public/`: static assets.
- `tests/`: frontend tests.

### apps/api

The backend and AI service.

Important areas:

- `app/main.py`: FastAPI entrypoint.
- `app/api/`: route handlers.
- `app/core/`: settings, config, security helpers.
- `app/db/`: database connection and migrations.
- `app/models/`: database models.
- `app/schemas/`: Pydantic request and response schemas.
- `app/services/`: business logic.
- `app/ai/`: extraction, cleaning, chunking, embeddings, retrieval, RAG.
- `tests/`: backend tests.

### packages/shared

Shared API contract definitions or generated client types later. Keep this small at first.

### docs

Planning, architecture, issue backlog, setup notes, and demo scripts.

### scripts

One-off developer scripts such as demo data seeding and feedback export.

## Suggested Backend Module Layout

```text
apps/api/app/
  main.py
  core/
    config.py
  api/
    health.py
    documents.py
    chat.py
    feedback.py
  schemas/
    documents.py
    chat.py
    feedback.py
  services/
    document_service.py
    chat_service.py
    feedback_service.py
  ai/
    extraction.py
    cleaning.py
    chunking.py
    embeddings.py
    vector_store.py
    retrieval.py
    rag.py
    evaluation.py
```

## Suggested Frontend Screens

### Documents

Purpose:

- Upload files.
- See uploaded documents.
- See processing status.

Components:

- `DocumentUpload`
- `DocumentList`
- `DocumentStatusBadge`

### Chat

Purpose:

- Ask questions.
- Read AI answers.
- Inspect citations.
- Submit feedback.

Components:

- `ChatThread`
- `ChatInput`
- `AnswerMessage`
- `CitationPanel`
- `FeedbackControls`

## Pull Request Rules

Keep pull requests small:

- One issue per PR.
- Explain what changed.
- Include screenshots for frontend changes.
- Include test notes.
- Ask the other person to review.

Recommended PR title format:

```text
[M1] Implement document upload API
```

## Branch Naming

Use clear branch names:

```text
feature/document-upload-api
feature/chat-ui
feature/chunking-pipeline
docs/project-plan
test/ingestion-pipeline
```

## Beginner Development Rhythm

Weekly rhythm:

1. Pick 2 to 4 issues for the week.
2. Discuss unclear parts before coding.
3. Create a branch per issue.
4. Open a pull request early.
5. Review each other's pull requests.
6. Merge only when it runs locally.
7. Update the project board.

Daily rhythm:

1. Pull latest `main`.
2. Work on one issue.
3. Commit small changes.
4. Push branch.
5. Open or update PR.
6. Write what works and what is still broken.

## Learning Order

### Shubham: Web/backend path

1. Git and GitHub basics.
2. TypeScript basics.
3. Next.js app structure.
4. Forms and file uploads.
5. Calling APIs from frontend.
6. FastAPI route basics.
7. Database basics.
8. Auth and deployment after MVP flow works.

### AI/ML owner path

Primary owner: `workagrimag186-max`

1. Python project structure.
2. Text extraction from PDF/TXT/DOCX.
3. Text cleaning.
4. Tokenization.
5. Chunking.
6. Embeddings.
7. Vector similarity search.
8. RAG prompt construction.
9. Evaluation.
10. Fine-tuning later.

## Product Quality Checklist

Before calling the MVP complete:

- A user can upload a document.
- The document becomes searchable.
- A user can ask a question.
- The answer uses document context.
- The answer includes citations.
- The user can inspect source snippets.
- The user can give feedback.
- The app handles failed uploads.
- The app handles questions with no answer.
- The README lets a new developer run the project.
