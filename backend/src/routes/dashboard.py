from fastapi import APIRouter, HTTPException
from src.routes.risk import get_risk_corridors
from src.routes.actions import (
    scenario_quick, 
    procurement_quick, 
    reserve, 
    get_precedents, 
    CorridorRequest, 
    PrecedentRequest
)

router = APIRouter()

@router.post("/dashboard/state")
def get_dashboard_state(req: CorridorRequest):
    """
    Aggregates all necessary data for the Drishti Dashboard in a single request,
    reducing frontend polling overhead significantly.
    """
    try:
        corridors_data = get_risk_corridors()
        scenario_data = scenario_quick(req)
        procurement_data = procurement_quick(req)
        reserve_data = reserve(req.corridor)
        precedents_data = get_precedents(PrecedentRequest(query=f"Severe supply chain disruption and escalation in {req.corridor}"))
        
        return {
            "corridors_data": corridors_data,
            "scenario_data": scenario_data,
            "procurement_data": procurement_data,
            "reserve_data": reserve_data,
            "precedents_data": precedents_data
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
