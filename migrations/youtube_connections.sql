create table if not exists youtube_connections (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null unique,
  channel_id text not null,
  channel_title text not null,
  access_token text not null,
  refresh_token text not null,
  token_expires_at timestamptz not null,
  connected_at timestamptz not null default now()
);

create index if not exists youtube_connections_owner_id_idx on youtube_connections (owner_id);

alter table youtube_connections enable row level security;
