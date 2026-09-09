-- Minimal real "Projects" concept for the new home screen (2026-09-10) —
-- name + created_at only, no content-linking yet. Deliberately scoped
-- down: an "inside a project" view (which generations belong to which
-- project) is a separate, later decision, not built here.
create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  name text not null,
  created_at timestamptz not null default now()
);
create index if not exists projects_owner_id_idx on projects (owner_id);
alter table projects enable row level security;
