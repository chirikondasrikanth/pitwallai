"""
ingestion/scrapers/race_ingester.py
Ingests race results (from CSV, dict, or API response) into the relational DB.
Handles: race_results, qualifying_results, pit_stops, weather_data.
Logs every operation to ingestion_log table.
"""

import os
import sys
import time
import logging
import pandas as pd
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ingestion.db.schema import (
    init_db, get_session, get_engine,
    Driver, Team, Circuit, Race,
    RaceResult, QualifyingResult, PitStop, WeatherData, IngestionLog
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

POINTS_MAP = {1:25,2:18,3:15,4:12,5:10,6:8,7:6,8:4,9:2,10:1}


class RaceIngester:

    def __init__(self, db_url: str = None):
        self.engine  = init_db(get_engine(db_url))
        self.session = get_session(self.engine)

    def _get_or_create_driver(self, name: str) -> Optional[int]:
        if not name or name.lower() in ("nan", "unknown", ""):
            return None
        name = name.strip().title()
        obj = self.session.query(Driver).filter_by(full_name=name).first()
        if obj:
            return obj.id
        # Create minimal driver record
        new_driver = Driver(full_name=name, active_season=2026)
        self.session.add(new_driver)
        self.session.flush()
        logger.info(f"  Created new driver: {name}")
        return new_driver.id

    def _get_or_create_team(self, name: str) -> Optional[int]:
        if not name or name.lower() in ("nan", "unknown", ""):
            return None
        team_map = {
            "mclaren": "McLaren", "mercedes": "Mercedes", "ferrari": "Ferrari",
            "red bull": "Red Bull", "aston martin": "Aston Martin", "alpine": "Alpine",
            "haas": "Haas", "williams": "Williams", "racing bulls": "Racing Bulls",
            "audi": "Audi", "cadillac": "Cadillac", "kick sauber": "Kick Sauber",
            "rb": "Racing Bulls",
        }
        name = team_map.get(name.strip().lower(), name.strip().title())
        obj = self.session.query(Team).filter_by(name=name).first()
        if obj:
            return obj.id
        new_team = Team(name=name, active_season=2026)
        self.session.add(new_team)
        self.session.flush()
        logger.info(f"  Created new team: {name}")
        return new_team.id

    def _get_race(self, season: int, circuit_name: str = None,
                  round_number: int = None) -> Optional[Race]:
        query = self.session.query(Race).filter_by(season=season)
        if round_number:
            query = query.filter_by(round_number=round_number)
        if circuit_name:
            query = query.filter(Race.race_name.ilike(f"%{circuit_name}%"))
        return query.first()

    def ingest_race_results(self, data: pd.DataFrame,
                             season: int = 2026,
                             round_number: int = None,
                             circuit_name: str = None,
                             triggered_by: str = "manual") -> dict:
        """
        Ingest a DataFrame of race results into the DB.
        Handles duplicates gracefully (upsert logic).
        """
        start_time = time.time()
        stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

        race = self._get_race(season, circuit_name, round_number)
        if not race:
            logger.warning(f"Race not found: season={season}, round={round_number}, circuit={circuit_name}")
            self._log(triggered_by, "race_result", season, round_number,
                      "failed", 0, 0, 0,
                      "Race not found in database", time.time()-start_time)
            return {"success": False, "message": "Race not found", **stats}

        for _, row in data.iterrows():
            try:
                driver_id = self._get_or_create_driver(str(row.get("driver","")))
                team_id   = self._get_or_create_team(str(row.get("team","")))
                if not driver_id:
                    stats["skipped"] += 1
                    continue

                finish_pos = self._safe_int(row.get("finish_position"))
                qual_pos   = self._safe_int(row.get("qualifying_position"))
                points     = float(row.get("points", POINTS_MAP.get(finish_pos, 0) if finish_pos else 0))
                status     = "Finished"
                if row.get("dnf", 0) == 1 or row.get("incidents", 0) == 1:
                    status = "DNF"
                if row.get("dns", 0) == 1:
                    status = "DNS"

                # Check existing
                existing = self.session.query(RaceResult).filter_by(
                    race_id=race.id, driver_id=driver_id
                ).first()

                result_data = {
                    "race_id":        race.id,
                    "driver_id":      driver_id,
                    "team_id":        team_id,
                    "finish_position": finish_pos,
                    "grid_position":  qual_pos,
                    "points":         points,
                    "status":         status,
                    "tire_strategy":  str(row.get("tire_strategy", "2-Stop")),
                    "pit_stop_count": self._safe_int(row.get("pit_stops", 2)),
                    "incidents":      bool(row.get("incidents", 0)),
                    "penalties":      self._safe_int(row.get("penalties", 0)),
                    "podium":         bool(finish_pos and finish_pos <= 3 and status == "Finished"),
                    "win":            bool(finish_pos == 1 and status == "Finished"),
                    "updated_at":     datetime.utcnow(),
                }

                if existing:
                    for k, v in result_data.items():
                        setattr(existing, k, v)
                    stats["updated"] += 1
                else:
                    self.session.add(RaceResult(**result_data))
                    stats["inserted"] += 1

            except Exception as e:
                logger.error(f"  Error on row {row.get('driver','?')}: {e}")
                stats["errors"] += 1

        try:
            self.session.commit()
            # Mark race as completed
            race.status = "completed"
            race.updated_at = datetime.utcnow()
            self.session.commit()
            status_flag = "success"
            msg = f"Race results ingested: {stats}"
        except Exception as e:
            self.session.rollback()
            status_flag = "failed"
            msg = str(e)

        elapsed = time.time() - start_time
        self._log(triggered_by, "race_result", season, round_number,
                  status_flag, stats["inserted"], stats["updated"],
                  stats["skipped"], msg if status_flag=="failed" else None, elapsed)

        logger.info(f"Ingest complete: {stats} in {elapsed:.2f}s")
        return {"success": status_flag == "success", "stats": stats, "message": msg}

    def ingest_qualifying_results(self, data: pd.DataFrame,
                                   season: int = 2026,
                                   round_number: int = None,
                                   circuit_name: str = None) -> dict:
        stats = {"inserted": 0, "updated": 0, "skipped": 0}

        race = self._get_race(season, circuit_name, round_number)
        if not race:
            return {"success": False, "message": "Race not found"}

        for _, row in data.iterrows():
            try:
                driver_id = self._get_or_create_driver(str(row.get("driver","")))
                team_id   = self._get_or_create_team(str(row.get("team","")))
                if not driver_id:
                    stats["skipped"] += 1
                    continue

                qual_pos = self._safe_int(row.get("qualifying_position"))
                existing = self.session.query(QualifyingResult).filter_by(
                    race_id=race.id, driver_id=driver_id
                ).first()

                qdata = {
                    "race_id":              race.id,
                    "driver_id":            driver_id,
                    "team_id":              team_id,
                    "qualifying_position":  qual_pos,
                    "best_lap_time":        str(row.get("q3_time", row.get("best_time", ""))),
                    "is_pole":              bool(qual_pos == 1),
                }

                if existing:
                    for k, v in qdata.items(): setattr(existing, k, v)
                    stats["updated"] += 1
                else:
                    self.session.add(QualifyingResult(**qdata))
                    stats["inserted"] += 1

            except Exception as e:
                logger.error(f"  Qual error {row.get('driver','?')}: {e}")

        self.session.commit()
        return {"success": True, "stats": stats}

    def ingest_weather(self, race_season: int, round_number: int,
                        condition: str, air_temp: float = None,
                        track_temp: float = None, session_type: str = "race") -> bool:
        race = self._get_race(race_season, round_number=round_number)
        if not race:
            return False
        w = WeatherData(
            race_id=race.id, session_type=session_type,
            condition=condition, air_temp_c=air_temp, track_temp_c=track_temp
        )
        self.session.add(w)
        self.session.commit()
        return True

    def ingest_from_csv(self, csv_path: str, season: int = 2026,
                         round_number: int = None, circuit_name: str = None) -> dict:
        """Load a CSV and ingest race results."""
        df = pd.read_csv(csv_path)
        return self.ingest_race_results(df, season, round_number, circuit_name,
                                         triggered_by="csv_upload")

    def ingest_from_platform_csv(self, triggered_by: str = "auto") -> dict:
        """
        Load the platform's own cleaned_race_data.csv and sync it to the DB.
        This bridges the CSV-based pipeline with the relational DB.
        """
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        csv_path = os.path.join(base, "data", "cleaned_race_data.csv")

        if not os.path.exists(csv_path):
            return {"success": False, "message": "cleaned_race_data.csv not found"}

        df = pd.read_csv(csv_path)
        total_stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

        for (season, round_num), group in df.groupby(["season", "round"]):
            circuit = group.iloc[0].get("circuit", "Unknown")
            result = self.ingest_race_results(
                group, season=int(season),
                round_number=int(round_num), circuit_name=circuit,
                triggered_by=triggered_by
            )
            if result.get("stats"):
                for k in total_stats:
                    total_stats[k] += result["stats"].get(k, 0)

        logger.info(f"Platform CSV sync complete: {total_stats}")
        return {"success": True, "stats": total_stats}

    def get_ingestion_history(self, limit: int = 20) -> list:
        logs = self.session.query(IngestionLog)\
            .order_by(IngestionLog.timestamp.desc())\
            .limit(limit).all()
        return [{
            "timestamp": str(l.timestamp),
            "source": l.source, "data_type": l.data_type,
            "season": l.season, "round": l.round_number,
            "status": l.status, "inserted": l.rows_inserted,
            "updated": l.rows_updated, "duration": l.duration_secs,
        } for l in logs]

    def _log(self, triggered_by, data_type, season, round_num,
             status, inserted, updated, skipped, error, duration):
        log = IngestionLog(
            source=triggered_by, data_type=data_type,
            season=season, round_number=round_num,
            status=status, rows_inserted=inserted,
            rows_updated=updated, rows_skipped=skipped,
            error_message=error, duration_secs=round(duration, 3),
            triggered_by=triggered_by,
        )
        self.session.add(log)
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()

    @staticmethod
    def _safe_int(val) -> Optional[int]:
        try:
            return int(float(val)) if val is not None and str(val) not in ("nan","") else None
        except (ValueError, TypeError):
            return None


if __name__ == "__main__":
    ingester = RaceIngester()
    from ingestion.db.seeder import seed_all
    seed_all(ingester.session)
    result = ingester.ingest_from_platform_csv(triggered_by="setup")
    print(f"\nSync result: {result}")
    history = ingester.get_ingestion_history(5)
    print(f"\nRecent ingestion log:")
    for h in history:
        print(f"  {h['timestamp'][:19]} | {h['data_type']:<15} | {h['status']:<8} | +{h['inserted']} rows")
