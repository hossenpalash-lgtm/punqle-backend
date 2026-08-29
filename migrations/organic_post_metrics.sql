-- Organic performance snapshots for posts published through Punqle
-- (Facebook/YouTube only — see main.py's fetch functions for why).
-- Deliberately separate from any future paid-ad metrics table: a plain
-- organic post has no spend/clicks/conversions/ROAS, and Meta's ad
-- structure (campaign/ad-set/ad, budget, targeting) doesn't exist in
-- this codebase yet and shouldn't be guessed at here.
--
-- One row per fetch = a real historical snapshot, not an overwritten
-- running total — a post's likes at 10:00, 10:15, 10:30 are 3 separate
-- rows, giving a trend for free later with no schema change. fetch_bucket
-- (fetched_at truncated to the same 15-minute window the backend treats
-- as "fresh enough to skip re-fetching") backs a unique constraint so two
-- near-simultaneous requests (e.g. a double-clicked Refresh, or two open
-- tabs) can't both insert a genuine duplicate snapshot for the same post
-- in the same window — the second write upserts onto the first's row
-- instead of creating a sibling. This does NOT collapse history: a
-- fetch in a later window still gets its own new row.
create table if not exists organic_post_metrics (
  id uuid primary key default gen_random_uuid(),
  scheduled_post_id uuid not null references scheduled_posts(id) on delete cascade,
  platform text not null check (platform in ('facebook', 'youtube')),
  external_post_id text not null,
  fetched_at timestamptz not null default now(),
  fetch_bucket timestamptz generated always as (date_bin('15 minutes', fetched_at, timestamptz '2000-01-01')) stored,
  views bigint,
  likes bigint,
  comments bigint,
  shares bigint,
  raw jsonb,
  created_at timestamptz not null default now(),
  unique (scheduled_post_id, fetch_bucket)
);
alter table organic_post_metrics enable row level security;
