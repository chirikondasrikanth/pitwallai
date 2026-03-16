"""
ingestion/scrapers/auto_sync.py
Automatic post-race sync pipeline.

After each Grand Prix:
1. Detects completed races not yet in DB
2. Fetches results from API (OpenF1 → Ergast → known data)
3. Saves to CSV + relational DB
4. Triggers model retraining
5. Logs everything

Run manually: python ingestion/scrapers/auto_sync.py
Or via scheduler: python ingestion/run_ingestion.py --schedule
"""

import os
import sys
import time
import logging
import pandas as pd
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ingestion.scrapers.f1_api_client import F1APIClient
from ingestion.scrapers.race_ingester import RaceIngester
from ingestion.db.schema import get_session, get_engine, init_db, Race

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_CSV  = os.path.join(BASE_DIR, "data", "raw_race_data.csv")
CLEAN_CSV = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")


class AutoSync:

    def __init__(self):
        self.api      = F1APIClient()
        self.ingester = RaceIngester()
        self.session  = self.ingester.session

    def get_missing_rounds(self, season: int = 2026) -> list:
        """Find rounds that are completed but not yet in CSV."""
        completed_api = self.api.get_completed_races_this_season(season)

        # Check what's already in CSV
        existing_rounds = []
        if os.path.exists(CLEAN_CSV):
            df = pd.read_csv(CLEAN_CSV)
            season_df = df[df["season"] == season]
            existing_rounds = season_df["round"].dropna().astype(int).unique().tolist()

        missing = [r for r in completed_api if r not in existing_rounds]
        logger.info(f"Season {season}: completed={completed_api}, existing={existing_rounds}, missing={missing}")
        return missing

    def sync_round(self, season: int, round_number: int,
                   retrain: bool = True) -> dict:
        """
        Full sync for one race round:
        API fetch → format → save CSV → ingest DB → retrain
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"Syncing {season} Round {round_number}...")
        logger.info(f"{'='*50}")

        result = {
            "season": season, "round": round_number,
            "success": False, "source": None,
            "rows": 0, "retrained": False,
        }

        # Step 1: Fetch from API
        df = self.api.fetch_and_format_for_platform(season, round_number)

        if df.empty:
            logger.warning(f"No data returned for {season} R{round_number}")
            return result

        result["rows"] = len(df)
        result["source"] = "api"

        # Step 2: Append to raw CSV
        if os.path.exists(RAW_CSV):
            existing = pd.read_csv(RAW_CSV)
            # Remove any existing rows for this race
            existing = existing[
                ~((existing["season"] == season) &
                  (existing["round"] == round_number))
            ]
            combined = pd.concat([existing, df], ignore_index=True)
        else:
            combined = df

        combined.to_csv(RAW_CSV, index=False)
        logger.info(f"  Saved to raw CSV: {len(df)} rows")

        # Step 3: Clean data
        from src.data_cleaner import clean_dataset
        clean_df = clean_dataset(RAW_CSV, CLEAN_CSV)
        logger.info(f"  Cleaned dataset: {len(clean_df)} total rows")

        # Step 4: Rebuild feature store
        from ingestion.feature_store import FeatureStore
        store = FeatureStore()
        store.build()

        # Step 5: Ingest into relational DB
        ingest_result = self.ingester.ingest_race_results(
            df, season=season, round_number=round_number,
            triggered_by="auto_sync"
        )
        logger.info(f"  DB ingest: {ingest_result.get('stats', {})}")

        result["success"] = True

        # Step 6: Retrain models
        if retrain:
            result["retrained"] = self._retrain_models()

        logger.info(f"✅ Sync complete for {season} R{round_number}")
        return result

    def sync_all_missing(self, season: int = 2026,
                          retrain_after_all: bool = True) -> dict:
        """Sync all rounds that are completed but missing from dataset."""
        missing = self.get_missing_rounds(season)

        if not missing:
            logger.info(f"✅ All completed {season} races already synced")
            return {"synced": 0, "rounds": []}

        logger.info(f"Found {len(missing)} rounds to sync: {missing}")

        results = []
        for round_num in missing:
            # Don't retrain after each round, only at the end
            r = self.sync_round(season, round_num, retrain=False)
            results.append(r)
            time.sleep(1)  # Be nice to API

        # Retrain once after all syncs
        retrained = False
        if retrain_after_all and any(r["success"] for r in results):
            retrained = self._retrain_models()

        return {
            "synced": sum(1 for r in results if r["success"]),
            "total": len(missing),
            "rounds": missing,
            "retrained": retrained,
            "results": results,
        }

    def check_and_sync(self, season: int = 2026) -> dict:
        """
        Main entry point — called by scheduler.
        Checks for new completed races and syncs them.
        """
        logger.info(f"🔄 Auto-sync check for {season} season...")

        summary = self.sync_all_missing(season)

        if summary["synced"] > 0:
            logger.info(f"✅ Synced {summary['synced']} new race(s): {summary['rounds']}")
        else:
            logger.info(f"✅ Dataset up to date — no new races to sync")

        return summary

    def add_race_result_manually(self, season: int, round_number: int,
                                  results_data: list) -> dict:
        """
        Manually add a race result when API is unavailable.
        results_data: list of dicts with driver, team, finish_position etc.
        """
        df = pd.DataFrame(results_data)
        df["season"] = season
        df["round"] = round_number

        # Normalize
        from src.smart_ingest import normalize_df
        df = normalize_df(df)

        return self.sync_round_from_df(df, season, round_number)

    def sync_round_from_df(self, df: pd.DataFrame, season: int,
                            round_number: int, retrain: bool = True) -> dict:
        """Sync from a pre-built DataFrame (used by dashboard upload)."""
        df["season"] = season
        df["round"] = round_number

        if os.path.exists(RAW_CSV):
            existing = pd.read_csv(RAW_CSV)
            existing = existing[
                ~((existing["season"] == season) &
                  (existing["round"] == round_number))
            ]
            combined = pd.concat([existing, df], ignore_index=True)
        else:
            combined = df

        combined.to_csv(RAW_CSV, index=False)

        from src.data_cleaner import clean_dataset
        clean_df = clean_dataset(RAW_CSV, CLEAN_CSV)

        self.ingester.ingest_race_results(
            df, season=season, round_number=round_number,
            triggered_by="manual_upload"
        )

        retrained = self._retrain_models() if retrain else False

        return {
            "success": True,
            "rows": len(df),
            "total_dataset": len(clean_df),
            "retrained": retrained,
        }

    def get_sync_status(self) -> dict:
        """Show current sync status — what's in DB vs what should be there."""
        status = {}

        for season in [2024, 2025, 2026]:
            if os.path.exists(CLEAN_CSV):
                df = pd.read_csv(CLEAN_CSV)
                season_df = df[df["season"] == season]
                rounds_in_csv = sorted(season_df["round"].dropna().astype(int).unique().tolist())
            else:
                rounds_in_csv = []

            status[season] = {
                "rounds_in_dataset": rounds_in_csv,
                "count": len(rounds_in_csv),
            }

        # Check for completed 2026 races not yet synced
        missing = self.get_missing_rounds(2026)
        status["missing_2026"] = missing
        status["up_to_date"] = len(missing) == 0

        return status

    def _retrain_models(self) -> bool:
        """Trigger model retraining after new data."""
        try:
            logger.info("  🔄 Retraining ML models...")
            from src.train_model import train_pipeline
            _, _, _, _, metrics = train_pipeline(CLEAN_CSV)
            logger.info(f"  ✅ Models retrained | "
                        f"Podium AUC: {metrics.get('podium_auc',0):.3f} | "
                        f"MAE: {metrics.get('position_mae',0):.2f}")
            return True
        except Exception as e:
            logger.error(f"  ❌ Retrain failed: {e}")
            return False


if __name__ == "__main__":
    sync = AutoSync()

    print("\n=== Auto-Sync Status ===")
    status = sync.get_sync_status()
    for season, info in status.items():
        if isinstance(info, dict) and "count" in info:
            print(f"  {season}: {info['count']} races in dataset {info['rounds_in_dataset']}")
    print(f"  Missing 2026 rounds: {status.get('missing_2026', [])}")
    print(f"  Up to date: {status.get('up_to_date', False)}")

    print("\n=== Running Auto-Sync ===")
    result = sync.check_and_sync(2026)
    print(f"  Synced: {result['synced']} rounds")
    print(f"  Retrained: {result.get('retrained', False)}")
