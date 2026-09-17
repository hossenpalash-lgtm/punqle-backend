-- "Create Your Own Actor" -- a saved photo, name, and gender (for
-- OmniHuman voice selection). No trained avatar object on any
-- vendor's side; OmniHuman takes the photo directly on every video
-- generation call, so there's nothing to "train" here.
create table if not exists custom_actors (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  name text not null,
  gender text not null check (gender in ('female', 'male')),
  photo_base64 text not null,
  photo_mime_type text not null default 'image/png',
  created_at timestamptz not null default now()
);
create index if not exists custom_actors_owner_id_idx on custom_actors (owner_id);
alter table custom_actors enable row level security;
