create extension if not exists vector;

create type match_status as enum ('new', 'notified', 'accepted', 'rejected');

create table requirements (
  id                   uuid primary key default gen_random_uuid(),
  client_name          text not null,
  contact_email        text not null,
  product_requirement  text not null,
  category             text not null,
  quantity             numeric not null check (quantity > 0),
  unit                 text not null,
  budget               numeric not null check (budget > 0),
  location             text not null,
  latitude             double precision,
  longitude            double precision,
  needed_within_days   int not null check (needed_within_days > 0),
  notes                text,
  embedding            vector(384),
  status               text not null default 'open',
  created_at           timestamptz not null default now()
);

create table offerings (
  id                   uuid primary key default gen_random_uuid(),
  supplier_name        text not null,
  contact_email        text not null,
  product_offered      text not null,
  category             text not null,
  available_quantity   numeric not null check (available_quantity > 0),
  unit                 text not null,
  unit_price           numeric not null check (unit_price > 0),
  pricing_notes        text,
  location             text not null,
  latitude             double precision,
  longitude            double precision,
  lead_time_days       int not null check (lead_time_days >= 0),
  delivery_scope       text not null check (delivery_scope in ('local','regional','national','international')),
  notes                text,
  embedding            vector(384),
  status               text not null default 'active',
  created_at           timestamptz not null default now()
);

create table matches (
  id              uuid primary key default gen_random_uuid(),
  requirement_id  uuid not null references requirements(id) on delete cascade,
  offering_id     uuid not null references offerings(id) on delete cascade,
  score           numeric(5,2) not null,
  score_breakdown jsonb not null,
  status          match_status not null default 'new',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (requirement_id, offering_id)
);

create table notifications (
  id               uuid primary key default gen_random_uuid(),
  match_id         uuid not null references matches(id) on delete cascade,
  recipient_role   text not null check (recipient_role in ('client','supplier')),
  recipient_email  text not null,
  message          text not null,
  is_read          boolean not null default false,
  created_at       timestamptz not null default now()
);

create table email_outbox (
  id          uuid primary key default gen_random_uuid(),
  to_email    text not null,
  subject     text not null,
  body        text not null,
  created_at  timestamptz not null default now(),
  sent_at     timestamptz
);

create table geocode_cache (
  query       text primary key,
  latitude    double precision,
  longitude   double precision,
  created_at  timestamptz not null default now()
);
