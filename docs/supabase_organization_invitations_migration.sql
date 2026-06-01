-- Issue 47: add organization invitation records.
-- Run this in Supabase SQL Editor before using invite/accept flows.

create table if not exists organization_invitations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  invited_email text not null,
  invited_by_user_id uuid not null references users(id) on delete cascade,
  status text not null default 'pending',
  expires_at timestamptz not null,
  accepted_at timestamptz,
  accepted_by_user_id uuid references users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organization_invitations_status_check check (
    status in ('pending', 'accepted', 'revoked', 'expired')
  )
);

create unique index if not exists organization_invitations_pending_email_idx
  on organization_invitations (organization_id, invited_email)
  where status = 'pending';

create index if not exists organization_invitations_email_status_idx
  on organization_invitations (invited_email, status);
