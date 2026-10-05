-- Gemini Omni became the default video engine on 2026-10-05, so two job
-- tables must accept 'omni' in their model column. Run this in the Supabase
-- SQL editor BEFORE the backend that uses Omni is deployed -- until it has
-- run, Image -> Video and Talking Video (the home page's Video tools) fail
-- when they try to record an Omni job.
alter table image_to_video_jobs drop constraint if exists image_to_video_jobs_model_check;
alter table image_to_video_jobs add constraint image_to_video_jobs_model_check
  check (model in ('omni', 'veo_3_1', 'kling_3_pro', 'seedance_2_5'));

alter table talking_video_jobs drop constraint if exists talking_video_jobs_model_check;
alter table talking_video_jobs add constraint talking_video_jobs_model_check
  check (model in ('omni', 'veo_3_1', 'kling_3_pro', 'seedance_2_5'));
