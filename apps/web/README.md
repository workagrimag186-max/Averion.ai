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
```

This points the frontend to the backend API. During local development, the default is:

```text
http://127.0.0.1:8000
```

## Current Routes

- `/` - product overview placeholder
- `/documents` - document upload workspace
- `/chat` - chat area placeholder

## Upload Flow

The documents page calls the backend upload endpoint:

```text
POST /documents/upload
```

Set the backend URL in `.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```
