# GitHub Issue Plan

Use these labels first, then create the issues in the order below.

## Labels

| Label | Color | Purpose |
| --- | --- | --- |
| `area:frontend` | `1D76DB` | Frontend UI and client behavior |
| `area:backend` | `5319E7` | API, database, and server logic |
| `area:ai-ml` | `0E8A16` | RAG, embeddings, NLP, model work |
| `area:database` | `FBCA04` | Schema, migrations, and stored metadata |
| `area:auth` | `5319E7` | Login, signup, sessions, protected routes, and account access |
| `area:devops` | `C5DEF5` | CI, environment, deployment |
| `area:docs` | `0075CA` | README, planning, onboarding |
| `type:feature` | `A2EEEF` | New user-facing or developer-facing capability |
| `type:task` | `D4C5F9` | Setup, chores, or non-feature work |
| `type:bug` | `D73A4A` | Broken behavior |
| `type:test` | `BFDADC` | Test coverage |
| `priority:p0` | `B60205` | Blocks everything |
| `priority:p1` | `D93F0B` | Important for MVP |
| `priority:p2` | `FBCA04` | Useful after main flow works |
| `good first issue` | `7057FF` | Beginner-friendly |
| `blocked` | `000000` | Waiting on another issue |
| `owner:web` | `0052CC` | Owned by web developer |
| `owner:ai-ml` | `128A0C` | Owned by AI/ML developer |
| `owner:shared` | `666666` | Requires both developers |

## Milestones

1. `M0 - Project Setup`
2. `M1 - Document Ingestion`
3. `M2 - Retrieval`
4. `M2.5 - Supabase Database Integration`
5. `M3 - RAG Chat`
6. `M4 - Citations and Feedback`
7. `M5 - Demo-Ready Product`
8. `M6 - Authentication and Account System`

## Issue Creation Order

Create issues in this order. Each issue should be small enough to finish in one focused pull request.

## M0 - Project Setup

### 1. Create monorepo project structure

Labels: `type:task`, `area:docs`, `area:backend`, `area:frontend`, `priority:p0`, `owner:shared`

Description:

Create the base folder structure for the project so frontend, backend, AI pipeline, docs, and tests have clear homes.

Acceptance criteria:

- Repository has `apps/web`, `apps/api`, `packages`, `docs`, and `scripts` folders.
- Root README explains what each folder is for.
- Both developers know where to add their work.

Depends on: none.

### 2. Add root README with local setup instructions

Labels: `type:task`, `area:docs`, `priority:p0`, `good first issue`, `owner:shared`

Description:

Write a beginner-friendly README explaining the product, MVP scope, tech stack, and how to run the project locally.

Acceptance criteria:

- README has product summary.
- README lists prerequisites.
- README has frontend setup commands.
- README has backend setup commands.
- README has environment variable instructions.

Depends on: issue 1.

### 3. Scaffold Next.js frontend app

Labels: `type:task`, `area:frontend`, `priority:p0`, `owner:web`

Description:

Create the web app that will later contain document upload, chat, citations, and feedback UI.

Acceptance criteria:

- `apps/web` contains a TypeScript Next.js app.
- App runs locally.
- Home page uses a simple application shell, not a landing page.
- Basic navigation includes Documents and Chat.

Depends on: issue 1.

### 4. Scaffold FastAPI backend app

Labels: `type:task`, `area:backend`, `priority:p0`, `owner:ai-ml`

Description:

Create the backend API service that will handle uploads, ingestion, retrieval, chat, and feedback.

Acceptance criteria:

- `apps/api` contains a FastAPI app.
- Health route returns `{ "status": "ok" }`.
- App runs locally with `uvicorn`.
- Pydantic is configured for request and response models.

Depends on: issue 1.

### 5. Add environment variable examples

Labels: `type:task`, `area:devops`, `priority:p1`, `good first issue`, `owner:shared`

Description:

