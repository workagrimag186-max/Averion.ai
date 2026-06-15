-- Supabase Auth profile mapping and user language preferences.

alter table public.users
  add column if not exists auth_user_id uuid,
  add column if not exists avatar_url text,
  add column if not exists job_title text,
  add column if not exists language_preference text not null default 'en';

create unique index if not exists users_auth_user_id_unique_idx
  on public.users (auth_user_id);

create index if not exists users_language_preference_idx
  on public.users (language_preference);

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.users'::regclass
      and conname = 'users_language_preference_check'
  ) then
    alter table public.users
      add constraint users_language_preference_check
      check (language_preference in ('en', 'hi', 'es', 'fr', 'de', 'ja'));
  end if;
end
$$;

comment on column public.users.language_preference is
  'Preferred UI, chatbot, and voice language: en, hi, es, fr, de, or ja.';
