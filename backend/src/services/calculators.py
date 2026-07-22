"""
All deterministic math for Drishti: no LLM calls, no DB calls inside these
functions — they take plain values/dicts in and return plain values/dicts
out, so they're easy to unit test in isolation.
"""
import math

# ---------- Signal 4: AIS density ----------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def count_vessels_near(corridor: dict, vessels: list[dict]) -> int:
    count = 0
    for v in vessels:
        d = haversine_km(corridor["center_lat"], corridor["center_lon"], v["lat"], v["lon"])
        if d <= corridor["radius_km"]:
            count += 1
    return count


def ais_density_norm(current_count: int, baseline_count: int) -> float:
    if baseline_count <= 0:
        return 0.0
    ratio = current_count / baseline_count
    deviation = abs(ratio - 1.0)
    return min(deviation, 1.0)


# ---------- Signal 3: price delta ----------

def price_delta_norm(prices_oldest_to_newest: list[float], cap_pct: float = 0.05) -> float:
    """prices_oldest_to_newest: trailing N days, oldest first, newest last."""
    if len(prices_oldest_to_newest) < 2 or prices_oldest_to_newest[0] == 0:
        return 0.0
    delta = (prices_oldest_to_newest[-1] - prices_oldest_to_newest[0]) / prices_oldest_to_newest[0]
    return min(abs(delta) / cap_pct, 1.0)


# ---------- Fusion ----------

def fuse_disruption_score(severity: float, sanctions_flag: float,
                           price_delta: float, ais_density: float) -> float:
    return (0.40 * severity + 0.25 * sanctions_flag +
            0.20 * price_delta + 0.15 * ais_density)


# ---------- Pipeline 2: Scenario (corridor-level days_of_cover, per-refinery impact) ----------

def compute_economic_impact(total_daily_shortfall_m3: float, unmitigated_gap_days: int, national_capacity_bpd: float = 5_000_000) -> dict:
    """
    Computes macroeconomic downstream impacts using elasticity approximations.
    1 m3 = ~6.289 barrels.
    """
    total_shortfall_bbl = total_daily_shortfall_m3 * 6.289
    baseline_daily_bbl = national_capacity_bpd
    
    # % shortfall of national capacity
    shortfall_pct = min((total_shortfall_bbl / baseline_daily_bbl) * 100, 100) if baseline_daily_bbl > 0 else 0
    
    # Simple elasticity model: e = 2.0 (fuel price is highly inelastic to supply drops)
    fuel_price_spike_pct = shortfall_pct * 2.0
    
    # GDP elasticity: a sustained 10% shock dragging for 30 days causes ~0.5% GDP hit.
    # Formula: (shortfall_pct / 10) * (gap_days / 30) * 0.5
    gdp_drag_pct = (shortfall_pct / 10.0) * (unmitigated_gap_days / 30.0) * 0.5
    
    return {
        "shortfall_pct": round(shortfall_pct, 2),
        "fuel_price_spike_pct": round(fuel_price_spike_pct, 2),
        "gdp_drag_pct": round(gdp_drag_pct, 3)
    }


def compute_scenario(disruption_score: float, refinery_baselines: list[dict],
                      spr_current_inventory_m3: float) -> dict:
    """
    refinery_baselines: rows from refinery_baselines for ONE corridor, each with
      daily_demand_m3, max_disruption_fraction, refinery_dependency_weight, refinery_id
    Returns corridor-level days_of_cover (shared reserve, summed demand) plus
    per-refinery impact_pct — avoids double-counting the national SPR.
    """
    total_effective_demand = 0.0
    refinery_impacts = []

    for rb in refinery_baselines:
        supply_loss_fraction = disruption_score * rb["max_disruption_fraction"]
        effective_daily_demand = rb["daily_demand_m3"] * (1 - supply_loss_fraction)
        total_effective_demand += effective_daily_demand

        refinery_impact_pct = supply_loss_fraction * rb["refinery_dependency_weight"]
        refinery_impacts.append({
            "refinery_id": rb["refinery_id"],
            "refinery_impact_pct": round(refinery_impact_pct, 4),
        })

    days_of_cover = (spr_current_inventory_m3 / total_effective_demand
                      if total_effective_demand > 0 else float("inf"))

    return {
        "days_of_cover": round(days_of_cover, 2),
        "refineries": refinery_impacts,
    }


