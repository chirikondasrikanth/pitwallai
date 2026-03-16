"""
ingestion/db/data_layer.py
Live database data layer for the Streamlit dashboard.

Replaces CSV reads with live SQLAlchemy queries.
Falls back to CSV if DB unavailable.

All functions mirror the existing dashboard helper signatures
so the dashboard needs minimal changes.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CLEAN_CSV     = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
ENRICHED_CSV  = os.path.join(BASE_DIR, "data", "enriched_features.csv")

# ── DB SESSION (singleton) ─────────────────────────────────────────

_session = None
_engine  = None

def _get_session():
    global _session, _engine
    if _session is None:
        try:
            from ingestion.db.schema import get_session, get_engine, init_db
            _engine  = init_db(get_engine())
            _session = get_session(_engine)
            logger.debug("DB session created")
        except Exception as e:
            logger.warning(f"DB unavailable: {e}")
    return _session


def db_available() -> bool:
    """Check if DB is reachable."""
    try:
        s = _get_session()
        if s is None:
            return False
        from ingestion.db.schema import Driver
        s.query(Driver).limit(1).all()
        return True
    except Exception:
        return False


# ── CORE DATA FUNCTIONS ────────────────────────────────────────────

def load_race_data(season: int = None) -> pd.DataFrame:
    """
    Load race results. Tries enriched CSV first (has all 39 features),
    falls back to clean CSV, then DB.
    """
    # Enriched CSV has the most features — use it if available
    if os.path.exists(ENRICHED_CSV):
        df = pd.read_csv(ENRICHED_CSV)
        return df[df["season"] == season] if season else df

    # Fall back to clean CSV
    if os.path.exists(CLEAN_CSV):
        df = pd.read_csv(CLEAN_CSV)
        return df[df["season"] == season] if season else df

    # Last resort: query DB
    session = _get_session()
    if session is None:
        return pd.DataFrame()

    try:
        from ingestion.db.schema import RaceResult
        from sqlalchemy.orm import joinedload
        query = session.query(RaceResult).options(
            joinedload(RaceResult.driver_obj),
            joinedload(RaceResult.team_obj),
            joinedload(RaceResult.race_obj),
        )
        if season:
            query = query.join(RaceResult.race_obj).filter_by(season=season)

        rows = []
        for r in query.all():
            rows.append({
                "season":               r.race_obj.season if r.race_obj else None,
                "round":                r.race_obj.round_number if r.race_obj else None,
                "circuit":              r.race_obj.race_name if r.race_obj else None,
                "driver":               r.driver_obj.full_name if r.driver_obj else None,
                "team":                 r.team_obj.name if r.team_obj else None,
                "finish_position":      r.finish_position,
                "qualifying_position":  r.grid_position,
                "pole_position":        1 if r.grid_position == 1 else 0,
                "points":               r.points,
                "podium":               1 if r.podium else 0,
                "win":                  1 if r.win else 0,
                "tire_strategy":        r.tire_strategy,
                "pit_stops":            r.pit_stop_count,
                "incidents":            1 if r.incidents else 0,
                "penalties":            r.penalties or 0,
                "status":               r.status,
                "weather":              "Dry",
            })
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"DB query failed: {e}")
        return pd.DataFrame()


def get_season_standings(season: int) -> pd.DataFrame:
    """Driver championship standings for a season."""
    df = load_race_data(season)
    if df.empty:
        return pd.DataFrame()

    standings = df.groupby(["driver", "team"]).agg(
        races    = ("finish_position", "count"),
        wins     = ("win",             "sum"),
        podiums  = ("podium",          "sum"),
        points   = ("points",          "sum"),
        avg_finish = ("finish_position","mean"),
        avg_qual   = ("qualifying_position","mean"),
    ).reset_index()
    standings.sort_values("points", ascending=False, inplace=True)
    standings.reset_index(drop=True, inplace=True)
    standings.index += 1
    return standings


def get_constructor_standings(season: int) -> pd.DataFrame:
    """Constructor championship standings."""
    df = load_race_data(season)
    if df.empty:
        return pd.DataFrame()

    standings = df.groupby("team").agg(
        races    = ("finish_position", "count"),
        wins     = ("win",             "sum"),
        podiums  = ("podium",          "sum"),
        points   = ("points",          "sum"),
        avg_finish = ("finish_position","mean"),
    ).reset_index()
    standings.sort_values("points", ascending=False, inplace=True)
    standings.reset_index(drop=True, inplace=True)
    standings.index += 1
    return standings


def get_driver_stats(driver: str, season: int = None) -> dict:
    """Full driver statistics including enriched features."""
    df = load_race_data()
    if df.empty:
        return {}

    d = df[df["driver"].str.lower().str.contains(
        driver.split()[-1].lower(), na=False
    )]
    if season:
        d = d[d["season"] == season]
    if d.empty:
        return {}

    latest = d.sort_values(["season","round"]).iloc[-1]

    return {
        "races":          len(d),
        "wins":           int(d["win"].sum()),
        "podiums":        int(d["podium"].sum()),
        "poles":          int(d["pole_position"].sum()) if "pole_position" in d.columns else 0,
        "points":         float(d["points"].sum()),
        "avg_finish":     float(d["finish_position"].mean()),
        "avg_qual":       float(d["qualifying_position"].mean()),
        "win_rate":       float(d["win"].mean()),
        "podium_rate":    float(d["podium"].mean()),
        "team":           latest["team"],
        "best_circuits":  d.groupby("circuit")["finish_position"].mean().nsmallest(3).index.tolist(),
        # Enriched features
        "expert_confidence":  float(latest.get("expert_confidence_score", 0.5) or 0.5),
        "expert_sentiment":   float(latest.get("expert_sentiment_score", 0.0) or 0.0),
        "form_momentum":      float(latest.get("driver_form_momentum_score", 0.5) or 0.5),
        "points_momentum":    float(latest.get("points_momentum", 0) or 0),
        "reg_impact":         float(latest.get("reg_combined_impact", 0.5) or 0.5),
        "cpi":                float(latest.get("combined_performance_index", 0.5) or 0.5),
        "h2h_qual":           float(latest.get("h2h_qual_win_rate", 0.5) or 0.5),
        "h2h_race":           float(latest.get("h2h_race_win_rate", 0.5) or 0.5),
        "team_trajectory":    float(latest.get("team_upgrade_trajectory", 0.0) or 0.0),
    }


def get_driver_form_trend(driver: str, season: int = None, last_n: int = 10) -> pd.DataFrame:
    """Driver finish positions over recent races."""
    df = load_race_data()
    if df.empty:
        return pd.DataFrame()

    d = df[df["driver"].str.lower().str.contains(
        driver.split()[-1].lower(), na=False
    )].sort_values(["season","round"])

    if season:
        d = d[d["season"] == season]

    return d.tail(last_n)[["season","round","circuit","finish_position",
                             "qualifying_position","points","team"]].reset_index(drop=True)


def get_circuit_stats(circuit: str) -> dict:
    """Circuit-specific statistics across all seasons."""
    df = load_race_data()
    if df.empty:
        return {}

    c = df[df["circuit"].str.lower().str.contains(
        circuit.lower().replace(" grand prix",""), na=False
    )]
    if c.empty:
        return {}

    winners = c[c["win"] == 1]["driver"].value_counts().head(5).to_dict()
    pole_holders = c[c["pole_position"] == 1]["driver"].value_counts().head(3).to_dict()

    return {
        "total_races":    c["round"].nunique(),
        "seasons":        sorted(c["season"].unique().tolist()),
        "top_winners":    winners,
        "top_pole":       pole_holders,
        "avg_pit_stops":  float(c["pit_stops"].mean()) if "pit_stops" in c.columns else 2.0,
        "dnf_rate":       float(c["incidents"].mean()) if "incidents" in c.columns else 0.15,
        "wet_races":      int((c["weather"] == "Wet").sum()) if "weather" in c.columns else 0,
    }


def get_expert_predictions(driver: str = None, race_weekend: str = None) -> pd.DataFrame:
    """Expert predictions from DB."""
    session = _get_session()
    if session is None:
        return pd.DataFrame()

    try:
        from ingestion.db.schema import ExpertPrediction
        query = session.query(ExpertPrediction)
        if driver:
            query = query.filter(
                ExpertPrediction.driver_name.ilike(f"%{driver}%")
            )
        if race_weekend:
            query = query.filter(
                ExpertPrediction.race_weekend.ilike(f"%{race_weekend}%")
            )

        rows = []
        for p in query.order_by(ExpertPrediction.ingested_at.desc()).all():
            rows.append({
                "driver":      p.driver_name,
                "team":        p.team_name,
                "prediction":  p.prediction_text,
                "sentiment":   p.sentiment,
                "confidence":  p.confidence_score,
                "source":      p.source,
                "weekend":     p.race_weekend,
                "raw_text":    p.raw_text,
                "ingested_at": str(p.ingested_at)[:19],
            })
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"Expert prediction query failed: {e}")
        return pd.DataFrame()


def get_regulations(season: int = 2026) -> pd.DataFrame:
    """Regulation data from DB."""
    session = _get_session()
    if session is None:
        return pd.DataFrame()

    try:
        from ingestion.db.schema import Regulation
        regs = session.query(Regulation).filter_by(
            effective_season=season
        ).all()

        rows = []
        for r in regs:
            rows.append({
                "rule_id":        r.rule_id,
                "category":       r.category,
                "sub_category":   r.sub_category,
                "description":    r.rule_description,
                "race_impact":    r.potential_race_impact,
                "strategy_impact":r.potential_strategy_impact,
                "impact_score":   r.impact_score,
            })
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"Regulation query failed: {e}")
        return pd.DataFrame()


def get_db_status() -> dict:
    """Full database status summary."""
    session = _get_session()
    if session is None:
        return {"available": False}

    try:
        from ingestion.db.schema import (
            Driver, Team, Circuit, Race, RaceResult,
            ExpertPrediction, Regulation, IngestionLog
        )
        return {
            "available":          True,
            "drivers":            session.query(Driver).count(),
            "teams":              session.query(Team).count(),
            "circuits":           session.query(Circuit).count(),
            "races_total":        session.query(Race).count(),
            "races_2026":         session.query(Race).filter_by(season=2026).count(),
            "race_results":       session.query(RaceResult).count(),
            "expert_predictions": session.query(ExpertPrediction).count(),
            "regulations":        session.query(Regulation).count(),
            "ingestion_logs":     session.query(IngestionLog).count(),
            "last_ingest":        _get_last_ingest_time(session),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def get_recent_ingestion_log(limit: int = 10) -> pd.DataFrame:
    """Recent ingestion log entries."""
    session = _get_session()
    if session is None:
        return pd.DataFrame()

    try:
        from ingestion.db.schema import IngestionLog
        logs = session.query(IngestionLog)\
            .order_by(IngestionLog.timestamp.desc())\
            .limit(limit).all()

        return pd.DataFrame([{
            "timestamp":  str(l.timestamp)[:19],
            "type":       l.data_type,
            "status":     l.status,
            "inserted":   l.rows_inserted,
            "updated":    l.rows_updated,
            "source":     l.triggered_by,
            "duration":   f"{l.duration_secs:.2f}s" if l.duration_secs else "-",
        } for l in logs])
    except Exception as e:
        return pd.DataFrame()


def get_season_race_calendar(season: int = 2026) -> pd.DataFrame:
    """Full race calendar with completion status."""
    session = _get_session()
    if session is None:
        return pd.DataFrame()

    try:
        from ingestion.db.schema import Race
        races = session.query(Race).filter_by(season=season)\
            .order_by(Race.round_number).all()

        return pd.DataFrame([{
            "round":        r.round_number,
            "race_name":    r.race_name,
            "date":         r.race_date,
            "sprint":       "✅" if r.is_sprint_weekend else "—",
            "status":       r.status,
        } for r in races])
    except Exception as e:
        return pd.DataFrame()


def get_driver_cpi_ranking(season: int = 2026) -> pd.DataFrame:
    """Driver Combined Performance Index ranking."""
    df = load_race_data(season)
    if df.empty or "combined_performance_index" not in df.columns:
        return pd.DataFrame()

    latest = df.sort_values(["season","round"])\
        .groupby("driver").last().reset_index()

    cols = ["driver", "team", "combined_performance_index",
            "expert_confidence_score", "reg_combined_impact",
            "driver_form_momentum_score", "circuit_performance_index"]
    available = [c for c in cols if c in latest.columns]

    return latest[available].sort_values(
        "combined_performance_index", ascending=False
    ).reset_index(drop=True)


def _get_last_ingest_time(session) -> str:
    try:
        from ingestion.db.schema import IngestionLog
        last = session.query(IngestionLog)\
            .filter_by(status="success")\
            .order_by(IngestionLog.timestamp.desc())\
            .first()
        return str(last.timestamp)[:19] if last else "Never"
    except Exception:
        return "Unknown"


if __name__ == "__main__":
    print("\n=== Data Layer Test ===\n")

    print(f"DB Available: {db_available()}")

    status = get_db_status()
    print(f"\nDB Status:")
    for k, v in status.items():
        print(f"  {k:<25} {v}")

    print(f"\nSeason 2026 Standings (top 5):")
    standings = get_season_standings(2026)
    if not standings.empty:
        print(standings.head(5)[["driver","team","wins","podiums","points"]].to_string())

    print(f"\nGeorge Russell stats:")
    stats = get_driver_stats("George Russell")
    for k, v in stats.items():
        if k != "best_circuits":
            print(f"  {k:<25} {v}")

    print(f"\nExpert Predictions:")
    preds = get_expert_predictions()
    if not preds.empty:
        print(preds[["driver","sentiment","confidence","source"]].to_string())

    print(f"\n2026 Calendar:")
    cal = get_season_race_calendar(2026)
    if not cal.empty:
        print(cal.head(5).to_string())