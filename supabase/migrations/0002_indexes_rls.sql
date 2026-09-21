create index on requirements using hnsw (embedding vector_cosine_ops);
create index on offerings using hnsw (embedding vector_cosine_ops);
create index on matches (requirement_id, score desc);
create index on matches (offering_id, score desc);
create index on notifications (recipient_email, is_read);
create index on requirements (contact_email);
create index on offerings (contact_email);

-- The backend connects as the database owner, which bypasses RLS.
alter table requirements enable row level security;
alter table offerings enable row level security;
alter table matches enable row level security;
alter table notifications enable row level security;
alter table email_outbox enable row level security;
alter table geocode_cache enable row level security;

-- Supabase provides the `anon` role; create it on plain Postgres so this file stays portable.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
end $$;

-- Demo-grade: anyone holding the anon key can read notifications (needed for Realtime).
create policy "anon_select_notifications" on notifications for select to anon using (true);

-- Realtime only emits changes for tables in this publication (exists on Supabase only).
do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    alter publication supabase_realtime add table notifications;
  end if;
end $$;
