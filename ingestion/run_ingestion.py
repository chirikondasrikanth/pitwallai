"""
ingestion/run_ingestion.py
Master entry point for the F1 Data Ingestion Engine.

Usage:
  python ingestion/run_ingestion.py --setup          # init DB + seed all data
  python ingestion/run_ingestion.py --sync           # sync CSV → DB
  python ingestion/run_ingestion.py --expert         # ingest sample expert insights
  python ingestion/run_ingestion.py --schedule       # start auto-scheduler
  python ingestion/run_ingestion.py --status         # show DB status & ingestion log
  python ingestion/run_ingestion.py --all            # run full pipeline
"""

import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def cmd_setup():
    print("\n" + "="*60)
    print("  F1 INGESTION ENGINE — DATABASE SETUP")
    print("="*60)

    from ingestion.db.schema import init_db, get_engine
    from ingestion.db.seeder import seed_all, get_session

    print("\n→ Initializing database...")
    engine = init_db(get_engine())
    session = get_session(engine)
    print("  ✅ Tables created")

    print("→ Seeding reference data...")
    seed_all(session)

    print("→ Syncing race results from CSV...")
    from ingestion.scrapers.race_ingester import RaceIngester
    ingester = RaceIngester()
    result = ingester.ingest_from_platform_csv(triggered_by="setup")
    stats = result.get("stats", {})
    print(f"  ✅ Synced: +{stats.get('inserted',0)} inserted, {stats.get('updated',0)} updated")

    print("\n✅ Database setup complete!")
    cmd_status()


def cmd_sync():
    print("\n→ Syncing CSV → Database...")
    from ingestion.scrapers.race_ingester import RaceIngester
    ingester = RaceIngester()
    result = ingester.ingest_from_platform_csv(triggered_by="manual_sync")
    print(f"  Result: {result}")


def cmd_expert():
    print("\n→ Ingesting expert insights...")
    from ingestion.scrapers.expert_ingester import ExpertIngester, SAMPLE_EXPERT_INSIGHTS
    ingester = ExpertIngester()
    result = ingester.ingest_batch(SAMPLE_EXPERT_INSIGHTS)
    print(f"  ✅ {result['success']}/{result['total']} insights ingested")

    print("\n→ Driver Sentiment Summary:")
    summary = ingester.get_driver_sentiment_summary()
    for driver, data in list(summary.items())[:8]:
        bar = "█" * int(data['avg_confidence'] * 10)
        print(f"  {driver:<22} [{bar:<10}] conf={data['avg_confidence']:.2f} | "
              f"😊{data['positive']} 😐{data['neutral']} 😟{data['negative']}")


