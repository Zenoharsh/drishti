-- DRISHTI SCHEMA

create table if not exists corridors (
    id text primary key,
    name text not null,
    center_lat double precision not null,
    center_lon double precision not null,
    radius_km double precision not null,
    supplier text,
    baseline_vessel_count integer not null default 10
);

create table if not exists ports (
    id text primary key,
    name text not null,
    lat double precision not null,
    lon double precision not null
);

create table if not exists refineries (
    id text primary key,
    name text not null,
    lat double precision not null,
    lon double precision not null,
    capacity_bpd bigint
);

-- Links a refinery's dependence on a given corridor + its target crude spec
create table if not exists refinery_baselines (
    id serial primary key,
    refinery_id text references refineries(id),
    corridor_id text references corridors(id),
    daily_demand_m3 double precision not null,
    max_disruption_fraction double precision not null,
    refinery_dependency_weight double precision not null,
    target_api_gravity double precision not null,
    target_sulfur_pct double precision not null
);

create table if not exists spr_inventory (
    id serial primary key,
    current_inventory_m3 double precision not null,
    safety_floor_pct double precision not null default 0.20
);

create table if not exists crude_assay_specs (
    id text primary key,
    source_name text not null,
    api_gravity double precision not null,
    sulfur_pct double precision not null,
    estimated_replacement_arrival_days integer not null
);

create table if not exists sanctions_registry (
    id serial primary key,
    entity_name text not null
);

create table if not exists commodity_prices (
    id serial primary key,
    price_date date not null,
    price_usd double precision not null
);

create table if not exists vessels (
    id serial primary key,
    corridor_id text references corridors(id),
    lat double precision not null,
    lon double precision not null
);

create table if not exists headlines (
    id serial primary key,
    url text unique not null,
    title text not null,
    source text,
    published_at timestamptz,
    processed boolean not null default false
);

create table if not exists risk_snapshots (
    id serial primary key,
    corridor_id text references corridors(id),
    disruption_score double precision not null,
    severity double precision not null,
    sanctions_flag double precision not null,
    price_delta_norm double precision not null,
    ais_density_norm double precision not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_risk_snapshots_corridor_time
    on risk_snapshots (corridor_id, created_at desc);
