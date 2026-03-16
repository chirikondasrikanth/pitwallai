"""
crm_ingest.py
CRM-style race data ingestion: form-based or CSV upload.
Validates, cleans, appends new race data, and triggers model retraining.
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_cleaner import clean_dataset

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data", "raw_race_data.csv")
CLEAN_PATH = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")

VALID_TEAMS_2026 = [
    "Mercedes", "Ferrari", "McLaren", "Red Bull", "Haas",
    "Racing Bulls", "Alpine", "Audi", "Aston Martin", "Williams", "Cadillac"
]

DRIVERS_2026 = [
    "George Russell", "Kimi Antonelli", "Charles Leclerc", "Lewis Hamilton",
    "Lando Norris", "Oscar Piastri", "Max Verstappen", "Isack Hadjar",
    "Oliver Bearman", "Esteban Ocon", "Pierre Gasly", "Franco Colapinto",
    "Nico Hulkenberg", "Gabriel Bortoleto", "Arvid Lindblad", "Liam Lawson",
    "Fernando Alonso", "Lance Stroll", "Alexander Albon", "Carlos Sainz",
    "Sergio Perez", "Valtteri Bottas",
]

CIRCUITS_2026 = [
    "Australian Grand Prix", "Chinese Grand Prix", "Japanese Grand Prix",
    "Bahrain Grand Prix", "Saudi Arabian Grand Prix", "Miami Grand Prix",
    "Emilia Romagna Grand Prix", "Monaco Grand Prix", "Spanish Grand Prix",
    "Canadian Grand Prix", "Austrian Grand Prix", "British Grand Prix",
    "Belgian Grand Prix", "Hungarian Grand Prix", "Dutch Grand Prix",
    "Italian Grand Prix", "Azerbaijan Grand Prix", "Singapore Grand Prix",
    "United States Grand Prix", "Mexico City Grand Prix", "São Paulo Grand Prix",
    "Las Vegas Grand Prix", "Qatar Grand Prix", "Abu Dhabi Grand Prix",
]


class RaceDataForm:
    """CRM-style form for inserting a single driver's race result."""
    
    REQUIRED_FIELDS = ["season", "circuit", "driver", "team",
                        "qualifying_position", "finish_position"]
    
    FIELD_TYPES = {
        "season": int, "round": int, "qualifying_position": int,
        "finish_position": int, "pole_position": int, "pit_stops": int,
        "incidents": int, "penalties": int, "points": float,
        "podium": int, "win": int,
    }
    
    FIELD_RANGES = {
        "qualifying_position": (1, 20),
        "finish_position": (1, 20),
        "pit_stops": (0, 5),
        "season": (2020, 2030),
        "round": (1, 25),
    }
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, list]:
        errors = []
        
        for f in self.REQUIRED_FIELDS:
            if f not in data or data[f] is None or str(data[f]).strip() == "":
                errors.append(f"Missing required field: {f}")
        
        for field, expected_type in self.FIELD_TYPES.items():
            if field in data and data[field] is not None:
                try:
                    expected_type(data[field])
                except (ValueError, TypeError):
                    errors.append(f"Invalid type for '{field}': expected {expected_type.__name__}")
        
        for field, (lo, hi) in self.FIELD_RANGES.items():
            if field in data and data[field] is not None:
                try:
                    val = float(data[field])
                    if not (lo <= val <= hi):
                        errors.append(f"'{field}' out of range [{lo}, {hi}]: got {val}")
                except (ValueError, TypeError):
                    pass
        
        return len(errors) == 0, errors
    
    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        
        # Type casting
        for k, v in data.items():
            if k in self.FIELD_TYPES and v is not None:
                try:
                    result[k] = self.FIELD_TYPES[k](v)
                except Exception:
                    result[k] = v
            else:
                result[k] = v
        
        # Derive podium/win/pole
        fp = result.get("finish_position")
        qp = result.get("qualifying_position")
        if fp is not None:
            result["podium"] = 1 if int(fp) <= 3 else 0
            result["win"] = 1 if int(fp) == 1 else 0
        if qp is not None:
            result["pole_position"] = 1 if int(qp) == 1 else 0
        
        # Default points from position
        if "points" not in result or result.get("points") is None:
            points_map = {1:25,2:18,3:15,4:12,5:10,6:8,7:6,8:4,9:2,10:1}
            result["points"] = points_map.get(result.get("finish_position", 99), 0)
        
        # Defaults
        result.setdefault("weather", "Dry")
        result.setdefault("tire_strategy", "2-Stop")
        result.setdefault("pit_stops", 2)
        result.setdefault("incidents", 0)
        result.setdefault("penalties", 0)
        result.setdefault("round", 1)
        result.setdefault("location", result.get("circuit", "").replace(" Grand Prix", ""))
        result["ingested_at"] = datetime.now().isoformat()
        
        return result


