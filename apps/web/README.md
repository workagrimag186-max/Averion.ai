# Web App

This folder will contain the Next.js frontend for Averion.ai.

Planned responsibilities:

- Document upload UI.
- Document list and processing status.
- Chat interface.
- Citation/source panel.
- Feedback controls.

## Local Commands

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

## Environment Variables

Copy the example file before running the app locally:

```bash
cp .env.example .env.local
```

Current variables:

```text
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_AUTH_REDIRECT_URL
NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS
```

`NEXT_PUBLIC_API_BASE_URL` points the frontend to the backend API. During local development, the default is:

```text
http://127.0.0.1:8000
```

The Supabase variables are prepared for the upcoming auth issues. Fill them in from the Supabase dashboard when working on login/signup. See [Supabase Auth Setup](../../docs/AUTH_SETUP.md).

## Current Routes

- `/` - product overview placeholder
- `/documents` - document upload workspace
- `/chat` - chat area placeholder
- `/login` - email/password sign in
- `/signup` - email/password account creation
- `/auth/callback` - Supabase auth redirect handler

## Upload Flow

The documents page calls the backend upload endpoint:

```text
POST /documents/upload
```

Set the backend URL in `.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```
