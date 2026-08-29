create table if not exists ad_credits (
  owner_id uuid primary key,
  credits integer not null default 3,
  updated_at timestamptz not null default now()
);
alter table ad_credits enable row level security;
