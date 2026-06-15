\set ON_ERROR_STOP on

do $$
declare
  missing_tables text;
  missing_indexes text;
  missing_constraints text;
  tables_without_rls text;
  browser_grants text;
begin
  if not exists (
    select 1 from pg_extension where extname = 'vector'
  ) then
    raise exception 'pgvector extension is missing';
  end if;

  select string_agg(required_table, ', ' order by required_table)
  into missing_tables
  from unnest(array[
    'organizations',
    'users',
    'documents',
    'document_chunks',
    'document_embeddings',
    'conversations',
    'messages',
    'feedback',
    'organization_invitations'
  ]) required_table
  where to_regclass('public.' || required_table) is null;

  if missing_tables is not null then
    raise exception 'Missing tables: %', missing_tables;
  end if;

  select string_agg(required_index, ', ' order by required_index)
  into missing_indexes
  from unnest(array[
    'users_organization_email_idx',
    'users_auth_user_id_unique_idx',
    'documents_organization_status_idx',
    'document_chunks_document_index_idx',
    'document_embeddings_organization_idx',
    'document_embeddings_document_idx',
    'document_embeddings_vector_idx',
    'conversations_organization_user_idx',
    'messages_conversation_created_at_idx',
    'organization_invitations_pending_email_idx',
    'organization_invitations_email_status_idx'
  ]) required_index
  where to_regclass('public.' || required_index) is null;

  if missing_indexes is not null then
    raise exception 'Missing indexes: %', missing_indexes;
  end if;

  select string_agg(required_constraint, ', ' order by required_constraint)
  into missing_constraints
  from unnest(array[
    'users_role_check',
    'users_language_preference_check',
    'documents_file_type_check',
    'documents_status_check',
    'documents_uploader_organization_fk',
    'conversations_user_organization_fk',
    'invitations_inviter_organization_fk',
    'invitations_acceptor_organization_fk',
    'document_embeddings_document_organization_fk'
  ]) required_constraint
  where not exists (
    select 1 from pg_constraint where conname = required_constraint
  );

  if missing_constraints is not null then
    raise exception 'Missing constraints: %', missing_constraints;
  end if;

  select string_agg(c.relname, ', ' order by c.relname)
  into tables_without_rls
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname = any(array[
      'organizations',
      'users',
      'documents',
      'document_chunks',
      'document_embeddings',
      'conversations',
      'messages',
      'feedback',
      'organization_invitations'
    ])
    and not c.relrowsecurity;

  if tables_without_rls is not null then
    raise exception 'RLS is disabled on: %', tables_without_rls;
  end if;

  select string_agg(
    grantee || ':' || table_name || ':' || privilege_type,
    ', ' order by grantee, table_name, privilege_type
  )
  into browser_grants
  from information_schema.role_table_grants
  where table_schema = 'public'
    and grantee in ('anon', 'authenticated')
    and table_name = any(array[
      'organizations',
      'users',
      'documents',
      'document_chunks',
      'document_embeddings',
      'conversations',
      'messages',
      'feedback',
      'organization_invitations'
    ]);

  if browser_grants is not null then
    raise exception 'Browser roles retain table grants: %', browser_grants;
  end if;
end
$$;

select 'Averion schema verification passed' as result;

begin;

insert into public.organizations (id, name)
values
  ('00000000-0000-0000-0000-00000000a001', 'Migration Test A'),
  ('00000000-0000-0000-0000-00000000b001', 'Migration Test B');

insert into public.users (id, organization_id, email, role)
values
  (
    '00000000-0000-0000-0000-00000000a002',
    '00000000-0000-0000-0000-00000000a001',
    'migration-test-a@example.com',
    'owner'
  ),
  (
    '00000000-0000-0000-0000-00000000b002',
    '00000000-0000-0000-0000-00000000b001',
    'migration-test-b@example.com',
    'owner'
  );

do $$
begin
  begin
    insert into public.documents (
      organization_id,
      uploaded_by_user_id,
      filename,
      file_type,
      storage_path
    )
    values (
      '00000000-0000-0000-0000-00000000a001',
      '00000000-0000-0000-0000-00000000b002',
      'cross-tenant.txt',
      'txt',
      'migration-test/cross-tenant.txt'
    );

    raise exception 'Cross-organization document upload was accepted';
  exception
    when foreign_key_violation then null;
  end;

  begin
    insert into public.conversations (organization_id, user_id, title)
    values (
      '00000000-0000-0000-0000-00000000a001',
      '00000000-0000-0000-0000-00000000b002',
      'Cross-tenant conversation'
    );

    raise exception 'Cross-organization conversation was accepted';
  exception
    when foreign_key_violation then null;
  end;
end
$$;

rollback;

select 'Averion tenancy behavior verification passed' as result;
