-- Issue 49: shared organization-scoped vector storage for RAG retrieval.
-- Run this in Supabase SQL Editor before testing organization-wide chat.

create extension if not exists vector;

create table if not exists document_embeddings (
  id uuid primary key default gen_random_uuid(),
  chunk_id text not null unique,
  organization_id uuid not null references organizations(id) on delete cascade,
  document_id uuid not null references documents(id) on delete cascade,
  chunk_index int not null,
  page_number int,
  text text not null,
  embedding vector(384) not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint document_embeddings_text_not_empty check (length(trim(text)) > 0),
  constraint document_embeddings_document_chunk_unique unique (document_id, chunk_index)
);

create index if not exists document_embeddings_organization_idx
  on document_embeddings (organization_id);

create index if not exists document_embeddings_document_idx
  on document_embeddings (document_id, chunk_index);

create index if not exists document_embeddings_vector_idx
  on document_embeddings
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
