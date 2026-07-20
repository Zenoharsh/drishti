from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import os
from src.config.db import get_db
from src.services.calculators import compute_scenario, rank_substitutes, compute_drawdown, compute_economic_impact

router = APIRouter()


class CorridorRequest(BaseModel):
    corridor: str


def _latest_score(db, corridor_id: str) -> float:
    latest = (db.table("risk_snapshots")
              .select("disruption_score")
              .eq("corridor_id", corridor_id)
              .order("created_at", desc=True)
              .limit(1)
              .execute().data)
    return latest[0]["disruption_score"] if latest else 0.0


def _get_baselines_and_spr(db, corridor_id: str):
    baselines_raw = (db.table("refinery_baselines")
                      .select("*")
                      .eq("corridor_id", corridor_id)
                      .execute().data)
    if not baselines_raw:
        raise HTTPException(status_code=404,
                             detail=f"No refinery baselines seeded for corridor: {corridor_id}")

    spr = db.table("spr_inventory").select("*").limit(1).execute().data
    if not spr:
        raise HTTPException(status_code=500, detail="No SPR inventory seeded")

    return baselines_raw, spr[0]


@router.post("/scenario/quick")
def scenario_quick(req: CorridorRequest):
    db = get_db()
    score = _latest_score(db, req.corridor)
    baselines_raw, spr = _get_baselines_and_spr(db, req.corridor)

    result = compute_scenario(score, baselines_raw, spr["current_inventory_m3"])
    
    total_shortfall_m3 = 0.0
    for b in baselines_raw:
        supply_loss_fraction = score * b["max_disruption_fraction"]
        total_shortfall_m3 += b["daily_demand_m3"] * supply_loss_fraction
        
    all_refineries = db.table("refineries").select("capacity_bpd").execute().data
    national_capacity_bpd = sum((r.get("capacity_bpd") or 0) for r in all_refineries)
    # Fallback in case DB is empty
    if national_capacity_bpd == 0:
        national_capacity_bpd = 5_000_000
        
    economic_impact = compute_economic_impact(
        total_shortfall_m3, 
        unmitigated_gap_days=30, 
        national_capacity_bpd=national_capacity_bpd
    )
    
    return {
        "corridor": req.corridor, 
        "disruption_score": score, 
        **result,
        "economic_impact_30_days": economic_impact
    }


@router.post("/procurement/quick")
def procurement_quick(req: CorridorRequest):
    db = get_db()
    baselines_raw, _ = _get_baselines_and_spr(db, req.corridor)

    # Primary refinery = highest dependency weight for this corridor
    primary = max(baselines_raw, key=lambda b: b["refinery_dependency_weight"])

    sources = db.table("crude_assay_specs").select("*").execute().data
    ranked = rank_substitutes(primary["target_api_gravity"], primary["target_sulfur_pct"], sources)

    return {
        "corridor": req.corridor,
        "primary_refinery_id": primary["refinery_id"],
        "substitutes": ranked,
    }


@router.get("/reserve")
def reserve(corridor: str):
    db = get_db()
    score = _latest_score(db, corridor)
    baselines_raw, spr = _get_baselines_and_spr(db, corridor)

    scenario_result = compute_scenario(score, baselines_raw, spr["current_inventory_m3"])
    baselines_by_id = {b["refinery_id"]: b for b in baselines_raw}

    # gap_days = top procurement match's transit estimate
    primary = max(baselines_raw, key=lambda b: b["refinery_dependency_weight"])
    sources = db.table("crude_assay_specs").select("*").execute().data
    ranked = rank_substitutes(primary["target_api_gravity"], primary["target_sulfur_pct"], sources, top_n=1)
    gap_days = ranked[0]["estimated_replacement_arrival_days"] if ranked else 20

    drawdown = compute_drawdown(
        scenario_result["refineries"], baselines_by_id, gap_days,
        spr["current_inventory_m3"], spr.get("safety_floor_pct", 0.20),
    )
    return {"corridor": corridor, **drawdown}


@router.post("/run-simulation")
def run_simulation():
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "simulate_crisis.py")
        result = subprocess.run(["python", script_path], capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e.stderr}")