Add `.env.example` files for frontend and backend.

Acceptance criteria:

- Frontend env example includes API base URL.
- Backend env example includes database URL, vector DB path, model names, and LLM provider key placeholder.
- Real `.env` files are ignored by Git.

Depends on: issues 3 and 4.

### 6. Add basic CI checks

Labels: `type:task`, `area:devops`, `priority:p1`, `owner:shared`

Description:

Add GitHub Actions to run basic frontend and backend checks on pull requests.

Acceptance criteria:

- CI runs on pull requests.
- Frontend lint/typecheck command is included if available.
- Backend test command is included if available.
- CI is documented in README.

Depends on: issues 3 and 4.

## M1 - Document Ingestion

### 7. Design database schema for documents, chunks, chat, and feedback

Labels: `type:task`, `area:database`, `area:backend`, `priority:p0`, `owner:shared`

Description:

Define the first database schema for organizations, users, documents, chunks, conversations, messages, and feedback.

Acceptance criteria:

- Schema includes tables listed in `docs/PROJECT_PLAN.md`.
- Each document belongs to an organization.
- Each chunk belongs to a document.
- Feedback can be linked to a model answer.

Depends on: issue 4.

### 8. Implement document upload API

Labels: `type:feature`, `area:backend`, `priority:p0`, `owner:web`

Description:

Create an API endpoint that accepts PDF, TXT, and DOCX uploads and creates a document record.

Acceptance criteria:

- `POST /documents/upload` accepts supported file types.
- Unsupported file types return a clear error.
- Uploaded file metadata is stored.
- Response includes document id and processing status.

Depends on: issues 4 and 7.

### 9. Build document upload UI

Labels: `type:feature`, `area:frontend`, `priority:p0`, `owner:web`

Description:

Create a simple upload screen for PDF, TXT, and DOCX files.

Acceptance criteria:

- User can select or drag a supported file.
- UI shows uploading, success, and error states.
- UI shows returned document id/status.
- Unsupported file types are rejected with a helpful message.

Depends on: issues 3 and 8.

### 10. Implement text extraction for PDF, TXT, and DOCX

Labels: `type:feature`, `area:ai-ml`, `priority:p0`, `owner:ai-ml`

Description:

Extract readable text from uploaded documents.

Acceptance criteria:

- TXT extraction works.
- PDF extraction works with page numbers when possible.
- DOCX extraction works.
- Extraction failures are stored on the document status.

Depends on: issue 8.

### 11. Implement text cleaning pipeline

Labels: `type:feature`, `area:ai-ml`, `priority:p1`, `owner:ai-ml`

Description:

Clean extracted text before chunking.

Acceptance criteria:

- Removes repeated whitespace.
- Handles empty/null text safely.
- Removes obvious extraction noise where possible.
- Keeps enough original text for citations to remain trustworthy.

Depends on: issue 10.

### 12. Implement chunking pipeline

Labels: `type:feature`, `area:ai-ml`, `priority:p0`, `owner:ai-ml`

Description:

Split cleaned text into overlapping chunks and store chunk metadata.

Acceptance criteria:

- Chunks are roughly 600 to 900 tokens.
- Chunks have 100 to 150 token overlap.
- Chunks store document id, chunk index, page number if available, and text.
- Empty chunks are not saved.

Depends on: issue 11.

### 13. Add ingestion tests with sample files

Labels: `type:test`, `area:ai-ml`, `area:backend`, `priority:p1`, `owner:ai-ml`

Description:

Add test coverage for extraction, cleaning, and chunking.

Acceptance criteria:

- Tests cover TXT, PDF, and DOCX samples.
- Tests cover empty document handling.
- Tests verify chunks include metadata.

Depends on: issues 10, 11, and 12.

## M2 - Retrieval

### 14. Choose and document the MVP embedding model

Labels: `type:task`, `area:ai-ml`, `area:docs`, `priority:p1`, `owner:ai-ml`

