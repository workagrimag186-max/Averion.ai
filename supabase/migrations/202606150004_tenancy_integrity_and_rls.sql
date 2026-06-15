-- Enforce organization consistency and make application tables server-only.
--
-- The FastAPI service connects directly to PostgreSQL with a server database
-- role. Browser clients use Supabase only for authentication and must not query
-- these tables through PostgREST.

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.users'::regclass
      and conname = 'users_id_organization_unique'
  ) then
    alter table public.users
      add constraint users_id_organization_unique unique (id, organization_id);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.documents'::regclass
      and conname = 'documents_id_organization_unique'
  ) then
    alter table public.documents
      add constraint documents_id_organization_unique unique (id, organization_id);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.documents'::regclass
      and conname = 'documents_uploader_organization_fk'
  ) then
    alter table public.documents
      add constraint documents_uploader_organization_fk
      foreign key (uploaded_by_user_id, organization_id)
      references public.users (id, organization_id)
      on delete set null (uploaded_by_user_id)
      deferrable initially immediate;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.conversations'::regclass
      and conname = 'conversations_user_organization_fk'
  ) then
    alter table public.conversations
      add constraint conversations_user_organization_fk
      foreign key (user_id, organization_id)
      references public.users (id, organization_id)
      on delete set null (user_id)
      deferrable initially immediate;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.organization_invitations'::regclass
      and conname = 'invitations_inviter_organization_fk'
  ) then
    alter table public.organization_invitations
      add constraint invitations_inviter_organization_fk
      foreign key (invited_by_user_id, organization_id)
      references public.users (id, organization_id)
      on delete cascade
      deferrable initially immediate;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.organization_invitations'::regclass
      and conname = 'invitations_acceptor_organization_fk'
  ) then
    alter table public.organization_invitations
      add constraint invitations_acceptor_organization_fk
      foreign key (accepted_by_user_id, organization_id)
      references public.users (id, organization_id)
      on delete set null (accepted_by_user_id)
      deferrable initially immediate;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.document_embeddings'::regclass
      and conname = 'document_embeddings_document_organization_fk'
  ) then
    alter table public.document_embeddings
      add constraint document_embeddings_document_organization_fk
      foreign key (document_id, organization_id)
      references public.documents (id, organization_id)
      on delete cascade
      deferrable initially immediate;
  end if;
end
$$;

alter table public.organizations enable row level security;
alter table public.users enable row level security;
alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.document_embeddings enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.feedback enable row level security;
alter table public.organization_invitations enable row level security;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    revoke all on table
      public.organizations,
      public.users,
      public.documents,
      public.document_chunks,
      public.document_embeddings,
      public.conversations,
      public.messages,
      public.feedback,
      public.organization_invitations
    from anon;
  end if;

  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    revoke all on table
      public.organizations,
      public.users,
      public.documents,
      public.document_chunks,
      public.document_embeddings,
      public.conversations,
      public.messages,
      public.feedback,
      public.organization_invitations
    from authenticated;
  end if;
end
$$;
