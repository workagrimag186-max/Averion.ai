-- OPTIONAL LEGACY DATA MIGRATION
--
-- Run this manually only when upgrading an old development database where
-- multiple authenticated users still share the original default organization.
-- It is intentionally outside supabase/migrations so fresh and normal upgrade
-- deployments never execute it automatically.

begin;

create extension if not exists pgcrypto;

set constraints all deferred;

create temp table user_private_workspace_map on commit drop as
select
  users.id as user_id,
  gen_random_uuid() as organization_id,
  concat(
    coalesce(nullif(trim(users.name), ''), split_part(users.email, '@', 1), 'Averion'),
    '''s Workspace'
  ) as organization_name
from public.users
where users.organization_id = '00000000-0000-0000-0000-000000000001'::uuid
  and users.auth_user_id is not null;

insert into public.organizations (id, name)
select organization_id, organization_name
from user_private_workspace_map
on conflict (id) do nothing;

update public.documents
set
  organization_id = user_private_workspace_map.organization_id,
  updated_at = now()
from user_private_workspace_map
where documents.uploaded_by_user_id = user_private_workspace_map.user_id
  and documents.organization_id = '00000000-0000-0000-0000-000000000001'::uuid;

update public.document_embeddings
set
  organization_id = user_private_workspace_map.organization_id,
  updated_at = now()
from user_private_workspace_map
where document_embeddings.document_id in (
  select documents.id
  from public.documents
  where documents.uploaded_by_user_id = user_private_workspace_map.user_id
);

update public.conversations
set
  organization_id = user_private_workspace_map.organization_id,
  updated_at = now()
from user_private_workspace_map
where conversations.user_id = user_private_workspace_map.user_id
  and conversations.organization_id = '00000000-0000-0000-0000-000000000001'::uuid;

update public.users
set
  organization_id = user_private_workspace_map.organization_id,
  role = 'owner',
  updated_at = now()
from user_private_workspace_map
where users.id = user_private_workspace_map.user_id;

commit;
