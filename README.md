# Averion.ai

Averion.ai is an Enterprise AI Knowledge Copilot MVP.

The product lets a company upload internal documents, ask questions, receive source-cited answers, inspect source snippets, and give feedback when an answer is wrong.

## MVP Scope

Build only these four features first:

1. Document upload for PDF, TXT, and DOCX.
2. Smart chat using RAG.
3. Source citations and snippet highlighting.
4. Feedback with thumbs up/down and correction text.

Do not build Slack, Notion, email, multi-agent systems, or dashboards until the core intelligence works.

## Planning Docs

- [Project Plan](docs/PROJECT_PLAN.md)
- [GitHub Issue Plan](docs/GITHUB_ISSUES.md)
- [Repository Structure](docs/REPO_STRUCTURE.md)

## Recommended Structure

```text
apps/
  web/      Next.js frontend
  api/      FastAPI backend and AI service
packages/
  shared/   shared API contracts later
docs/       planning and architecture
scripts/    developer scripts
```

## Development Rule

Work through GitHub issues in milestone order:

1. M0 - Project Setup
2. M1 - Document Ingestion
3. M2 - Retrieval
4. M3 - RAG Chat
5. M4 - Citations and Feedback
6. M5 - Demo-Ready Product

Keep every pull request small and linked to one issue.
