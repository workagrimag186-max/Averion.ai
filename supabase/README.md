# Averion Database Migrations

The files in `migrations/` are the only supported schema source of truth. Apply
them in filename order. Every automatic migration is safe to run again.

## Fresh Supabase project

With the Supabase CLI:

```bash
supabase link --project-ref <project-ref>
supabase db push
```

With a direct PostgreSQL connection:

```bash
for migration in supabase/migrations/*.sql; do
  psql "$DATABASE_URL" --set ON_ERROR_STOP=1 --file "$migration"
done

psql "$DATABASE_URL" --set ON_ERROR_STOP=1 \
  --file supabase/tests/verify_schema.sql
```

## Existing development database

1. Back up the database.
2. Check for cross-organization references:

   ```sql
   select d.id
   from public.documents d
   join public.users u on u.id = d.uploaded_by_user_id
   where d.organization_id <> u.organization_id;

   select c.id
   from public.conversations c
   join public.users u on u.id = c.user_id
   where c.organization_id <> u.organization_id;

   select e.id
   from public.document_embeddings e
   join public.documents d on d.id = e.document_id
   where e.organization_id <> d.organization_id;
   ```

3. Correct any rows returned by those queries.
4. Apply all files in `migrations/` in filename order.
5. Run `tests/verify_schema.sql`.

If multiple authenticated users still share the original development
organization, run `legacy/202606150900_private_workspace_conversion.sql`
manually after the numbered migrations. It is intentionally excluded from
normal deployments.

## Access model

All application tables are server-only:

- The browser uses Supabase Auth but does not query application tables through
  PostgREST.
- RLS is enabled on every application table.
- `anon` and `authenticated` have no table privileges or policies.
- FastAPI uses a private PostgreSQL connection and organization-scoped queries.
- Composite foreign keys prevent cross-organization references.
- The private `documents` Storage bucket uses organization-scoped object keys.
- Authenticated users can read and upload only inside their organization prefix.
- Only organization owners can update or delete objects through Storage APIs.
- FastAPI uses the service-role credential for coordinated object/database work.

Never expose `DATABASE_URL` or a service-role credential to the browser.
