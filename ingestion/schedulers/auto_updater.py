"""
ingestion/schedulers/auto_updater.py
Automated update system — runs scheduled jobs for:
  - Post-race result ingestion
  - Daily data freshness checks  
  - Season calendar updates
  - Model retraining triggers

Uses 'schedule' library (lightweight) or APScheduler (production).
Run this as a background process: python ingestion/schedulers/auto_updater.py
"""

import os
import sys
import time
import logging
import json
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import schedule

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                         "data", "ingestion.log"),
            mode="a"
        ),
    ]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# ─── RACE CALENDAR (2026) ─────────────────────────────────────────
RACE_CALENDAR_2026 = [
    {"round": 1,  "name": "Australian Grand Prix",     "date": "2026-03-08", "status": "completed"},
    {"round": 2,  "name": "Chinese Grand Prix",        "date": "2026-03-15", "status": "completed"},
    {"round": 3,  "name": "Japanese Grand Prix",       "date": "2026-03-29", "status": "scheduled"},
    {"round": 4,  "name": "Bahrain Grand Prix",        "date": "2026-04-12", "status": "scheduled"},
    {"round": 5,  "name": "Saudi Arabian Grand Prix",  "date": "2026-04-19", "status": "scheduled"},
    {"round": 6,  "name": "Miami Grand Prix",          "date": "2026-05-03", "status": "scheduled"},
    {"round": 7,  "name": "Emilia Romagna Grand Prix", "date": "2026-05-17", "status": "scheduled"},
    {"round": 8,  "name": "Monaco Grand Prix",         "date": "2026-05-24", "status": "scheduled"},
    {"round": 9,  "name": "Spanish Grand Prix",        "date": "2026-06-01", "status": "scheduled"},
    {"round": 10, "name": "Canadian Grand Prix",       "date": "2026-06-15", "status": "scheduled"},
]


def get_next_race() -> dict:
    today = date.today().isoformat()
    upcoming = [r for r in RACE_CALENDAR_2026
                if r["date"] >= today and r["status"] == "scheduled"]
    return upcoming[0] if upcoming else None


def get_races_needing_update() -> list:
    today = date.today().isoformat()
    return [r for r in RACE_CALENDAR_2026
            if r["date"] <= today and r["status"] == "scheduled"]


# ─── JOB FUNCTIONS ────────────────────────────────────────────────

def job_check_race_results():
    """
    Check if any scheduled race date has passed and trigger ingestion.
    Run daily at 10:00 UTC.
    """
    logger.info("⏰ [SCHEDULER] Checking for new race results...")

    races_pending = get_races_needing_update()
    if not races_pending:
        logger.info("   No new races to process today.")
        return

    for race in races_pending:
        logger.info(f"   Found pending race: Round {race['round']} — {race['name']}")
        _trigger_race_ingestion(race)


def _trigger_race_ingestion(race: dict):
    """
    Trigger ingestion for a completed race.
    In production: would call FastF1 API or Ergast API.
    Currently: syncs from platform CSV.
    """
    try:
        from ingestion.scrapers.race_ingester import RaceIngester
        ingester = RaceIngester()
        result = ingester.ingest_from_platform_csv(triggered_by="scheduler")
        logger.info(f"   ✅ Race ingestion complete: {result['stats']}")

        # Mark as completed in calendar
        for r in RACE_CALENDAR_2026:
            if r["round"] == race["round"]:
                r["status"] = "completed"

        # Trigger model retraining
        _trigger_model_retrain(race)

    except Exception as e:
        logger.error(f"   ❌ Race ingestion failed for {race['name']}: {e}")


def _trigger_model_retrain(race: dict):
    """Retrain ML models after new race data is ingested."""
    try:
        logger.info(f"   🔄 Triggering model retrain after {race['name']}...")
        clean_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
        if not os.path.exists(clean_path):
            logger.warning("   cleaned_race_data.csv not found — skipping retrain")
            return

        from src.train_model import train_pipeline
        _, _, _, _, metrics = train_pipeline(clean_path)
        logger.info(f"   ✅ Models retrained | "
                    f"Podium AUC: {metrics.get('podium_auc',0):.3f} | "
                    f"Position MAE: {metrics.get('position_mae',0):.2f}")
    except Exception as e:
        logger.error(f"   ❌ Model retrain failed: {e}")