# ---------- Pipeline 3: Procurement ----------

def rank_substitutes(target_api: float, target_sulfur: float,
                      candidate_sources: list[dict], top_n: int = 3) -> list[dict]:
    ranked = []
    for source in candidate_sources:
        api_diff = abs(source["api_gravity"] - target_api)
        sulfur_diff = abs(source["sulfur_pct"] - target_sulfur)

        if api_diff <= 3 and sulfur_diff <= 0.1:
            compatibility = "high"
            chem_penalty = 0
        elif api_diff <= 6 and sulfur_diff <= 0.3:
            compatibility = "moderate"
            chem_penalty = 10
        else:
            compatibility = "low"
            chem_penalty = 25

        # Optimize for lowest total cost and fastest arrival, while matching chemistry.
        spot_price = source.get("current_spot_price_usd", 80.0)
        freight = source.get("freight_cost_per_bbl", 3.0)
        days = source.get("estimated_replacement_arrival_days", 20)
        
        total_cost = spot_price + freight
        
        # Base score 100. Deduct for price > $75, arrival > 10 days, and chem mismatch.
        price_penalty = max(0, total_cost - 75.0) * 1.5
        time_penalty = max(0, days - 10) * 1.0
        
        raw_match_score = 100 - price_penalty - time_penalty - chem_penalty
        match_score = max(0, min(100, raw_match_score))

        ranked.append({
            "source_id": source["id"],
            "source_name": source["source_name"],
            "compatibility": compatibility,
            "api_gravity": source["api_gravity"],
            "sulfur_pct": source["sulfur_pct"],
            "estimated_replacement_arrival_days": days,
            "current_spot_price_usd": spot_price,
            "freight_cost_per_bbl": freight,
            "procurement_score": int(round(match_score)),
            "_sort_key": match_score,
        })

    # Sort descending so highest match score is first
    ranked.sort(key=lambda x: x["_sort_key"], reverse=True)
    for r in ranked:
        del r["_sort_key"]
    return ranked[:top_n]


# ---------- Pipeline 4: Reserve drawdown ----------

def compute_drawdown(refinery_impacts: list[dict], refinery_baselines_by_id: dict,
                      gap_days: int, spr_current_inventory_m3: float,
                      safety_floor_pct: float = 0.20) -> dict:
    """
    refinery_impacts: [{refinery_id, refinery_impact_pct}, ...] from compute_scenario
    refinery_baselines_by_id: {refinery_id: {daily_demand_m3, ...}}
    Cumulative shortfall across ALL affected refineries, not just the primary one.
    """
    total_daily_shortfall = 0.0
    for ri in refinery_impacts:
        baseline = refinery_baselines_by_id.get(ri["refinery_id"])
        if not baseline:
            continue
        total_daily_shortfall += baseline["daily_demand_m3"] * ri["refinery_impact_pct"]

    total_shortfall = total_daily_shortfall * gap_days
    safety_floor_m3 = spr_current_inventory_m3 * safety_floor_pct
    available_for_drawdown = spr_current_inventory_m3 - safety_floor_m3

    drawdown_schedule = []
    remaining_available = available_for_drawdown
    
    for day in range(1, gap_days + 1):
        # Front-load the release: heavy on early days, tapering off.
        taper_factor = 1.0 - (0.5 * (day - 1) / max(gap_days - 1, 1))
        desired_drawdown = total_daily_shortfall * taper_factor
        
        actual_drawdown = min(desired_drawdown, remaining_available)
        remaining_available -= actual_drawdown
        
        drawdown_schedule.append({
            "day": day,
            "volume_m3": round(actual_drawdown, 2)
        })
        
    total_drawn = available_for_drawdown - remaining_available
    fully_covered = total_drawn >= total_shortfall

    return {
        "total_drawn_m3": round(total_drawn, 2),
        "schedule": drawdown_schedule,
        "gap_days": gap_days,
        "fully_covered": fully_covered,
        "safety_floor_m3": round(safety_floor_m3, 2),
    }