def cmd_status():
    print("\n" + "="*60)
    print("  DATABASE STATUS")
    print("="*60)

    try:
        from ingestion.db.schema import (
            get_session, get_engine, init_db,
            Driver, Team, Circuit, Race,
            RaceResult, ExpertPrediction, Regulation, IngestionLog
        )
        engine = init_db(get_engine())
        session = get_session(engine)

        tables = {
            "Drivers":            session.query(Driver).count(),
            "Teams":              session.query(Team).count(),
            "Circuits":           session.query(Circuit).count(),
            "Races (all)":        session.query(Race).count(),
            "Races (2026)":       session.query(Race).filter_by(season=2026).count(),
            "Race Results":       session.query(RaceResult).count(),
            "Expert Predictions": session.query(ExpertPrediction).count(),
            "Regulations":        session.query(Regulation).count(),
            "Ingestion Logs":     session.query(IngestionLog).count(),
        }

        print()
        for table, count in tables.items():
            bar = "█" * min(count, 30)
            print(f"  {table:<22} {count:>5}  {bar}")

        print("\n  Recent Ingestion Log:")
        logs = session.query(IngestionLog)\
            .order_by(IngestionLog.timestamp.desc()).limit(5).all()
        for log in logs:
            icon = "✅" if log.status == "success" else "❌"
            print(f"  {icon} {str(log.timestamp)[:19]} | {log.data_type:<15} | "
                  f"+{log.rows_inserted} rows | {log.triggered_by}")

    except Exception as e:
        print(f"  ⚠️  Could not read DB status: {e}")
        print("  Run: python ingestion/run_ingestion.py --setup")

    # CSV status
    print("\n  CSV Dataset Status:")
    csv_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
    if os.path.exists(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        print(f"  cleaned_race_data.csv: {len(df)} rows | "
              f"{df['season'].nunique()} seasons | "
              f"{df['driver'].nunique()} drivers")
        df26 = df[df["season"] == 2026]
        print(f"  2026 data: {len(df26)} entries | "
              f"{df26['round'].nunique()} completed race(s)")
    else:
        print("  ⚠️  cleaned_race_data.csv not found — run setup.py first")

    print()


def cmd_schedule():
    from ingestion.schedulers.auto_updater import run_scheduler
    run_scheduler()


def cmd_nlp_demo():
    """Demo the NLP extraction on sample F1 expert quotes."""
    print("\n" + "="*60)
    print("  NLP EXTRACTION DEMO")
    print("="*60)

    from ingestion.nlp.expert_extractor import ExpertExtractor

    samples = [
        "Mercedes have clearly found a massive power advantage in 2026. Russell will win the championship.",
        "Ferrari's start procedure is revolutionary — Hamilton and Leclerc are unbeatable off the line.",
        "Verstappen is really struggling. Red Bull have a fundamental problem with energy deployment.",
        "McLaren appears strong at Monaco. Norris could challenge for pole in high-downforce conditions.",
        "Antonelli might surprise everyone at Suzuka — the kid has incredible natural pace.",
    ]

    extractor = ExpertExtractor()
    for text in samples:
        r = extractor.extract(text)
        print(f"\n  Input: \"{text[:70]}...\"")
        print(f"  → Driver:     {r['driver_name']} | Team: {r['team_name']}")
        print(f"  → Prediction: {r['prediction_text']}")
        print(f"  → Sentiment:  {r['sentiment']} ({r['sentiment_score']:+.2f}) | "
              f"Confidence: {r['confidence_score']:.2f}")


def cmd_reasoning():
    print("\n" + "="*60)
    print("  LLM REASONING ENGINE DEMO")
    print("="*60)
    from ingestion.llm_reasoning import LLMReasoning
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY","")
    reasoner = LLMReasoning(api_key=api_key)
    engine_type = "Claude API" if reasoner.has_api else "Rule-based engine"
    print(f"\nUsing: {engine_type}")

    mock = {
        "circuit": "Japanese Grand Prix", "weather": "Dry",
        "winner": {"driver":"George Russell","team":"Mercedes",
                   "win_prob":0.22,"podium_prob":0.78,"qualifying_position":1,"predicted_rank":1},
        "top_10": [
            {"driver":"George Russell", "team":"Mercedes",    "predicted_rank":1,"win_prob":0.22,"podium_prob":0.78,"qualifying_position":1},
            {"driver":"Charles Leclerc","team":"Ferrari",     "predicted_rank":2,"win_prob":0.18,"podium_prob":0.72,"qualifying_position":3},
            {"driver":"Max Verstappen", "team":"Red Bull",    "predicted_rank":3,"win_prob":0.15,"podium_prob":0.60,"qualifying_position":2},
            {"driver":"Lewis Hamilton", "team":"Ferrari",     "predicted_rank":4,"win_prob":0.12,"podium_prob":0.45,"qualifying_position":5},
            {"driver":"Lando Norris",   "team":"McLaren",     "predicted_rank":5,"win_prob":0.10,"podium_prob":0.38,"qualifying_position":4},
        ],
        "underdogs": [{"driver":"Fernando Alonso","qualifying_position":9,"podium_prob":0.12}],
    }

    exp = reasoner.explain_race_prediction("Japanese Grand Prix", mock, "Dry")
    print(f"\n{exp['race_preview']}")
    print(f"\n{exp['winner_reasoning']}")
    print(f"\nConfidence: {exp['confidence_level']} -- {exp['confidence_reason']}")
    print(f"\nDriver Summaries:")
    for d, s in list(exp.get("driver_summaries",{}).items())[:5]:
        print(f"   {d:<22} -> {s}")


def cmd_sync_api():
    print("\n" + "="*60)
    print("  AUTO-SYNC — FETCHING FROM F1 API")
    print("="*60)

    from ingestion.scrapers.auto_sync import AutoSync
    sync = AutoSync()

    print("\n-> Checking sync status...")
    status = sync.get_sync_status()
    for season in [2024, 2025, 2026]:
        info = status.get(season, {})
        if isinstance(info, dict):
            print(f"  {season}: {info.get('count', 0)} races in dataset")

    missing = status.get("missing_2026", [])
    if missing:
        print(f"\n-> Found {len(missing)} unsynced 2026 race(s): {missing}")
        print("-> Fetching from API...")
        result = sync.check_and_sync(2026)
        print(f"\n  [OK] Synced: {result['synced']}/{result['total']} races")
        if result.get("retrained"):
            print("  [OK] Models retrained with new data")
    else:
        print("\n  [OK] All completed races already in dataset -- nothing to sync")

    cmd_status()


def cmd_api_status():
    print("\n" + "="*60)
    print("  API & DATASET STATUS")
    print("="*60)

    from ingestion.scrapers.auto_sync import AutoSync
    from ingestion.scrapers.f1_api_client import F1APIClient

    sync   = AutoSync()
    client = F1APIClient()

    status = sync.get_sync_status()
    print()
    for season in [2024, 2025, 2026]:
        info   = status.get(season, {})
        rounds = info.get("rounds_in_dataset", [])
        bar    = "#" * len(rounds)
        print(f"  {season}  [{bar:<24}] {len(rounds):>2} races  {rounds[:5]}{'...' if len(rounds)>5 else ''}")

    missing = status.get("missing_2026", [])
    print(f"\n  Missing 2026 rounds: {missing if missing else 'None -- up to date'}")
    print("\n  API Sources:")
    print("  -> OpenF1  (https://api.openf1.org)  -- real-time, free")
    print("  -> Ergast   (http://ergast.com/api/f1) -- historical, free")
    print("  -> Local cache (data/api_cache/)       -- previously fetched")
    print("  -> Built-in verified results           -- 2026 R1 Australian GP")

    cache_dir = os.path.join(BASE_DIR, "data", "api_cache")
    if os.path.exists(cache_dir):
        cached = os.listdir(cache_dir)
        print(f"\n  Cached API responses: {len(cached)} files")
    print()


def cmd_feature_store():
    print("\n" + "="*60)
    print("  BUILDING FEATURE STORE")
    print("="*60)
    from ingestion.feature_store import FeatureStore
    store = FeatureStore()
    df = store.build()

    print("\n📊 Top 10 drivers by Combined Performance Index (2026):")
    df_2026 = df[df["season"] == 2026].sort_values(
        "combined_performance_index", ascending=False
    ).drop_duplicates("driver")
    cols = ["driver","team","combined_performance_index",
            "expert_confidence_score","reg_combined_impact","driver_form_momentum_score"]
    print(df_2026[cols].head(10).to_string(index=False))



    """Auto-detect and sync missing race results from API."""
    print("\n" + "="*60)
    print("  AUTO-SYNC — FETCHING FROM F1 API")
    print("="*60)

    from ingestion.scrapers.auto_sync import AutoSync
    sync = AutoSync()

    print("\n→ Checking sync status...")
    status = sync.get_sync_status()
    for season in [2024, 2025, 2026]:
        info = status.get(season, {})
        if isinstance(info, dict):
            print(f"  {season}: {info.get('count', 0)} races in dataset")

    missing = status.get("missing_2026", [])
    if missing:
        print(f"\n→ Found {len(missing)} unsynced 2026 race(s): {missing}")
        print("→ Fetching from API...")
        result = sync.check_and_sync(2026)
        print(f"\n  ✅ Synced: {result['synced']}/{result['total']} races")
        if result.get("retrained"):
            print("  ✅ Models retrained with new data")
    else:
        print("\n  ✅ All completed races already in dataset — nothing to sync")

    cmd_status()


def cmd_api_status():
    """Show what races are available from API vs what's in dataset."""
    print("\n" + "="*60)
    print("  API & DATASET STATUS")
    print("="*60)

    from ingestion.scrapers.auto_sync import AutoSync
    from ingestion.scrapers.f1_api_client import F1APIClient

    sync   = AutoSync()
    client = F1APIClient()

    status = sync.get_sync_status()
    print()
    for season in [2024, 2025, 2026]:
        info = status.get(season, {})
        rounds = info.get("rounds_in_dataset", [])
        bar = "█" * len(rounds)
        print(f"  {season}  [{bar:<24}] {len(rounds):>2} races  {rounds[:5]}{'...' if len(rounds)>5 else ''}")

    missing = status.get("missing_2026", [])
    print(f"\n  Missing 2026 rounds: {missing if missing else 'None — up to date ✅'}")

    print("\n  API Sources:")
    print("  → OpenF1  (https://api.openf1.org)  — real-time, free")
    print("  → Ergast   (http://ergast.com/api/f1) — historical, free")
    print("  → Local cache (data/api_cache/)       — previously fetched")
    print("  → Built-in verified results           — 2026 R1 Australian GP")

    cache_dir = os.path.join(BASE_DIR, "data", "api_cache")
    if os.path.exists(cache_dir):
        cached = os.listdir(cache_dir)
        print(f"\n  Cached API responses: {len(cached)} files")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="F1 Data Ingestion Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  --setup       Initialize DB, seed all reference data, sync CSV results
  --sync        Sync cleaned_race_data.csv → relational database
  --sync-api    Auto-detect & fetch missing race results from F1 APIs
  --expert      Ingest sample expert insights with NLP extraction
  --status      Show database row counts and recent ingestion log
  --api-status  Show API sources and what races are missing
  --schedule    Start auto-scheduler (runs in background)
  --nlp         Demo NLP extraction on sample F1 expert quotes
  --all         Run setup + expert + status
        """
    )
    parser.add_argument("--setup",      action="store_true")
    parser.add_argument("--sync",       action="store_true")
    parser.add_argument("--sync-api",   action="store_true")
    parser.add_argument("--features",   action="store_true")
    parser.add_argument("--reasoning",  action="store_true")
    parser.add_argument("--expert",     action="store_true")
    parser.add_argument("--status",     action="store_true")
    parser.add_argument("--api-status", action="store_true")
    parser.add_argument("--schedule",   action="store_true")
    parser.add_argument("--nlp",        action="store_true")
    parser.add_argument("--all",        action="store_true")
    args = parser.parse_args()

    if args.all:
        cmd_setup()
        cmd_expert()
        cmd_feature_store()
        cmd_nlp_demo()
        cmd_status()
    elif args.setup:
        cmd_setup()
    elif args.sync:
        cmd_sync()
    elif getattr(args, "sync_api", False):
        cmd_sync_api()
    elif getattr(args, "features", False):
        cmd_feature_store()
    elif getattr(args, "reasoning", False):
        cmd_reasoning()
    elif args.expert:
        cmd_expert()
    elif args.status:
        cmd_status()
    elif getattr(args, "api_status", False):
        cmd_api_status()
    elif args.schedule:
        cmd_schedule()
    elif args.nlp:
        cmd_nlp_demo()
    else:
        cmd_status()
        print("Run with --help for all options")
