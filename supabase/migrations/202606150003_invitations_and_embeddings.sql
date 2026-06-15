-- Organization invitations and shared pgvector embeddings.

create extension if not exists vector;

create table if not exists public.organization_invitations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  invited_email text not null,
  invited_by_user_id uuid not null references public.users(id) on delete cascade,
  status text not null default 'pending',
  expires_at timestamptz not null,
  accepted_at timestamptz,
  accepted_by_user_id uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organization_invitations_status_check check (
    status in ('pending', 'accepted', 'revoked', 'expired')
  )
);

create table if not exists public.document_embeddings (
  id uuid primary key default gen_random_uuid(),
  chunk_id text not null unique,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  chunk_index integer not null,
  page_number integer,
  text text not null,
  embedding vector(384) not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint document_embeddings_text_not_empty check (length(trim(text)) > 0),
  constraint document_embeddings_document_chunk_unique unique (document_id, chunk_index)
);

create unique index if not exists organization_invitations_pending_email_idx
  on public.organization_invitations (organization_id, invited_email)
  where status = 'pending';
create index if not exists organization_invitations_email_status_idx
  on public.organization_invitations (invited_email, status);
create index if not exists document_embeddings_organization_idx
  on public.document_embeddings (organization_id);
create index if not exists document_embeddings_document_idx
  on public.document_embeddings (document_id, chunk_index);
create index if not exists document_embeddings_vector_idx
  on public.document_embeddings
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