Description:

Pick the first embedding model and explain why.

Suggested default:

`sentence-transformers/all-MiniLM-L6-v2`

Acceptance criteria:

- Model name is documented.
- Tradeoffs are explained in beginner-friendly language.
- Model can run locally for development.

Depends on: issue 12.

### 15. Generate embeddings for document chunks

Labels: `type:feature`, `area:ai-ml`, `priority:p0`, `owner:ai-ml`

Description:

Convert each document chunk into an embedding vector.

Acceptance criteria:

- Embeddings are generated after chunking.
- Each embedding is linked to a chunk.
- Failures update document status.
- Model name/version is stored or logged.

Depends on: issue 14.

### 16. Set up local vector database

Labels: `type:feature`, `area:ai-ml`, `area:backend`, `priority:p0`, `owner:ai-ml`

Description:

Set up Chroma for local vector search.

Acceptance criteria:

- Vector DB persists locally.
- Chunk ids and metadata are stored with vectors.
- Similarity search returns top matching chunks.

Depends on: issue 15.

### 17. Implement retrieval service

Labels: `type:feature`, `area:ai-ml`, `area:backend`, `priority:p0`, `owner:ai-ml`

Description:

Create a backend service that takes a question and returns relevant chunks.

Acceptance criteria:

- Service embeds the question.
- Service retrieves top K chunks.
- Results include text and citation metadata.
- K is configurable.

Depends on: issue 16.

### 18. Create simple retrieval evaluation set

Labels: `type:test`, `area:ai-ml`, `priority:p1`, `owner:ai-ml`

Description:

Create a small evaluation file with sample questions and expected source documents/chunks.

Acceptance criteria:

- At least 10 sample questions exist.
- Expected source document is listed for each question.
- Retrieval success can be checked manually or by script.

Depends on: issue 17.

## M3 - RAG Chat

### Supabase Course Correction Before M3

Issues S1-S6 were added between the original M2 work and M3 so the MVP has a real Supabase-backed data foundation before chat work starts.

Completed Supabase foundation:

- S1: Supabase project/schema setup and verification docs.
- S2: Backend `DATABASE_URL` connection health check.
- S3: Uploads store document metadata in Supabase.
- S4: Uploads store extracted chunks in `document_chunks`.
- S5: Documents page lists uploaded documents from Supabase.
- S6 / issue 46: Vector store metadata links retrieval results to database chunks through `document_id`, `chunk_index`, and `chunk_id`.

This changes the meaning of issues 19-34: do not rebuild metadata/chunk storage. Build on the Supabase tables and shared pgvector metadata that now exist.

### 19. Design chat API response format with citations

Labels: `type:task`, `area:backend`, `area:frontend`, `area:ai-ml`, `priority:p0`, `owner:shared`

Description:

Finalize the request and response shape for chat using the Supabase + pgvector foundation from S1-S6.

Acceptance criteria:

- Request includes conversation id and question.
- Response includes answer text.
- Response includes citation array.
- Citation objects include `document_id`, `chunk_index`, `chunk_id`, filename, page number when available, and snippet.
- Contract explains how `chunk_id` maps back to Supabase `document_chunks`.
- Frontend and backend owners both approve the contract.

Depends on: issue 17 and S6 / issue 46.

### 20. Implement RAG prompt builder

Labels: `type:feature`, `area:ai-ml`, `priority:p0`, `owner:ai-ml`

Description:

Build the prompt that gives retrieved chunks to the LLM and asks for a grounded answer.

Acceptance criteria:

- Prompt tells model to answer only from context.
- Prompt tells model to say when information is missing.
- Prompt includes citation ids for chunks.
- Prompt input uses retrieved chunks that include `document_id`, `chunk_index`, and `chunk_id`.
- Prompt is easy to test without the web UI.

Depends on: issue 19.

### 21. Integrate MVP LLM provider

