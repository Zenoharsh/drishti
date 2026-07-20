from fastapi import APIRouter, HTTPException
from src.config.db import get_db

router = APIRouter()


@router.get("/risk/corridors")
def get_risk_corridors():
    """Latest fused disruption score per corridor + its seeded supplier."""
    db = get_db()
    corridors = db.table("corridors").select("*").execute().data

    result = []
    for c in corridors:
        latest = (db.table("risk_snapshots")
                  .select("*")
                  .eq("corridor_id", c["id"])
                  .order("created_at", desc=True)
                  .limit(1)
                  .execute().data)
        result.append({
            "corridor_id": c["id"],
            "corridor_name": c["name"],
            "center_lat": c["center_lat"],
            "center_lon": c["center_lon"],
            "radius_km": c["radius_km"],
            "supplier": c.get("supplier"),
            "disruption_score": latest[0]["disruption_score"] if latest else None,
            "last_updated": latest[0]["created_at"] if latest else None,
        })
    return {"corridors": result}


@router.get("/risk/history/{corridor_id}")
def get_risk_history(corridor_id: str, page: int = 1, page_size: int = 50):
    db = get_db()
    corridor = db.table("corridors").select("*").eq("id", corridor_id).execute().data
    if not corridor:
        raise HTTPException(status_code=404, detail=f"Unknown corridor: {corridor_id}")

    offset = (page - 1) * page_size
    end = offset + page_size - 1

    # Fetch exact count for pagination metadata
    count_res = db.table("risk_snapshots").select("*", count="exact").eq("corridor_id", corridor_id).limit(1).execute()
    total_count = getattr(count_res, 'count', 0) or 0

    history = (db.table("risk_snapshots")
               .select("*")
               .eq("corridor_id", corridor_id)
               .order("created_at", desc=True)
               .range(offset, end)
               .execute().data)

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "corridor_id": corridor_id,
        "metadata": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages
        },
        "history": history
    }
