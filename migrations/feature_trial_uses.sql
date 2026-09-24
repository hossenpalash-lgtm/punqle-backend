create table if not exists feature_trial_uses (
  owner_id uuid not null,
  feature text not null,
  used_at timestamptz not null default now(),
  primary key (owner_id, feature)
);
alter table feature_trial_uses enable row level security;
