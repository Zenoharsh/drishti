import os
from datetime import date, timedelta, datetime, timezone
from fastapi import APIRouter, Header, HTTPException
from src.config.db import get_db
from src.services import feed_parser, gemini_engine
from src.services.calculators import (
    count_vessels_near, ais_density_norm, price_delta_norm, fuse_disruption_score,
)

router = APIRouter()

_last_poll_status = {
    "last_poll_time": None,
    "fetched": 0,
    "passed_filter": 0,
    "processed_by_gemini": 0,
}


def _check_secret(x_ingest_secret: str | None):
    expected = os.environ.get("INGEST_SECRET")
    if not expected or x_ingest_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Ingest-Secret header")


@router.post("/ingest/poll")
def ingest_poll(x_ingest_secret: str | None = Header(default=None)):
    _check_secret(x_ingest_secret)
    db = get_db()

    # 1-3: fetch, filter, dedup (all before any Gemini call)
    raw_entries = feed_parser.fetch_candidate_entries()
    relevant = feed_parser.filter_relevant(raw_entries)
    new_entries = feed_parser.dedup_against_db(relevant)
    inserted = feed_parser.insert_headlines(new_entries)

    # Fetch ALL unprocessed headlines from the database (including our injected crisis)
    unprocessed = db.table("headlines").select("*").eq("processed", False).execute().data

    processed_count = 0
    for headline in unprocessed:
        try:
            extraction = gemini_engine.extract_risk_signal(headline["title"])
        except Exception as e:
            print(f"Gemini extraction failed for headline: {headline['title']} - Error: {e}")
            continue  # one bad extraction shouldn't kill the whole poll

        corridor_id = extraction.corridor
        corridor_row = db.table("corridors").select("*").eq("id", corridor_id).execute().data
        if not corridor_row:
            continue
        corridor = corridor_row[0]

        # Signal 2: sanctions
        sanctioned = db.table("sanctions_registry").select("entity_name").execute().data
        sanctioned_names = {s["entity_name"].lower() for s in sanctioned}
        sanctions_flag = 1.0 if any(
            e.lower() in sanctioned_names for e in extraction.entities
        ) else 0.0

        # Signal 3: price delta, trailing 3 days
        prices = (db.table("commodity_prices")
                  .select("price_usd, price_date")
                  .gte("price_date", str(date.today() - timedelta(days=3)))
                  .order("price_date")
                  .execute().data)
        price_values = [p["price_usd"] for p in prices]
        price_norm = price_delta_norm(price_values) if len(price_values) >= 2 else 0.0

        # Signal 4: AIS density
        vessels = (db.table("vessels").select("lat, lon")
                   .eq("corridor_id", corridor_id).execute().data)
        current_count = count_vessels_near(corridor, vessels)
        ais_norm = ais_density_norm(current_count, corridor["baseline_vessel_count"])

        # Fuse and store
        score = fuse_disruption_score(extraction.severity, sanctions_flag, price_norm, ais_norm)
        db.table("risk_snapshots").insert({
            "corridor_id": corridor_id,
            "disruption_score": round(score, 4),
            "severity": extraction.severity,
            "sanctions_flag": sanctions_flag,
            "price_delta_norm": price_norm,
            "ais_density_norm": ais_norm,
        }).execute()

        db.table("headlines").update({"processed": True}).eq("id", headline["id"]).execute()
        processed_count += 1

    _last_poll_status["last_poll_time"] = datetime.now(timezone.utc).isoformat()
    _last_poll_status["fetched"] = len(raw_entries)
    _last_poll_status["passed_filter"] = len(relevant)
    _last_poll_status["processed_by_gemini"] = processed_count

    return {
        "fetched": len(raw_entries),
        "passed_filter": len(relevant),
        "new_after_dedup": len(new_entries),
        "processed_by_gemini": processed_count,
    }


@router.get("/ingest/status")
def ingest_status():
    return _last_poll_status
