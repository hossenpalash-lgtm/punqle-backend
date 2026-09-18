-- Tracks the credit tier (standard/premium) a video Upscale (Topaz Labs,
-- via Replicate) job was started at, keyed by Replicate's own prediction
-- id. Same shape and same reason as cinematic_ugc_jobs/avatar_video_jobs
-- -- Replicate's own status response never says which resolution tier a
-- prediction was billed at, and tier changes the credit price, so this
-- can't be trusted from the client at poll time.
create table if not exists upscale_video_jobs (
  prediction_id text primary key,
  owner_id uuid not null,
  tier text not null check (tier in ('standard', 'premium')),
  created_at timestamptz not null default now()
);
create index if not exists upscale_video_jobs_owner_id_idx on upscale_video_jobs (owner_id);
alter table upscale_video_jobs enable row level security;
