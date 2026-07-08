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
        elif api_diff <= 6 and sulfur_diff <= 0.3:
            compatibility = "moderate"
        else:
            compatibility = "low"

        ranked.append({
            "source_id": source["id"],
            "source_name": source["source_name"],
            "compatibility": compatibility,
            "api_gravity": source["api_gravity"],
            "sulfur_pct": source["sulfur_pct"],
            "estimated_replacement_arrival_days": source["estimated_replacement_arrival_days"],
            "_sort_key": api_diff + sulfur_diff,
        })

    ranked.sort(key=lambda x: x["_sort_key"])
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

    if total_shortfall > available_for_drawdown:
        daily_drawdown_m3 = available_for_drawdown / gap_days if gap_days > 0 else 0
        fully_covered = False
    else:
        daily_drawdown_m3 = total_daily_shortfall
        fully_covered = True

    return {
        "daily_drawdown_m3": round(daily_drawdown_m3, 2),
        "gap_days": gap_days,
        "fully_covered": fully_covered,
        "safety_floor_m3": round(safety_floor_m3, 2),
    }