Labels: `type:feature`, `area:ai-ml`, `area:backend`, `priority:p0`, `owner:ai-ml`

Description:

Connect the RAG chain to the first LLM provider.

Acceptance criteria:

- LLM provider key is loaded from environment variables.
- Chat endpoint can produce an answer.
- Failure states are handled clearly.
- Provider can be swapped later without rewriting the frontend.
- LLM provider receives only retrieved context, not raw database credentials or full document tables.

Depends on: issue 20.

### 22. Implement chat API endpoint

Labels: `type:feature`, `area:backend`, `priority:p0`, `owner:web`

Description:

Expose the RAG pipeline through `POST /chat`.

Acceptance criteria:

- Endpoint accepts a user question.
- Endpoint calls retrieval, prompt building, and LLM generation.
- Endpoint stores conversation and message records in Supabase.
- Endpoint returns answer and citations.
- Endpoint citations preserve `chunk_id` so source chunks can be resolved later.
- Endpoint handles no-retrieval and LLM-provider failures cleanly.

Depends on: issues 19, 20, 21, and S6 / issue 46.

### 23. Build chat UI

Labels: `type:feature`, `area:frontend`, `priority:p0`, `owner:web`

Description:

Create the main chat screen.

Acceptance criteria:

- User can type and submit a question.
- User sees their message and AI answer.
- UI shows loading state while waiting.
- UI shows errors cleanly.
- UI can render citation placeholders returned by the chat API, even before the full source panel is built.

Depends on: issue 22.

## M4 - Citations and Feedback

### 24. Build citation/source panel

Labels: `type:feature`, `area:frontend`, `priority:p0`, `owner:web`

Description:

Display the sources used for an answer.

Acceptance criteria:

- Each answer can show its citations.
- Citation displays filename, page number if available, snippet, and `chunk_id` for debugging.
- User can expand/collapse source snippets.
- Missing citation metadata does not break UI.

Depends on: issues 23 and 25.

### 25. Improve backend citation mapping

Labels: `type:feature`, `area:ai-ml`, `area:backend`, `priority:p1`, `owner:ai-ml`

Description:

Resolve citation metadata from retrieval results and Supabase chunk records so returned citations point back to the exact chunks used by the answer.

Acceptance criteria:

- Citations include `chunk_id`.
- Citations can use `document_id` + `chunk_index` to find the matching Supabase `document_chunks` row.
- Citations include document id and filename.
- Citations include page number when available.
- Citations include source snippet.

Depends on: issue 22 and S6 / issue 46.

### 26. Build feedback UI

Labels: `type:feature`, `area:frontend`, `priority:p0`, `owner:web`

Description:

Allow users to rate AI answers and provide corrections.

Acceptance criteria:

- Each AI answer has thumbs up/down.
- Downvote reveals correction input.
- Submit state is visible.
- Success and error states are handled.
- UI sends feedback against the assistant message id returned by the chat API.

Depends on: issue 23.

### 27. Implement feedback API and storage

Labels: `type:feature`, `area:backend`, `area:database`, `priority:p0`, `owner:web`

Description:

Store user feedback for model answers.

Acceptance criteria:

- `POST /feedback` stores message id, rating, user id if available, and correction text.
- Feedback links to the original answer.
- Invalid message ids return clear errors.
- Feedback can be queried later for analysis.
- Feedback is stored in the existing Supabase `feedback` table from S1.

Depends on: issues 22 and 26.

### 28. Create feedback review dataset export

Labels: `type:task`, `area:ai-ml`, `priority:p2`, `owner:ai-ml`

Description:

Create a simple way to export negative feedback and corrections for future model/retrieval improvement.

Acceptance criteria:

- Export includes question, answer, citations, rating, and correction.
- Export format is JSONL or CSV.
- Script is documented.
- Export reads from Supabase conversations, messages, and feedback tables.

Depends on: issue 27.

## M5 - Demo-Ready Product

