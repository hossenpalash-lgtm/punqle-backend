-- Pre-baked Punqle Actors v2 base clips -- one real Veo 3.1 video per
-- actor/situation, generated once (see scripts/populate_actor_video_clips.py)
-- and reused across every business that picks that actor. Redubbed
-- per-user with a fresh narration track via Sync Labs at request time
-- (see generate-actor-video-v2 in main.py) -- this table only ever holds
-- the silent pre-baked base clip, never anyone's actual ad content.
create table if not exists actor_video_clips (
  id uuid primary key default gen_random_uuid(),
  actor_id text not null,
  situation_id text not null,
  video_base64 text not null,
  created_at timestamptz not null default now(),
  unique (actor_id, situation_id)
);
create index if not exists actor_video_clips_actor_id_idx on actor_video_clips (actor_id);
alter table actor_video_clips enable row level security;
