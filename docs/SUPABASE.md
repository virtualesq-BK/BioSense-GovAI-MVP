# Supabase Setup

BioSense-GovAI uses **Supabase** for:

- **PostgreSQL + pgvector** — relational data, embeddings, RAG
- **Auth** — email/password login, JWT for FastAPI

## 1. Create a Supabase project

1. [supabase.com/dashboard](https://supabase.com/dashboard) → New project
2. Note your **Project URL** and **anon key**

## 2. Enable pgvector

In **SQL Editor**, run migrations from `infra/db/migrations/postgres/` in order (`001` … `006`).

Or run at minimum:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then apply all migration files.

## 3. Configure `.env`

```bash
# Database (Session pooler URI from Supabase → Database → Connect)
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres

# API (Project Settings → API)
SUPABASE_URL=https://[ref].supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=...

# Next.js (same URL + anon key)
NEXT_PUBLIC_SUPABASE_URL=https://[ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

`DATABASE_URL` accepts `postgresql://` or `postgres://`; the API converts it for asyncpg automatically.

## 4. Auth redirect URLs

In **Authentication → URL Configuration**, add:

- Site URL: `http://localhost:3000`
- Redirect URLs: `http://localhost:3000/auth/callback`

## 5. Local Postgres (optional)

To use Docker Postgres instead of Supabase cloud:

```bash
docker compose --profile local-db up -d postgres
```

Set `DATABASE_URL` to the local connection string.

## API authentication

The web app sends `Authorization: Bearer <supabase_access_token>` to FastAPI.

`GET /v1/me` verifies the JWT with `SUPABASE_JWT_SECRET` and upserts the `users` row (`auth_user_id` = Supabase user UUID).
