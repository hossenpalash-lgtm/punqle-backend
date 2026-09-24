create table if not exists real_cost_metrics (
  id uuid primary key default gen_random_uuid(),
  feature text not null,
  provider text not null,
  model text,
  metrics jsonb,
  created_at timestamptz not null default now()
);
create index if not exists real_cost_metrics_feature_created_at_idx on real_cost_metrics (feature, created_at);
alter table real_cost_metrics enable row level security;
