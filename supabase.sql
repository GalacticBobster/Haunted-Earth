-- Run once in Supabase SQL Editor ("Run without RLS")
create table if not exists haunts (
  id          text primary key,
  kind        text,
  title       text,
  lat         double precision,
  lon         double precision,
  severity    double precision,
  status      text,
  verdict     text,
  story       text,
  first_seen  timestamptz,
  updated_at  timestamptz default now()
);

create table if not exists chatter (
  id         bigint generated always as identity primary key,
  sender     text,
  haunt_id   text,
  message    text,
  created_at timestamptz default now()
);

-- Newsroom tables (run these too)
create table if not exists factchecks (
  id           bigint generated always as identity primary key,
  haunt_id     text,
  article_url  text,
  headline     text,
  outlet       text,
  checker      text,
  claim        text,
  verdict      text,
  explanation  text,
  created_at   timestamptz default now()
);

create table if not exists outlets (
  outlet        text primary key,
  confirmed     int,
  plausible     int,
  mismatched    int,
  implausible   int,
  unverifiable  int,
  score         double precision,
  score_sd      double precision,
  updated_at    timestamptz default now()
);

-- Only if you turned on RLS for haunts/chatter: let the public site read these too
-- alter table factchecks enable row level security;
-- alter table outlets    enable row level security;
-- create policy "public read" on factchecks for select using (true);
-- create policy "public read" on outlets    for select using (true);

-- v3: agency consensus + county alerts (run these too)
alter table haunts add column if not exists consensus text;

create table if not exists county_alerts (
  id            text primary key,
  fips          text,
  state         text,
  county        text,
  event         text,
  severity      text,
  sev_rank      int,
  headline      text,
  expires       timestamptz,
  lat           double precision,
  lon           double precision,
  linked_haunt  text,
  updated_at    timestamptz default now()
);
-- If RLS is on:  alter table county_alerts enable row level security;
--                create policy "public read" on county_alerts for select using (true);

-- v4: warning system (run these too)
create table if not exists places (
  id       text primary key,
  name     text,
  lat      double precision,
  lon      double precision,
  coastal  boolean default false
);

create table if not exists warnings (
  id          text primary key,      -- place_id|key
  place_id    text,
  place_name  text,
  key         text,
  hazard      text,
  level       int,                   -- 1 Advisory, 2 Watch, 3 Warning
  level_name  text,
  headline    text,
  detail      text,
  updated_at  timestamptz default now()
);
-- If RLS is on: allow public read on warnings, and public insert/delete on places
-- (or keep the sidebar for local use only).

-- v5: share-by-QR (run this too)
alter table places add column if not exists email  text;
alter table places add column if not exists shared boolean default false;

-- v7: relief missions (run this too)
create table if not exists missions (
  id              text primary key,        -- place_id--hazard
  place_id        text,
  place_name      text,
  hazard          text,
  level           int,
  status          text,                    -- active | stood down
  tasks_json      text,
  resources_json  text,
  needs_json      text,
  nearest_json    text,
  checklist_json  text,
  updated_at      timestamptz default now()
);

-- v8: drills (run this too)
create table if not exists drills (
  id           text primary key,
  kind         text,
  label        text,
  lat          double precision,
  lon          double precision,
  mag          double precision,
  depth_km     double precision,
  vmax_kt      double precision,
  heading_deg  double precision,
  speed_kmh    double precision,
  active       boolean default true,
  created_at   timestamptz default now()
);

-- v9: Airport Watch (run this too)
create table if not exists airports (
  icao        text primary key,
  data_json   text,
  updated_at  timestamptz default now()
);

-- v10: crew status (run this too)
create table if not exists agents (
  name text primary key, pid int, runs int, cycles int,
  last_action text, last_seen timestamptz, started timestamptz
);
