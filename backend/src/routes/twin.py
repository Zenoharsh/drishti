from fastapi import APIRouter, HTTPException
from src.config.db import get_db

router = APIRouter()


@router.get("/twin")
def get_twin():
    """Shared geospatial data layer: all seeded corridors, ports, refineries.
    Read by the frontend for the map, and conceptually the same reference
    data that risk/scenario/procurement/reserve all read internally."""
    db = get_db()
    try:
        corridors = db.table("corridors").select("*").execute().data
        ports = db.table("ports").select("*").execute().data
        refineries = db.table("refineries").select("*").execute().data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load twin data: {e}")

    return {
        "corridors": corridors,
        "ports": ports,
        "refineries": refineries,
    }
