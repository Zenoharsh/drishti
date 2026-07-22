-- 1. Enable the vector extension
create extension if not exists vector;

-- 2. Create the table for historical precedents
create table if not exists historical_precedents (
    id serial primary key,
    event_title text not null,
    event_date date not null,
    description text not null,
    economic_impact_summary text not null,
    embedding vector(768)
);

-- 3. Create a Postgres function (RPC) to perform similarity search
-- This allows our Python REST client to search vectors without needing raw SQL.
create or replace function match_precedents (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id int,
  event_title text,
  event_date date,
  description text,
  economic_impact_summary text,
  similarity float
)
language sql
as $$
  select
    hp.id,
    hp.event_title,
    hp.event_date,
    hp.description,
    hp.economic_impact_summary,
    1 - (hp.embedding <=> query_embedding) as similarity
  from historical_precedents hp
  where 1 - (hp.embedding <=> query_embedding) > match_threshold
  order by hp.embedding <=> query_embedding
  limit match_count;
$$;
