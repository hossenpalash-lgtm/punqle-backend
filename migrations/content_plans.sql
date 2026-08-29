create table if not exists content_plans (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  period_start date not null,
  period_end date not null,
  status text not null default 'active',
  posts jsonb not null,
  input_text text,
  created_at timestamptz not null default now()
);
create index if not exists content_plans_owner_id_idx on content_plans (owner_id);
alter table content_plans enable row level security;
