create table if not exists referrals (
  id uuid primary key default gen_random_uuid(),
  referrer_id uuid not null,
  referee_id uuid not null,
  created_at timestamptz not null default now()
);
create index if not exists referrals_referrer_id_idx on referrals (referrer_id);
alter table referrals enable row level security;
