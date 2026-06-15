# Supabase Setup

This guide covers S1: creating the Supabase project and applying the Averion.ai MVP schema.
For login, signup, Google signin, and account setup, use [Supabase Auth Setup](AUTH_SETUP.md).

Supabase is used as the PostgreSQL database for structured product data:

- organizations
- users
- documents
- document_chunks
- document_embeddings
- conversations
- messages
- feedback

Supabase also stores shared pgvector embeddings so every member of the same organization can retrieve the same uploaded documents in chat.

## What Connects To What

```text
Frontend upload UI
  -> FastAPI backend
  -> Supabase Postgres for metadata, chunks, and pgvector embeddings
```

The frontend should not receive the database password. Only the FastAPI backend uses `DATABASE_URL`.

## Step 1: Create A Supabase Project

1. Open [Supabase](https://supabase.com).
2. Sign in or create an account.
3. Click `New project`.
4. Choose your organization.
5. Use a clear project name:

```text
averion-ai
```

6. Choose a database password and store it safely.
7. Choose the closest region.
8. Create the project.

Do not commit the database password or connection string to GitHub.

## Step 2: Get The Database Connection String

1. Open the Supabase project dashboard.
2. Click `Connect`.
3. Copy a Postgres connection string.

For local FastAPI development, prefer:

- Direct connection if your network supports IPv6.
- Session pooler if direct connection fails because of IPv6/network issues.

Save it locally in:

```text
apps/api/.env
```

Example:

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres
```

If you use a pooler URL, paste that instead. Keep it in `.env` only.

## Step 3: Apply The Schema

Apply the numbered files in `supabase/migrations/` in filename order. Use
`supabase db push` or the direct `psql` commands documented in
[supabase/README.md](../supabase/README.md).

Expected tables:

```text
organizations
users
documents
document_chunks
document_embeddings
conversations
messages
feedback
organization_invitations
```

## Step 4: Verify The Tables

Run [supabase/tests/verify_schema.sql](../supabase/tests/verify_schema.sql).

Expected result:

- `Averion schema verification passed`
- `Averion tenancy behavior verification passed`

You can also check in the Supabase Table Editor that all nine tables are visible.

Existing databases use the same ordered chain. Complete the backup and
consistency checks in [supabase/README.md](../supabase/README.md) first.
Documents uploaded before shared pgvector storage should be re-uploaded so
their embeddings exist in `document_embeddings`.

## Step 5: Create Local Env File

From the repo root:

```bash
cp apps/api/.env.example apps/api/.env
```

Then edit:

```text
apps/api/.env
```

Set:

```env
DATABASE_URL=your_supabase_postgres_connection_string
DEFAULT_ORGANIZATION_ID=00000000-0000-0000-0000-000000000001
```

Never commit `apps/api/.env`.

Until real auth exists, requests use `DEFAULT_ORGANIZATION_ID` through
`app.core.organization.get_current_organization_id()`. The backend creates a
temporary `Development Organization` row automatically when it stores document
metadata. Documents, conversations, and vector retrieval are scoped through this
temporary organization path so it can be replaced cleanly by real auth later.

When `DATABASE_URL` is configured, uploaded documents also run through the
extraction, cleaning, and chunking pipeline. Produced chunks are stored in the
`document_chunks` table, embeddings are stored in the shared
`document_embeddings` pgvector table, and the document status is updated to
`ready`. If no readable chunks are produced, the document is marked `failed`.

## Safety Checklist

Before closing S1:

- Supabase project exists.
- All files in `supabase/migrations/` have been applied in order.
- `supabase/tests/verify_schema.sql` passes.
- `apps/api/.env` contains `DATABASE_URL` locally.
- `git status` does not show `apps/api/.env`.
- No passwords or Supabase secrets are in committed files.

## Troubleshooting

If the direct connection does not work, use the Supabase pooler connection string from the `Connect` page.

If a migration fails, stop rather than manually altering production. Restore
the backup if needed, correct inconsistent data, and rerun the ordered chain.

If you accidentally paste a secret into a tracked file, do not commit it. Remove it immediately and ask for help before pushing.
