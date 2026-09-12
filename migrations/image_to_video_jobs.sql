-- Tracks jobs for the "turn a generated image into a short video" tool
-- (home page's Video action on a generated image) -- model, duration,
-- and (for the two Replicate-backed models) Replicate's own prediction
-- id, keyed by our own server-generated job id. Needed because credit
-- cost depends on model + duration, neither of which can be trusted
-- from the client at poll time (same reasoning as cinematic_ugc_jobs
-- and avatar_video_jobs's own tier tracking).
create table if not exists image_to_video_jobs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  model text not null check (model in ('veo_3_1', 'kling_3_pro', 'seedance_2_5')),
  duration_seconds integer not null,
  prediction_id text,
  created_at timestamptz not null default now()
);
create index if not exists image_to_video_jobs_owner_id_idx on image_to_video_jobs (owner_id);
alter table image_to_video_jobs enable row level security;
