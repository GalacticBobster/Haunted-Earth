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
