-- Tracks an "AI Actor" talking video job (OmniHuman via Replicate),
-- keyed by Replicate's own prediction id — needed so credits are
-- charged server-side on success only, never trusted from the client
-- at poll time. No tier column: unlike Avatar/Cinematic UGC, this
-- style has one fixed price (AI_ACTOR_VIDEO_CREDIT_COST).
create table if not exists ai_actor_video_jobs (
  prediction_id text primary key,
  owner_id uuid not null,
  created_at timestamptz not null default now()
);
create index if not exists ai_actor_video_jobs_owner_id_idx on ai_actor_video_jobs (owner_id);
alter table ai_actor_video_jobs enable row level security;