### 29. Enhance document list and processing status UI

Labels: `type:feature`, `area:frontend`, `priority:p1`, `owner:web`

Description:

Improve the Supabase-backed document list created in S5 so it feels demo-ready.

Acceptance criteria:

- Documents page keeps listing uploaded files from Supabase.
- Status values are visible: uploaded, processing, ready, failed.
- Failed documents show a clear error.
- Empty and loading states are polished.
- Chunk count is visible and readable.

Depends on: S5.

### 30. Add organization-ready data scoping

Labels: `type:task`, `area:backend`, `area:database`, `priority:p1`, `owner:shared`

Description:

Prepare the app for future multi-tenant SaaS usage beyond the temporary development organization added during S3/S4.

Acceptance criteria:

- Documents are scoped by organization id.
- Conversations are scoped by organization id.
- Retrieval only searches within the current organization.
- Temporary development organization behavior remains documented.
- The current hardcoded `DEFAULT_ORGANIZATION_ID` path is clearly isolated for development only.

Depends on: S3, S5, S6 / issue 46, and issue 22.

### 31. Add error, empty, and loading states across MVP UI

Labels: `type:task`, `area:frontend`, `priority:p1`, `owner:web`

Description:

Polish the UI so the product feels usable during demos.

Acceptance criteria:

- Upload screen has empty/error/loading states.
- Chat screen has empty/error/loading states.
- Citation panel has empty/error/loading states.
- Feedback controls handle submitted/failed states.
- Documents list has empty/error/loading states.

Depends on: issues 23, 24, 26, and 29.

### 32. Add backend tests for core API endpoints

Labels: `type:test`, `area:backend`, `priority:p1`, `owner:web`

Description:

Extend backend endpoint coverage now that upload, Supabase document listing, chat, and feedback exist.

Acceptance criteria:

- Health route test remains green.
- Upload endpoint tests remain green.
- Documents list endpoint tests remain green.
- Feedback endpoint test exists.
- Chat endpoint has a mocked AI pipeline test.
- Tests do not require live LLM calls.

Depends on: S5, issues 22 and 27.

### 33. Add end-to-end demo script

Labels: `type:task`, `area:docs`, `priority:p1`, `owner:shared`

Description:

Write a repeatable script for demonstrating the product.

Acceptance criteria:

- Demo document is listed.
- Demo questions are listed.
- Expected answer behavior is described.
- Feedback example is included.
- Supabase setup and local env requirements are included.

Depends on: issues 23, 24, 26, and 29.

### 34. Prepare deployment plan

Labels: `type:task`, `area:devops`, `priority:p2`, `owner:shared`

Description:

Document how the MVP will be deployed.

Acceptance criteria:

- Frontend deployment target is chosen.
- Backend deployment target is chosen.
- Database hosting option is Supabase unless a later decision changes it.
- Vector DB persistence plan is documented.
- Required environment variables are listed.
- Supabase connection string handling is documented without exposing secrets.

Depends on: milestone 4.

## M6 - Authentication and Account System

Auth should be added after the core document, chat, citation, and feedback flow exists. Averion already has Supabase, organizations, and users in the database, so the safest path is to use Supabase Auth instead of building password hashing and session management manually.

Recommended auth scope:

- Email/password signup.
- Email/password signin.
- Email verification through Supabase.
- Google signin for Gmail/Google users.
- Normal email format validation for all email/password users.
- Optional Gmail-only allowlist later if the product truly needs it.
- Protected app routes.
- Logout.
- Account/profile page.
- Authenticated user and organization context in the backend.

Implementation note:

Do not commit real Supabase keys, service keys, or `.env` files. Only update `.env.example` files and setup docs.

### 35. Configure Supabase Auth for Averion

Labels: `type:task`, `area:auth`, `area:database`, `priority:p0`, `owner:shared`

Description:

Enable Supabase Auth for the project and document the required local environment variables.

Acceptance criteria:

