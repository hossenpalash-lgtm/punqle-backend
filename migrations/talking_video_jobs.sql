-- Tracks jobs for the "talking video" chain (Video action's optional
-- "Add spoken narration" toggle): animate the image (Kling/Seedance/
-- Veo, same as the plain Video action) -> synthesize narration audio
-- (OpenAI TTS) -> Sync Labs lip-sync redub. Two separate Replicate
-- predictions happen one after another for a single user-facing job,
-- so this table also tracks which stage the job is in (poll needs to
-- know whether it's still waiting on the motion clip or the redub).
create table if not exists talking_video_jobs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  model text not null check (model in ('veo_3_1', 'kling_3_pro', 'seedance_2_5')),
  duration_seconds integer not null,
  narration text not null,
  voice_gender text not null check (voice_gender in ('female', 'male')),
  stage text not null default 'animating' check (stage in ('animating', 'redubbing')),
  prediction_id text,
  created_at timestamptz not null default now()
);
create index if not exists talking_video_jobs_owner_id_idx on talking_video_jobs (owner_id);
alter table talking_video_jobs enable row level security;
