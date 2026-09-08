-- Append-only usage history for every credit-costing (and Voiceover's
-- now-free) action — built for the pre-beta pricing review (2026-09-08).
-- ad_credits only ever holds a current balance; before this table there
-- was no way to see WHAT a user actually spent credits on, in what
-- order, or where they hit a wall and stopped — exactly the behavioral
-- signal a real pricing decision needs, and exactly what a beta cohort
-- is meant to produce. One row per action, never updated or collapsed,
-- same one-row-per-event precedent as organic_post_metrics.
--
-- feature is a short slug matching _spend_ad_credit's/_spend_ad_credits'
-- call sites (e.g. 'image_generate', 'video_generate', 'avatar_video',
-- 'cinematic_ugc', 'tryon_image', 'tryon_animate', 'remove_background',
-- 'enhance_image', 'weekly_plan_day', 'voiceover') — deliberately a
-- free-text column, not a check-constrained enum, since new features
-- will keep adding new slugs and a migration shouldn't be required each
-- time. tier is only set for the two features with real sub-tiers
-- (avatar: standard/premium; cinematic_ugc: standard/premium) — null
-- everywhere else. credits_spent is 0 for Voiceover's now-free usage,
-- logged anyway since "how many people use this for free" is itself
-- real signal for a future pricing call.
create table if not exists credit_usage_log (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  feature text not null,
  tier text,
  credits_spent integer not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists credit_usage_log_owner_id_idx on credit_usage_log (owner_id);
create index if not exists credit_usage_log_feature_idx on credit_usage_log (feature);
alter table credit_usage_log enable row level security;
