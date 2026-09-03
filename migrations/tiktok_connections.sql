create table if not exists tiktok_connections (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null unique,
  open_id text not null,
  display_name text not null,
  access_token text not null,
  refresh_token text not null,
  token_expires_at timestamptz not null,
  connected_at timestamptz not null default now()
);

create index if not exists tiktok_connections_owner_id_idx on tiktok_connections (owner_id);

alter table tiktok_connections enable row level security;
