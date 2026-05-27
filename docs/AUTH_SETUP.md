# Supabase Auth Setup

This guide covers issue 35: preparing Averion.ai for login, signup, Google signin, and account/profile work.

Supabase Auth should be used for authentication because Averion already uses Supabase Postgres for product data. Do not build password hashing, email verification, or OAuth flows manually.

## Auth Scope

Issue 35 only prepares configuration and documentation. Later issues implement the pages, protected routes, backend validation, and profile updates.

Planned auth features:

- Email/password signup.
- Email/password signin.
- Supabase email verification.
- Google signin for Gmail/Google users.
- Optional Gmail-only domain allowlist.
- Protected app routes.
- Logout.
- Account/profile page.
- Backend user and organization context.

## Step 1: Enable Email Auth

1. Open your Supabase project.
2. Go to `Authentication`.
3. Open `Providers`.
4. Enable `Email`.
5. Keep password signup enabled for the MVP.
6. Decide whether email confirmations are required.

Recommended MVP choice:

- Enable email confirmations if you want a more realistic SaaS flow.
- Disable email confirmations only if you need faster local testing.

Document your choice in the issue or pull request.

## Step 2: Configure Auth URLs

In Supabase, open `Authentication` -> `URL Configuration`.

For local development, add:

```text
http://localhost:3000
```

For redirect/callback URLs, add:

```text
http://localhost:3000/auth/callback
```

When the app is deployed later, add the deployed frontend URL too.

## Step 3: Get Frontend Auth Values

Open `Project Settings` -> `API`.

Copy these values into `apps/web/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=your_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_public_key
NEXT_PUBLIC_AUTH_REDIRECT_URL=http://localhost:3000/auth/callback
```

These values are safe to expose to the browser, but they should still be kept in local env files instead of hardcoded in components.

## Step 4: Get Backend Auth Values

Open `Project Settings` -> `API` -> `JWT Settings`.

Copy the JWT secret into `apps/api/.env`:

```env
SUPABASE_URL=your_project_url
SUPABASE_JWT_SECRET=your_jwt_secret
AUTH_REQUIRED=false
```

The JWT secret must stay server-side only. Never put it in `apps/web/.env.local`, frontend code, screenshots, GitHub issues, or pull request descriptions.

`AUTH_REQUIRED=false` keeps local development forgiving while you are wiring the
frontend and backend together. When set to `true`, FastAPI rejects requests that
do not include a valid Supabase bearer token.

## Step 5: Apply Profile Mapping Migration

If your Supabase database was created before issue 36, run [supabase_auth_profile_migration.sql](supabase_auth_profile_migration.sql) in the Supabase SQL Editor.

This adds profile mapping fields to the existing `users` table:

```text
auth_user_id
avatar_url
job_title
```

`auth_user_id` links a Supabase Auth identity to Averion's product profile. Passwords and OAuth identities stay inside Supabase Auth; Averion stores only product profile and organization membership data.

## Step 6: Optional Gmail-Only Validation

For the MVP, the recommended default is to allow any valid email address and add Google signin for Gmail/Google users.

If the product must allow only Gmail accounts later, set:

```env
NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS=gmail.com,googlemail.com
ALLOWED_EMAIL_DOMAINS=gmail.com,googlemail.com
```

The frontend value gives users quick validation feedback. The backend value is the real enforcement point and must be checked before trusting account access.

## Step 7: Configure Google Signin

Issue 38 adds the "Continue with Google" button to the login and signup pages. Supabase still needs dashboard configuration before the button can complete the OAuth flow.

### In Supabase

1. Open your Supabase project.
2. Go to `Authentication` -> `Providers`.
3. Open `Google`.
4. Enable the Google provider.
5. Paste your Google OAuth client id.
6. Paste your Google OAuth client secret.
7. Save the provider settings.

Copy the callback URL shown by Supabase in the Google provider screen. You need it in Google Cloud.

### In Google Cloud

1. Open Google Cloud Console.
2. Create or select a project.
3. Configure the OAuth consent screen.
4. Create an OAuth client id for a web application.
5. Add this authorized JavaScript origin:

```text
http://localhost:3000
```

6. Add the Supabase callback URL as an authorized redirect URI.
7. Copy the client id and client secret back into Supabase.

For production, also add your deployed frontend URL as an authorized origin and make sure Supabase has the deployed redirect URL.

Do not add Google secrets to Git.

If `NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS` is set, the auth callback signs out Google users whose email domain is not allowed.

## Local Env Files

Create local env files from the examples:

```bash
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
```

Then fill in only your local files.

Tracked example files:

- `apps/web/.env.example`
- `apps/api/.env.example`

Ignored real files:

- `apps/web/.env.local`
- `apps/api/.env`

## Issue 35 Completion Checklist

Before closing issue 35:

- Email auth provider is enabled in Supabase.
- Email confirmation choice is documented.
- Local callback URL is configured in Supabase.
- `apps/web/.env.example` lists public auth variables.
- `apps/api/.env.example` lists server auth variables.
- Real `.env` files are not shown in `git status`.
- No Supabase secrets are committed.