- Supabase email/password auth provider is enabled.
- Email verification behavior is decided and documented.
- Google provider setup is documented, even if implementation happens in a later issue.
- Frontend env example includes Supabase URL and anon key.
- Backend env example includes Supabase project/JWT settings needed to validate users.
- Setup docs explain where to find the Supabase values.
- Real `.env` files remain ignored by Git.

Depends on: issue 34.

### 36. Add auth database profile mapping

Labels: `type:task`, `area:auth`, `area:database`, `area:backend`, `priority:p0`, `owner:shared`

Description:

Connect Supabase Auth identities to Averion's existing `users` profile table and organization model.

Acceptance criteria:

- Existing `users` table is extended safely for auth profile data.
- User profile records can be linked to Supabase Auth users.
- Profile data supports email, display name, role, organization, and optional account fields.
- New authenticated users can be mapped to an organization.
- Existing development organization flow is not broken during local testing.
- Schema docs are updated.

Suggested profile fields:

- `auth_user_id`
- `email`
- `name`
- `role`
- `organization_id`
- `avatar_url`
- `job_title`

Depends on: issue 35.

### 37. Build signup and signin pages

Labels: `type:feature`, `area:auth`, `area:frontend`, `priority:p0`, `owner:web`

Description:

Create user-facing signup and signin pages for email/password auth.

Acceptance criteria:

- `/signup` page exists.
- `/login` page exists.
- Email format validation is present.
- Password validation is present.
- Loading, success, and error states are shown clearly.
- Signup tells the user to verify their email if email confirmation is enabled.
- Logged-in users are not encouraged to sign in again.
- Existing app pages still build and render.

Depends on: issue 35.

### 38. Add Google and Gmail signin

Labels: `type:feature`, `area:auth`, `area:frontend`, `priority:p1`, `owner:web`

Description:

Add Google OAuth signin so Gmail/Google users can enter the app without email/password.

Acceptance criteria:

- Login page has a "Continue with Google" action.
- Signup page has a "Continue with Google" action.
- OAuth callback route works locally.
- Google user email is stored in the user profile.
- Auth errors are shown clearly.
- If Gmail-only mode is later enabled, non-Gmail users are blocked with a helpful message.

Depends on: issues 35 and 37.

### 39. Protect app routes and add logout

Labels: `type:feature`, `area:auth`, `area:frontend`, `priority:p0`, `owner:web`

Description:

Require a valid session before users can access the product pages.

Acceptance criteria:

- `/`, `/documents`, `/chat`, and `/account` require login.
- Logged-out users are redirected to `/login`.
- Logged-in users are redirected away from `/login` and `/signup`.
- Header shows an account/profile entry.
- Logout clears the session.
- Session persists after browser refresh.

Depends on: issue 37.

### 40. Add backend auth context

Labels: `type:feature`, `area:auth`, `area:backend`, `priority:p0`, `owner:shared`

Description:

Replace the temporary development-only organization helper with authenticated user and organization context.

Acceptance criteria:

- Frontend sends the Supabase access token to FastAPI requests.
- Backend validates the access token.
- Backend resolves the current user id and organization id.
- Existing `get_current_organization_id()` path is upgraded or replaced cleanly.
- Documents, chat, and feedback endpoints can depend on authenticated context.
- Local development fallback is explicit and documented.

Depends on: issues 36 and 39.

### 41. Connect documents, chat, and feedback to logged-in users

Labels: `type:feature`, `area:auth`, `area:backend`, `area:database`, `priority:p1`, `owner:shared`

Description:

Store real user ownership for the main product actions.

Acceptance criteria:

- Uploaded documents store `uploaded_by_user_id`.
- New conversations store `user_id`.
- Feedback stores authenticated `user_id`.
- Users only see documents from their organization.
- Users cannot access another organization's conversations or documents.
- Existing upload, chat, citation, and feedback tests are updated as needed.

