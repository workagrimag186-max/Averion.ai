-- Issue 36: add Supabase Auth profile mapping fields to the Averion users table.
-- Run this in Supabase SQL Editor if your database was created before issue 36.

alter table users
  add column if not exists auth_user_id uuid,
  add column if not exists avatar_url text,
  add column if not exists job_title text;

create unique index if not exists users_auth_user_id_unique_idx
  on users (auth_user_id);
