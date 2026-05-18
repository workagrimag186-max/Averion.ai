-- Verify that the Averion.ai MVP Supabase schema has been applied.

select 'organizations' as table_name, to_regclass('public.organizations') is not null as exists
union all
select 'users', to_regclass('public.users') is not null
union all
select 'documents', to_regclass('public.documents') is not null
union all
select 'document_chunks', to_regclass('public.document_chunks') is not null
union all
select 'conversations', to_regclass('public.conversations') is not null
union all
select 'messages', to_regclass('public.messages') is not null
union all
select 'feedback', to_regclass('public.feedback') is not null
order by table_name;