Depends on: issue 40.

### 42. Build account and profile page

Labels: `type:feature`, `area:auth`, `area:frontend`, `area:database`, `priority:p1`, `owner:web`

Description:

Create an account/profile screen where users can see and update basic profile information.

Acceptance criteria:

- `/account` or `/settings/profile` page exists.
- Page shows email, display name, role, and organization.
- User can edit display name.
- User can edit optional job title if that field is added.
- Email is read-only for the MVP.
- Logout is available from the account area.
- Empty/loading/error states are handled.

Depends on: issues 39 and 41.

### 43. Add auth tests and documentation

Labels: `type:test`, `area:auth`, `area:docs`, `priority:p1`, `owner:shared`

Description:

Add verification coverage and beginner-friendly setup docs for authentication.

Acceptance criteria:

- Frontend build/typecheck passes.
- Backend tests cover missing/invalid auth behavior.
- Backend tests cover authenticated organization scoping.
- Docs explain Supabase Auth setup.
- Docs explain local `.env` updates.
- Manual test checklist covers signup, login, Google signin, logout, upload, chat, and feedback.
- Tests do not require committing real auth secrets.

Depends on: issues 35 through 42.

### 44. Support Supabase JWT signing keys

Labels: `type:bug`, `area:auth`, `area:backend`, `priority:p0`, `owner:shared`

Description:

Make backend access-token validation work with Supabase projects using the newer asymmetric JWT signing key system.

Acceptance criteria:

- Backend validates asymmetric Supabase access tokens through the project JWKS endpoint.
- Legacy HS256 token validation still works for older projects.
- SSL certificate handling works in local Python environments.
- Invalid token and JWKS fetch failures return clear API errors instead of crashing.
- Backend auth tests pass.

Depends on: issues 40 and 43.

### 45. Add organization and team settings foundation

Labels: `type:feature`, `area:auth`, `area:frontend`, `area:backend`, `area:database`, `priority:p1`, `owner:shared`

Description:

Add a safe first version of workspace management on top of the account system.

Acceptance criteria:

- Account page shows current organization and member list.
- Organization owners can rename the organization.
- Organization owners can change other members between `member` and `owner`.
- Owners cannot accidentally demote themselves.
- Non-owner members can view workspace information but cannot edit organization or role settings.
- Backend endpoints enforce owner-only organization and role changes.
- Tests cover owner and member permission behavior.

Depends on: issues 42, 43, and 44.

### 46. Create isolated workspace per new user

Labels: `type:bug`, `area:auth`, `area:backend`, `area:database`, `priority:p0`, `owner:shared`

Description:

Prevent unrelated signup accounts from sharing the same development organization and seeing each other's uploaded documents.

Acceptance criteria:

- New authenticated users are created in a private organization by default.
- New authenticated users become `owner` of their private organization.
- Existing authenticated users keep their current organization on repeat login.
- Documents, conversations, chat retrieval, and feedback remain organization-scoped.
- Optional migration SQL exists for splitting old test users out of the shared development organization.
- Tests cover private workspace creation and existing workspace preservation.

Depends on: issues 40, 41, and 45.

### 47. Add organization invites and member removal

Labels: `type:feature`, `area:auth`, `area:frontend`, `area:backend`, `area:database`, `priority:p0`, `owner:shared`

Description:

Let organization owners invite users into their workspace and remove members safely.

Acceptance criteria:

- Owners can send an invite to another user's email address.
- Invites store sender, target email, target organization, status, and expiry.
- Invited users can accept an invite after signing in.
- When a user accepts an invite, they move into the inviter's organization as `member`.
- If the invited user was owner of their own private signup organization, accepting the invite changes them to `member` in the target organization.
- Owners can remove a member from their organization.
- Removed members are moved into a new private organization where they are the `owner`.
- Members cannot invite, accept on behalf of others, remove users, or change organization membership.
- Owners cannot remove themselves.
- Documents and conversations remain scoped to the organization where they were created.
- Backend tests cover invite, accept, remove, and permission rules.

