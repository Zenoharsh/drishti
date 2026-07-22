import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.config.db import get_db
from src.routes.ingest import ingest_poll
import os
import logging

logger = logging.getLogger(__name__)

def update_commodity_prices():
    """Fetch live WTI and Brent crude spot prices using yfinance and update the crude_assay_specs table."""
    logger.info("Fetching live commodity prices...")
    try:
        wti = yf.Ticker("CL=F")
        brent = yf.Ticker("BZ=F")
        
        wti_price = wti.history(period="1d")["Close"].iloc[-1]
        brent_price = brent.history(period="1d")["Close"].iloc[-1]
        
        db = get_db()
        # Update WTI sources
        db.table("crude_assay_specs").update({"current_spot_price_usd": float(wti_price)}).eq("id", "src_usa_wti").execute()
        # Update Brent/Bonny Light sources (approximate using Brent)
        db.table("crude_assay_specs").update({"current_spot_price_usd": float(brent_price)}).eq("id", "src_nga_bonny").execute()
        db.table("crude_assay_specs").update({"current_spot_price_usd": float(brent_price)}).eq("id", "src_ago_cabinda").execute()
        
        logger.info(f"Updated crude prices: WTI=${wti_price:.2f}, Brent=${brent_price:.2f}")
    except Exception as e:
        logger.error(f"Failed to fetch commodity prices: {e}")

def run_intelligence_ingestion():
    """Run the tinyfish intelligence polling and Gemini processing."""
    logger.info("Running intelligence ingestion poll...")
    try:
        secret = os.environ.get("INGEST_SECRET", "df6d782e5781041d55a476ccd1b0951e")
        result = ingest_poll(x_ingest_secret=secret)
        logger.info(f"Ingestion complete: {result}")
    except Exception as e:
        logger.error(f"Failed intelligence ingestion: {e}")

# Global scheduler instance
scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(update_commodity_prices, IntervalTrigger(minutes=15), id="update_prices", replace_existing=True)
    scheduler.add_job(run_intelligence_ingestion, IntervalTrigger(minutes=5), id="run_ingestion", replace_existing=True)
    
    # Do not run synchronously on startup to avoid deadlocking FastAPI if yfinance hangs.
    scheduler.start()
    logger.info("Background scheduler started.")

def stop_scheduler():
    scheduler.shutdown()
