-- Tracks the credit tier (standard/premium) a HeyGen avatar video was
-- generated at, keyed by HeyGen's own video_id. HeyGen's own status
-- response never says which engine/tier a video was rendered with, and
-- tier changes the credit price, so this can't be trusted from the
-- client at poll time -- the backend writes it here at generation-start
-- and reads it back at poll-completion, then deletes the row (its only
-- job was tier tracking, not history).
create table if not exists avatar_video_jobs (
  video_id text primary key,
  owner_id uuid not null,
  tier text not null check (tier in ('standard', 'premium')),
  created_at timestamptz not null default now()
);
create index if not exists avatar_video_jobs_owner_id_idx on avatar_video_jobs (owner_id);
alter table avatar_video_jobs enable row level security;
