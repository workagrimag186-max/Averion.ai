-- Durable PostgreSQL-backed document ingestion queue.

create table if not exists public.document_ingestion_jobs (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null,
  organization_id uuid not null,
  status text not null default 'queued',
  attempts integer not null default 0,
  max_attempts integer not null default 3,
  available_at timestamptz not null default now(),
  locked_at timestamptz,
  locked_by text,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  constraint document_ingestion_jobs_status_check check (
    status in ('queued', 'processing', 'completed', 'failed')
  ),
  constraint document_ingestion_jobs_attempts_check check (
    attempts >= 0 and max_attempts between 1 and 10
  ),
  constraint document_ingestion_jobs_document_unique unique (document_id),
  constraint document_ingestion_jobs_document_organization_fk
    foreign key (document_id, organization_id)
    references public.documents (id, organization_id)
    on delete cascade
);

create index if not exists document_ingestion_jobs_claim_idx
  on public.document_ingestion_jobs (status, available_at, created_at);

create index if not exists document_ingestion_jobs_organization_idx
  on public.document_ingestion_jobs (organization_id, status);

alter table public.document_ingestion_jobs enable row level security;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    revoke all on table public.document_ingestion_jobs from anon;
  end if;

  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    revoke all on table public.document_ingestion_jobs from authenticated;
  end if;
end
$$;
