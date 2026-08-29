-- Base table, predates brand_name (see business_profile_brand_name.sql
-- for that later addition — kept as a separate migration to preserve
-- the real order these columns were actually added in).
create table if not exists business_profile (
  owner_id uuid primary key,
  category text not null default 'other',
  brand_color text,
  logo_base64 text,
  logo_mime_type text,
  updated_at timestamptz not null default now()
);
alter table business_profile enable row level security;