def job_data_freshness_check():
    """
    Daily data freshness check — verifies dataset integrity.
    Run daily at 08:00 UTC.
    """
    logger.info("⏰ [SCHEDULER] Running data freshness check...")
    try:
        import pandas as pd
        clean_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
        if not os.path.exists(clean_path):
            logger.warning("   ⚠️  cleaned_race_data.csv not found")
            return

        df = pd.read_csv(clean_path)
        season_2026 = df[df["season"] == 2026]

        logger.info(f"   Dataset: {len(df)} total rows")
        logger.info(f"   2026 races loaded: {season_2026['round'].nunique()}")
        logger.info(f"   Latest round: {season_2026['round'].max() if not season_2026.empty else 'N/A'}")

        # Check for missing values in key columns
        key_cols = ["driver","team","finish_position","qualifying_position"]
        for col in key_cols:
            if col in df.columns:
                null_pct = df[col].isnull().mean() * 100
                if null_pct > 5:
                    logger.warning(f"   ⚠️  {col} has {null_pct:.1f}% missing values")

        logger.info("   ✅ Data freshness check complete")

    except Exception as e:
        logger.error(f"   ❌ Freshness check failed: {e}")


def job_sync_db():
    """
    Sync CSV data to relational database.
    Run every 6 hours.
    """
    logger.info("⏰ [SCHEDULER] Syncing CSV → Database...")
    try:
        from ingestion.scrapers.race_ingester import RaceIngester
        ingester = RaceIngester()
        result = ingester.ingest_from_platform_csv(triggered_by="scheduler_sync")
        logger.info(f"   ✅ DB sync complete: {result.get('stats', {})}")
    except Exception as e:
        logger.error(f"   ❌ DB sync failed: {e}")


def job_next_race_preview():
    """
    Log next race preview — useful for triggering prediction reports.
    Run every Monday.
    """
    next_race = get_next_race()
    if next_race:
        days_away = (
            datetime.strptime(next_race["date"], "%Y-%m-%d").date() - date.today()
        ).days
        logger.info(f"⏰ [SCHEDULER] Next race: Round {next_race['round']} — "
                    f"{next_race['name']} in {days_away} days ({next_race['date']})")


# ─── SCHEDULER SETUP ──────────────────────────────────────────────

def setup_schedule():
    """Configure all scheduled jobs."""
    # Daily at 08:00 — freshness check
    schedule.every().day.at("08:00").do(job_data_freshness_check)

    # Daily at 10:00 — check for new race results
    schedule.every().day.at("10:00").do(job_check_race_results)

    # Every 6 hours — sync to DB
    schedule.every(6).hours.do(job_sync_db)

    # Every Monday — next race preview
    schedule.every().monday.at("07:00").do(job_next_race_preview)

    logger.info("✅ Scheduler configured:")
    logger.info("   08:00 daily  → Data freshness check")
    logger.info("   10:00 daily  → Race result check + auto-ingest")
    logger.info("   Every 6h     → CSV → DB sync")
    logger.info("   Every Monday → Next race preview")


def run_scheduler():
    """Start the scheduler loop — runs indefinitely."""
    setup_schedule()

    # Run all jobs once immediately on startup
    logger.info("\n🚀 Running startup jobs...")
    job_data_freshness_check()
    job_next_race_preview()
    job_sync_db()

    logger.info("\n⏰ Scheduler running... (Press Ctrl+C to stop)\n")
    while True:
        schedule.run_pending()
        time.sleep(60)


def run_once(job: str = "all"):
    """Run a specific job once — for testing or manual triggers."""
    jobs = {
        "check": job_check_race_results,
        "freshness": job_data_freshness_check,
        "sync": job_sync_db,
        "preview": job_next_race_preview,
    }
    if job == "all":
        for fn in jobs.values():
            fn()
    elif job in jobs:
        jobs[job]()
    else:
        logger.error(f"Unknown job: {job}. Options: {list(jobs.keys())}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="F1 Data Ingestion Scheduler")
    parser.add_argument("--mode", choices=["run", "once", "check", "freshness", "sync"],
                        default="once", help="Scheduler mode")
    args = parser.parse_args()

    if args.mode == "run":
        run_scheduler()
    else:
        run_once(args.mode if args.mode != "once" else "all")