Depends on: issues 45 and 46.

### 48. Harden owner-to-owner role management

Labels: `type:test`, `area:auth`, `area:backend`, `area:frontend`, `priority:p1`, `owner:shared`

Description:

Make role management rules explicit for organizations with multiple owners.

Acceptance criteria:

- An owner can promote a member to owner.
- An owner can demote another owner to member.
- An owner cannot demote themselves.
- A member cannot change anyone's role.
- Account team UI allows owner-to-owner role changes for other users.
- Backend tests cover owner demotion and member-blocked role changes.

Depends on: issue 45.

### 49. Move organization embeddings to shared Supabase pgvector

Labels: `type:feature`, `area:ai-ml`, `area:backend`, `area:database`, `priority:p0`, `owner:shared`

Description:

Move document embeddings out of local laptop `vector_store` storage and into a shared Supabase `pgvector` table so every member of the same organization can chat with documents uploaded by any teammate.

Problem:

Right now document metadata and chunks are shared in Supabase, so teammates can see the same uploaded files in the Documents page. But embeddings used for chat retrieval are still stored locally on the backend machine that processed the upload. This means a document uploaded from one laptop may be visible to another teammate but not retrievable in chat from that teammate's local backend.

Acceptance criteria:

- Supabase has a shared vector table for document chunk embeddings.
- The vector table stores `organization_id`, `document_id`, `chunk_id`, `chunk_index`, embedding vector, and retrieval metadata.
- Upload/ingestion writes embeddings to the shared Supabase vector table instead of only local `vector_store`.
- Chat retrieval reads from the shared Supabase vector table scoped by `organization_id`.
- A document uploaded by one organization member can be used in chat by another member of the same organization.
- A document uploaded by one organization is not retrievable by users from another organization.
- Existing citation mapping still returns `document_id`, `chunk_id`, filename, page number when available, snippet, and score.
- Local Chroma/vector store usage is removed, disabled, or clearly kept only as an optional development fallback.
- Backend tests cover same-organization retrieval and cross-organization isolation.
- Manual test proves: user A uploads a document, user B joins the same organization, user B asks a question and gets cited answers from user A's document.

Depends on: issues 22, 30, 46, 47, and 48.

Recommended implementation order:

1. Issue 35.
2. Issue 36.
3. Issue 37.
4. Issue 39.
5. Issue 40.
6. Issue 41.
7. Issue 38.
8. Issue 42.
9. Issue 43.
10. Issue 44.
11. Issue 45.
12. Issue 46.
13. Issue 48.
14. Issue 47.
15. Issue 49.

## How To Add Your Friend As Collaborator

Friend's GitHub username: `workagrimag186-max`

GitHub UI steps:

1. Open `https://github.com/mitra9917/Averion.ai`.
2. Go to `Settings`.
3. Open `Collaborators and teams`.
4. Click `Add people`.
5. Enter `workagrimag186-max`.
6. Choose the permission level.
7. For this project, use `Write` access.

Recommended permission:

- Use `Write` access for your friend.
- Do not use `Admin` unless she needs to manage repository settings.

## How To Create Issues

GitHub UI steps:

1. Open the repo.
2. Go to `Issues`.
3. Click `New issue`.
4. Copy one issue title and description from this file.
5. Add the listed labels.
6. Add the listed milestone.
7. Assign the owner.
8. Create the issue.

Create all M0 issues first, then M1, then M2, and so on.

## Suggested GitHub Project Board Columns

Use a GitHub Projects board with these columns:

1. Backlog
2. Ready
3. In Progress
4. In Review
5. Done

Rules:

- Keep only one issue per person in `In Progress`.
- Every feature should be done through a pull request.
- Do not merge your own PR without the other person reviewing it.
- If an issue is unclear, discuss it in the issue comments before coding.
