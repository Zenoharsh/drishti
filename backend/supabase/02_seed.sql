-- CORRIDORS
insert into corridors (id, name, center_lat, center_lon, radius_km, supplier, baseline_vessel_count) values
('hormuz', 'Strait of Hormuz', 26.5667, 56.25, 100, 'Saudi Arabia / Iraq / UAE', 25),
('bab_el_mandeb', 'Bab-el-Mandeb', 12.6167, 43.4167, 80, 'Red Sea Transit', 15),
('red_sea_suez', 'Red Sea / Suez', 29.9668, 32.5498, 90, 'Egypt Transit', 18)
on conflict (id) do nothing;

-- REFINERIES
insert into refineries (id, name, lat, lon, capacity_bpd) values
('jamnagar', 'Jamnagar Refinery', 22.3700, 69.7000, 1240000),
('vizag', 'Visakhapatnam Refinery', 17.6868, 83.2185, 220000),
('paradip', 'Paradip Refinery', 20.3167, 86.6167, 300000)
on conflict (id) do nothing;

-- REFINERY BASELINES (per corridor)
insert into refinery_baselines (refinery_id, corridor_id, daily_demand_m3, max_disruption_fraction, refinery_dependency_weight, target_api_gravity, target_sulfur_pct) values
('jamnagar', 'hormuz', 197000, 0.6, 0.8, 33, 0.20),
('paradip', 'hormuz', 47000, 0.5, 0.5, 32, 0.22),
('vizag', 'bab_el_mandeb', 35000, 0.4, 0.4, 31, 0.25),
('jamnagar', 'red_sea_suez', 197000, 0.3, 0.3, 33, 0.20)
on conflict do nothing;

-- SPR INVENTORY (~9.5 days national cover at baseline demand)
insert into spr_inventory (current_inventory_m3, safety_floor_pct) values
(5300000, 0.20)
on conflict do nothing;

-- CRUDE ASSAY SPECS (real published approximate values)
insert into crude_assay_specs (id, source_name, api_gravity, sulfur_pct, estimated_replacement_arrival_days) values
('bonny_light', 'Nigeria - Bonny Light', 35.0, 0.15, 18),
('cabinda', 'Angola - Cabinda', 32.0, 0.17, 20),
('wti', 'USA - WTI', 39.6, 0.24, 22),
('urals', 'Russia - Urals', 31.0, 1.35, 25)
on conflict (id) do nothing;

-- SANCTIONS REGISTRY
insert into sanctions_registry (entity_name) values
('IRGC'), ('Iran'), ('Rosneft')
on conflict do nothing;

-- COMMODITY PRICES (Brent, 10-day series with one clear jump)
insert into commodity_prices (price_date, price_usd) values
(current_date - interval '9 days', 82.10),
(current_date - interval '8 days', 82.40),
(current_date - interval '7 days', 82.15),
(current_date - interval '6 days', 82.60),
(current_date - interval '5 days', 83.00),
(current_date - interval '4 days', 83.50),
(current_date - interval '3 days', 84.10),
(current_date - interval '2 days', 86.90),
(current_date - interval '1 days', 87.50),
(current_date, 88.00)
on conflict do nothing;

-- VESSELS (seeded near Hormuz, above baseline to demonstrate anomaly)
insert into vessels (corridor_id, lat, lon) values
('hormuz', 26.60, 56.20), ('hormuz', 26.55, 56.30), ('hormuz', 26.50, 56.15),
('hormuz', 26.65, 56.35), ('hormuz', 26.58, 56.28), ('hormuz', 26.52, 56.22),
('hormuz', 26.61, 56.18), ('hormuz', 26.48, 56.33), ('hormuz', 26.63, 56.27),
('hormuz', 26.57, 56.19), ('hormuz', 26.54, 56.31), ('hormuz', 26.66, 56.24),
('hormuz', 26.49, 56.26), ('hormuz', 26.59, 56.21), ('hormuz', 26.51, 56.29),
('hormuz', 26.62, 56.23), ('hormuz', 26.56, 56.34), ('hormuz', 26.60, 56.17),
('hormuz', 26.53, 56.25), ('hormuz', 26.64, 56.30), ('hormuz', 26.47, 56.20),
('hormuz', 26.58, 56.16), ('hormuz', 26.55, 56.36), ('hormuz', 26.61, 56.32),
('hormuz', 26.50, 56.28), ('hormuz', 26.63, 56.19), ('hormuz', 26.57, 56.33),
('hormuz', 26.52, 56.17), ('hormuz', 26.59, 56.35), ('hormuz', 26.65, 56.22),
('hormuz', 26.48, 56.29), ('hormuz', 26.60, 56.26)
on conflict do nothing;

-- HEADLINES (spanning the severity rubric range, for local testing without live RSS)
insert into headlines (url, title, source, published_at, processed) values
('https://example.com/h1', 'Iranian naval vessels intercept commercial tanker near Hormuz', 'test-fixture', now(), false),
('https://example.com/h2', 'Shipping companies monitor tensions in Gulf region', 'test-fixture', now(), false),
('https://example.com/h3', 'OPEC+ signals routine production review', 'test-fixture', now(), false)
on conflict (url) do nothing;
