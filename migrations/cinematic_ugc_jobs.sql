-- Tracks the credit tier (standard/premium) a Cinematic UGC (Seedance
-- 2.5, via Replicate) video was generated at, keyed by Replicate's own
-- prediction id. Same shape and same reason as avatar_video_jobs --
-- Replicate's own status response never says which resolution tier a
-- prediction was billed at, and tier changes the credit price, so this
-- can't be trusted from the client at poll time.
create table if not exists cinematic_ugc_jobs (
  prediction_id text primary key,
  owner_id uuid not null,
  tier text not null check (tier in ('standard', 'premium')),
  created_at timestamptz not null default now()
);
create index if not exists cinematic_ugc_jobs_owner_id_idx on cinematic_ugc_jobs (owner_id);
alter table cinematic_ugc_jobs enable row level security;
