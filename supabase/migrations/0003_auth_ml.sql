-- Learned model parameters (e.g. ranker weights), one JSON document per key.
create table model_state (
  key         text primary key,
  value       jsonb not null,
  updated_at  timestamptz not null default now()
);
alter table model_state enable row level security;

-- Real accounts now exist: a signed-in user may read only their own notifications
-- (Realtime honours this). Replaces the demo policy that let anon read everything.
drop policy if exists "anon_select_notifications" on notifications;
do $$
begin
  if exists (select 1 from pg_roles where rolname = 'authenticated')
     and exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                 where n.nspname = 'auth' and p.proname = 'jwt') then
    execute $p$create policy "own_notifications" on notifications for select to authenticated
             using (recipient_email = lower(auth.jwt() ->> 'email'))$p$;
  end if;
end $$;
