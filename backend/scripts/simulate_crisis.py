import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
from src.config.db import get_db

def trigger_crisis():
    db = get_db()
    
    print("🚨 Triggering Hormuz Geopolitical Crisis Simulation...")
    time.sleep(1)
    
    # 1. Inject a scary headline
    headline_hormuz = {
        "url": f"https://reuters-mock.com/live-news-hormuz-{int(time.time())}",
        "title": "URGENT: IRGC naval blockade established in Strait of Hormuz. All crude oil transit halted indefinitely. Iranian sanctions severely tightened.",
        "source": "Reuters Simulation",
        "published_at": datetime.utcnow().isoformat(),
        "processed": False
    }
    db.table("headlines").insert(headline_hormuz).execute()
    print("📰 Injected high-severity headline into database.")
    
    # 2. Simulate AIS drop (delete half the vessels in Hormuz)
    vessels = db.table("vessels").select("id").eq("corridor_id", "hormuz").execute().data
    if vessels:
        vessels_to_delete = [v["id"] for v in vessels[:len(vessels)//2]]
        if vessels_to_delete:
            for vid in vessels_to_delete:
                db.table("vessels").delete().eq("id", vid).execute()
            print(f"🚢 Removed {len(vessels_to_delete)} vessels from Hormuz (Simulating AIS diversion).")
            
    # 3. Simulate price spike
    price = {
        "price_date": datetime.utcnow().isoformat(),
        "price_usd": 105.50  # Sudden spike
    }
    db.table("commodity_prices").insert(price).execute()
    print("📈 Injected Brent crude price spike to $105.50.")
            
    print("✅ Raw crisis data injected into database.")
    print("🧠 Waking up Gemini AI Ingestion Engine to process the event...")
    
    from src.routes.ingest import ingest_poll
    try:
        secret = os.environ.get("INGEST_SECRET", "df6d782e5781041d55a476ccd1b0951e")
        result = ingest_poll(x_ingest_secret=secret)
        print(f"✅ AI Analysis complete! Processed {result.get('processed_by_gemini', 0)} headlines.")
    except Exception as e:
        print(f"❌ Failed to wake up ingestion engine: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    trigger_crisis()
