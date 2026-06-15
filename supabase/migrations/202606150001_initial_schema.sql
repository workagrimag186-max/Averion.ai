-- Averion.ai core schema.
-- This migration is safe for both blank databases and environments that
-- already contain the original MVP tables.

create extension if not exists pgcrypto;

create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  email text not null,
  name text,
  role text not null default 'member',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint users_role_check check (role in ('owner', 'member')),
  constraint users_org_email_unique unique (organization_id, email)
);

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  uploaded_by_user_id uuid references public.users(id) on delete set null,
  filename text not null,
  file_type text not null,
  storage_path text not null,
  status text not null default 'uploaded',
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint documents_file_type_check check (file_type in ('pdf', 'txt', 'docx')),
  constraint documents_status_check check (
    status in ('uploaded', 'processing', 'ready', 'failed')
  )
);

create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  chunk_index integer not null,
  page_number integer,
  text text not null,
  token_count integer,
  embedding_id text,
  created_at timestamptz not null default now(),
  constraint document_chunks_text_not_empty check (length(trim(text)) > 0),
  constraint document_chunks_index_unique unique (document_id, chunk_index)
);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid references public.users(id) on delete set null,
  title text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  role text not null,
  content text not null,
  citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  constraint messages_role_check check (role in ('user', 'assistant', 'system')),
  constraint messages_content_not_empty check (length(trim(content)) > 0)
);

create table if not exists public.feedback (
  id uuid primary key default gen_random_uuid(),
  message_id uuid not null references public.messages(id) on delete cascade,
  user_id uuid references public.users(id) on delete set null,
  rating text not null,
  correction_text text,
  created_at timestamptz not null default now(),
  constraint feedback_rating_check check (rating in ('up', 'down'))
);

create index if not exists users_organization_email_idx
  on public.users (organization_id, email);
create index if not exists documents_organization_status_idx
  on public.documents (organization_id, status);
create index if not exists document_chunks_document_index_idx
  on public.document_chunks (document_id, chunk_index);
create index if not exists conversations_organization_user_idx
  on public.conversations (organization_id, user_id);
create index if not exists messages_conversation_created_at_idx
  on public.messages (conversation_id, created_at);
create index if not exists feedback_message_idx
  on public.feedback (message_id);
create index if not exists feedback_user_idx
  on public.feedback (user_id);
