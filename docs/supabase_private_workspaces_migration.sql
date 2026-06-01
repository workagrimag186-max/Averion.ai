-- Issue 46: move existing authenticated development users into private workspaces.
-- Run this only if multiple real test accounts were created in the shared
-- Development Organization before Issue 46 was merged.

begin;

create extension if not exists pgcrypto;

create temp table user_private_workspace_map as
select
  users.id as user_id,
  gen_random_uuid() as organization_id,
  concat(
    coalesce(nullif(trim(users.name), ''), split_part(users.email, '@', 1), 'Averion'),
    '''s Workspace'
  ) as organization_name
from users
where users.organization_id = '00000000-0000-0000-0000-000000000001'::uuid
  and users.auth_user_id is not null;

insert into organizations (id, name)
select
  organization_id,
  organization_name
from user_private_workspace_map;

update documents
set
  organization_id = user_private_workspace_map.organization_id,
  updated_at = now()
from user_private_workspace_map
where documents.uploaded_by_user_id = user_private_workspace_map.user_id
  and documents.organization_id = '00000000-0000-0000-0000-000000000001'::uuid;

update conversations
set
  organization_id = user_private_workspace_map.organization_id,
  updated_at = now()
from user_private_workspace_map
where conversations.user_id = user_private_workspace_map.user_id
  and conversations.organization_id = '00000000-0000-0000-0000-000000000001'::uuid;

update users
set
  organization_id = user_private_workspace_map.organization_id,
  role = 'owner',
  updated_at = now()
from user_private_workspace_map
where users.id = user_private_workspace_map.user_id;

commit;
