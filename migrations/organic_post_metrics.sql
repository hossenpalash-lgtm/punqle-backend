-- Organic performance snapshots for posts published through Punqle
-- (Facebook/YouTube only — see main.py's fetch functions for why).
-- Deliberately separate from any future paid-ad metrics table: a plain
-- organic post has no spend/clicks/conversions/ROAS, and Meta's ad
-- structure (campaign/ad-set/ad, budget, targeting) doesn't exist in
-- this codebase yet and shouldn't be guessed at here. One row per
-- fetch (append-only snapshot, never updated in place) — gives a
-- trend-over-time for free later without a schema change.
create table if not exists organic_post_metrics (
  id uuid primary key default gen_random_uuid(),
  scheduled_post_id uuid not null references scheduled_posts(id) on delete cascade,
  platform text not null check (platform in ('facebook', 'youtube')),
  external_post_id text not null,
  fetched_at timestamptz not null default now(),
  views bigint,
  likes bigint,
  comments bigint,
  shares bigint,
  raw jsonb,
  created_at timestamptz not null default now()
);
create index if not exists organic_post_metrics_scheduled_post_id_idx on organic_post_metrics (scheduled_post_id);
alter table organic_post_metrics enable row level security;
