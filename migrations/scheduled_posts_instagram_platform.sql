-- Lets scheduled_posts (and its metrics table) hold Instagram posts, so
-- every post published to Instagram through Punqle is remembered with its
-- real media id. Nothing reads Instagram numbers yet (that needs the
-- instagram_manage_insights permission, still to be approved) — this only
-- starts the history now so it exists when that permission arrives.
alter table scheduled_posts drop constraint if exists scheduled_posts_platform_check;
alter table scheduled_posts add constraint scheduled_posts_platform_check
  check (platform in ('facebook', 'youtube', 'tiktok', 'instagram'));

alter table organic_post_metrics drop constraint if exists organic_post_metrics_platform_check;
alter table organic_post_metrics add constraint organic_post_metrics_platform_check
  check (platform in ('facebook', 'youtube', 'instagram'));
