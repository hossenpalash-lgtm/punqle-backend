create table if not exists competitor_analyses (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  source_key text not null,
  source_url text not null,
  competitor_name text not null,
  result jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, source_key)
);

create index if not exists competitor_analyses_owner_updated_idx on competitor_analyses (owner_id, updated_at desc);

alter table competitor_analyses enable row level security;
