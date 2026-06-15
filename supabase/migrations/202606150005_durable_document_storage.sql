-- Durable, organization-scoped document object storage.
--
-- Supabase projects include the storage schema. Plain PostgreSQL CI does not,
-- so bucket and policy creation is conditional while the document key
-- constraint is verified in every environment.

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.documents'::regclass
      and conname = 'documents_storage_object_key_check'
  ) then
    alter table public.documents
      add constraint documents_storage_object_key_check
      check (
        storage_path =
          'organizations/' || organization_id::text ||
          '/documents/' || id::text || '/' || filename
      )
      not valid;
  end if;
end
$$;

do $$
begin
  if to_regclass('storage.buckets') is not null then
    insert into storage.buckets (
      id,
      name,
      public,
      file_size_limit,
      allowed_mime_types
    )
    values (
      'documents',
      'documents',
      false,
      104857600,
      array[
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ]
    )
    on conflict (id) do update set
      public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;
  end if;
end
$$;

do $$
begin
  if to_regclass('storage.objects') is null
    or to_regnamespace('auth') is null
    or not exists (select 1 from pg_roles where rolname = 'authenticated')
  then
    return;
  end if;

  execute '
    create or replace function public.current_storage_organization_id()
    returns uuid
    language sql
    stable
    security definer
    set search_path = public, pg_temp
    as $function$
      select organization_id
      from public.users
      where auth_user_id = auth.uid()
      limit 1
    $function$
  ';

  execute '
    create or replace function public.current_storage_user_role()
    returns text
    language sql
    stable
    security definer
    set search_path = public, pg_temp
    as $function$
      select role
      from public.users
      where auth_user_id = auth.uid()
      limit 1
    $function$
  ';

  revoke all on function public.current_storage_organization_id() from public;
  revoke all on function public.current_storage_user_role() from public;
  grant execute on function public.current_storage_organization_id()
    to authenticated;
  grant execute on function public.current_storage_user_role()
    to authenticated;

  execute 'drop policy if exists documents_read_same_organization on storage.objects';
  execute 'drop policy if exists documents_insert_same_organization on storage.objects';
  execute 'drop policy if exists documents_update_owner_only on storage.objects';
  execute 'drop policy if exists documents_delete_owner_only on storage.objects';

  execute $policy$
    create policy documents_read_same_organization
    on storage.objects
    for select
    to authenticated
    using (
      bucket_id = 'documents'
      and (storage.foldername(name))[1] = 'organizations'
      and (storage.foldername(name))[2] =
        public.current_storage_organization_id()::text
    )
  $policy$;

  execute $policy$
    create policy documents_insert_same_organization
    on storage.objects
    for insert
    to authenticated
    with check (
      bucket_id = 'documents'
      and (storage.foldername(name))[1] = 'organizations'
      and (storage.foldername(name))[2] =
        public.current_storage_organization_id()::text
    )
  $policy$;

  execute $policy$
    create policy documents_update_owner_only
    on storage.objects
    for update
    to authenticated
    using (
      bucket_id = 'documents'
      and (storage.foldername(name))[1] = 'organizations'
      and (storage.foldername(name))[2] =
        public.current_storage_organization_id()::text
      and public.current_storage_user_role() = 'owner'
    )
    with check (
      bucket_id = 'documents'
      and (storage.foldername(name))[1] = 'organizations'
      and (storage.foldername(name))[2] =
        public.current_storage_organization_id()::text
      and public.current_storage_user_role() = 'owner'
    )
  $policy$;

  execute $policy$
    create policy documents_delete_owner_only
    on storage.objects
    for delete
    to authenticated
    using (
      bucket_id = 'documents'
      and (storage.foldername(name))[1] = 'organizations'
      and (storage.foldername(name))[2] =
        public.current_storage_organization_id()::text
      and public.current_storage_user_role() = 'owner'
    )
  $policy$;
end
$$;
