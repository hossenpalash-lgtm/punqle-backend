-- Tracks a Punqle Actors v2 redub job (Sync Labs, via Replicate), keyed
-- by Replicate's own prediction id -- same shape and same reason as the
-- older ai_actor_video_jobs table: credits are charged server-side on
-- success only, never trusted from the client at poll time.
create table if not exists actor_video_v2_jobs (
  prediction_id text primary key,
  owner_id uuid not null,
  created_at timestamptz not null default now()
);
create index if not exists actor_video_v2_jobs_owner_id_idx on actor_video_v2_jobs (owner_id);
alter table actor_video_v2_jobs enable row level security;
