create table if not exists scheduled_posts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  platform text not null check (platform in ('facebook', 'youtube')),
  external_post_id text,
  caption text not null default '',
  description text,
  image_base64 text,
  scheduled_time timestamptz not null,
  status text not null default 'scheduled' check (status in ('scheduled', 'published', 'failed')),
  error text,
  source text not null default 'single' check (source in ('single', 'weekly_plan')),
  content_plan_id uuid,
  content_plan_day text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
-- No FK on content_plan_id: generate_content_plan() deletes+replaces the
-- user's one active plan on every regenerate. A cascading FK would
-- silently delete scheduled_posts rows for posts already committed to
-- Facebook/YouTube. content_plan_id/day are informational only.
create index if not exists scheduled_posts_owner_id_idx on scheduled_posts (owner_id);
create index if not exists scheduled_posts_owner_scheduled_time_idx on scheduled_posts (owner_id, scheduled_time);
alter table scheduled_posts enable row level security;
