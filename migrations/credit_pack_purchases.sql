create table if not exists credit_pack_purchases (
  stripe_session_id text primary key,
  owner_id uuid not null,
  pack text not null,
  credits integer not null,
  created_at timestamptz not null default now()
);
create index if not exists credit_pack_purchases_owner_id_idx on credit_pack_purchases (owner_id);
alter table credit_pack_purchases enable row level security;
