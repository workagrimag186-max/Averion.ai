# Auth Manual Test Checklist

Use this checklist after issues 35 through 43 are merged. It verifies that Supabase Auth, the frontend session, and the FastAPI authenticated data flow work together.

Do not paste real secrets into GitHub issues, pull requests, screenshots, or committed files.

## Before Testing

1. Pull the latest `main` branch.
2. Confirm local env files exist:

```bash
test -f apps/web/.env.local
test -f apps/api/.env
```

3. Confirm real env files are ignored by Git:

```bash
git status --short apps/web/.env.local apps/api/.env
```

Expected result: no output.

4. Start the backend:

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload
```

5. Start the frontend in a second terminal:

```bash
cd apps/web
npm run dev
```

6. Open:

```text
http://localhost:3000
```

## Signup

1. Open `http://localhost:3000/signup`.
2. Enter a valid name, email, password, and matching confirm password.
3. Submit the form.
4. If email confirmation is enabled, open the confirmation email and complete the callback.
5. Confirm Supabase `Authentication` shows the new user.
6. Confirm the app can open protected pages after signin.

Pass condition:

- The user can create an account without app errors.
- The callback lands back in the app.
- No real secrets appear in browser-visible errors.

## Login

1. Open `http://localhost:3000/login`.
2. Enter the verified email and password.
3. Submit the form.
4. Confirm the app redirects to the requested protected route or `/`.

Pass condition:

- `/`, `/documents`, `/chat`, and `/account` load after login.
- Logged-out users are redirected to `/login`.

## Google Signin

1. Confirm Google provider is enabled in Supabase.
2. Confirm Google Cloud has `http://localhost:3000` as an authorized JavaScript origin.
3. Confirm Google Cloud has the Supabase callback URL as an authorized redirect URI.
4. Open `http://localhost:3000/login`.
5. Click `Continue with Google`.
6. Complete the Google flow.

Pass condition:

- The Google user returns to `/auth/callback`.
- The app opens a protected route.
- Supabase `Authentication` shows the Google identity.

## Account And Logout

1. Open `/account`.
2. Confirm email, role, organization, and user id are visible.
3. Update display name.
4. Update job title.
5. Save the profile.
6. Refresh the page.
7. Click `Logout`.

Pass condition:

- Display name and job title persist after refresh.
- Email remains read-only.
- Logout returns the user to `/login`.
- Protected pages redirect to `/login` after logout.

## Upload

1. Sign in.
2. Open `/documents`.
3. Upload a small `.txt` file.
4. Upload a small `.pdf` file.
5. Click refresh in the uploaded documents list.
6. In Supabase Table Editor, check `documents`.

Pass condition:

- Upload succeeds.
- The document row uses the logged-in user's `uploaded_by_user_id`.
- The document row uses the user's `organization_id`.
- Real `.env` files remain untracked.

## Chat

1. Sign in.
2. Upload a document that reaches `ready`.
3. Open `/chat`.
4. Ask a question about the uploaded document.
5. In Supabase Table Editor, check `conversations` and `messages`.

Pass condition:

- A conversation row is created.
- The conversation row stores the authenticated `user_id`.
- The conversation row stores the authenticated `organization_id`.
- Assistant messages include citations when retrieval returns sources.

## Feedback

1. After a chat answer appears, click `Good` or `Needs correction`.
2. If using correction feedback, enter a short correction.
3. In Supabase Table Editor, check `feedback`.

Pass condition:

- Feedback row is created.
- Feedback row stores the authenticated `user_id`.
- Feedback is linked to an assistant message from the current organization.

## Expected Automated Checks

Run these before opening or merging auth PRs:

```bash
cd apps/api
source .venv/bin/activate
pytest tests
```

```bash
cd apps/web
npm run lint
npm run typecheck
npm run build
```

The tests use fake JWT secrets and fake tokens. They do not require real Supabase secrets.
