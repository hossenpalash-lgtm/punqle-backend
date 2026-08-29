create table if not exists generated_posts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  item_description text not null,
  facebook_caption text not null,
  whatsapp_message text not null,
  image_base64 text not null,
  created_at timestamptz not null default now()
);
create index if not exists generated_posts_owner_id_idx on generated_posts (owner_id);
alter table generated_posts enable row level security;
