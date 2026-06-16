-- Harden organization invitation and tenant ownership constraints.
--
-- The API performs owner checks before calling these paths, but deployment
-- safety depends on the database also preserving tenant boundaries when writes
-- happen in a transaction.

do $$
begin
  if exists (
    select 1
    from pg_constraint
    where conrelid = 'public.organization_invitations'::regclass
      and conname = 'invitations_acceptor_organization_fk'
  ) then
    alter table public.organization_invitations
      alter constraint invitations_acceptor_organization_fk
      deferrable initially deferred;
  end if;
end
$$;

create index if not exists users_organization_role_idx
  on public.users (organization_id, role);