def ingest_single_result(data: Dict[str, Any], auto_retrain: bool = False) -> dict:
    """Insert a single driver race result via CRM form."""
    form = RaceDataForm()
    is_valid, errors = form.validate(data)
    
    if not is_valid:
        return {"success": False, "errors": errors}
    
    normalized = form.normalize(data)
    
    # Load existing raw data
    if os.path.exists(RAW_PATH):
        df = pd.read_csv(RAW_PATH)
    else:
        df = pd.DataFrame(columns=list(normalized.keys()))
    
    # Check for duplicate
    dup_check = df[
        (df["season"].astype(str) == str(normalized["season"])) &
        (df["circuit"].str.lower() == str(normalized["circuit"]).lower()) &
        (df["driver"].str.lower() == str(normalized["driver"]).lower())
    ]
    
    if len(dup_check) > 0:
        logger.warning(f"Updating existing entry for {normalized['driver']} at {normalized['circuit']} {normalized['season']}")
        idx = dup_check.index[0]
        for k, v in normalized.items():
            if k in df.columns:
                df.at[idx, k] = v
    else:
        new_row = pd.DataFrame([normalized])
        df = pd.concat([df, new_row], ignore_index=True)
    
    df.to_csv(RAW_PATH, index=False)
    
    # Re-clean
    clean_df = clean_dataset(RAW_PATH, CLEAN_PATH)
    
    result = {"success": True, "message": f"Race result ingested for {normalized['driver']}", "rows": len(clean_df)}
    
    if auto_retrain:
        try:
            from src.train_model import train_pipeline
            metrics = train_pipeline(CLEAN_PATH)
            result["retrained"] = True
            result["metrics"] = metrics
        except Exception as e:
            result["retrained"] = False
            result["retrain_error"] = str(e)
    
    return result


def ingest_race_csv(csv_path: str, auto_retrain: bool = False) -> dict:
    """Bulk ingest from a CSV file (one row per driver per race)."""
    try:
        new_df = pd.read_csv(csv_path)
        logger.info(f"Loading CSV: {len(new_df)} rows, columns: {list(new_df.columns)}")
    except Exception as e:
        return {"success": False, "errors": [f"Failed to read CSV: {e}"]}
    
    if os.path.exists(RAW_PATH):
        existing_df = pd.read_csv(RAW_PATH)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df
    
    combined.to_csv(RAW_PATH, index=False)
    clean_df = clean_dataset(RAW_PATH, CLEAN_PATH)
    
    result = {
        "success": True,
        "rows_added": len(new_df),
        "total_rows": len(clean_df),
        "message": f"Successfully ingested {len(new_df)} rows from CSV",
    }
    
    if auto_retrain:
        try:
            from src.train_model import train_pipeline
            train_pipeline(CLEAN_PATH)
            result["retrained"] = True
        except Exception as e:
            result["retrained"] = False
            result["retrain_error"] = str(e)
    
    return result


def get_season_summary(season: int = 2025) -> pd.DataFrame:
    """Return season standings from clean data."""
    if not os.path.exists(CLEAN_PATH):
        return pd.DataFrame()
    df = pd.read_csv(CLEAN_PATH)
    df = df[df["season"] == season]
    standings = df.groupby(["driver", "team"]).agg(
        races=("finish_position", "count"),
        wins=("win", "sum"),
        podiums=("podium", "sum"),
        points=("points", "sum"),
        avg_finish=("finish_position", "mean"),
        avg_qual=("qualifying_position", "mean"),
    ).reset_index()
    standings.sort_values("points", ascending=False, inplace=True)
    standings.reset_index(drop=True, inplace=True)
    standings.index += 1
    return standings


if __name__ == "__main__":
    # Demo: ingest a sample result
    sample = {
        "season": 2026, "round": 1, "circuit": "Australian Grand Prix",
        "driver": "Lando Norris", "team": "McLaren",
        "qualifying_position": 1, "finish_position": 1,
        "weather": "Dry", "tire_strategy": "2-Stop",
        "pit_stops": 2, "incidents": 0, "penalties": 0,
    }
    result = ingest_single_result(sample)
    print(result)
    print(get_season_summary(2025).to_string())
