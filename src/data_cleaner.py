"""
data_cleaner.py
Handles messy F1 CSV inputs: normalizes columns, fills missing values,
removes duplicates, validates numerics, and encodes categoricals.
"""

import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

COLUMN_ALIASES = {
    # Common messy column name variants -> canonical name
    "race": "circuit",
    "grand_prix": "circuit",
    "gp": "circuit",
    "name": "driver",
    "constructor": "team",
    "car": "team",
    "grid": "qualifying_position",
    "grid_position": "qualifying_position",
    "start_position": "qualifying_position",
    "position": "finish_position",
    "result": "finish_position",
    "final_position": "finish_position",
    "race_position": "finish_position",
    "pole": "pole_position",
    "year": "season",
    "conditions": "weather",
    "tyre_strategy": "tire_strategy",
    "strategy": "tire_strategy",
    "stops": "pit_stops",
    "pit_stop_count": "pit_stops",
    "crash": "incidents",
    "dnf": "incidents",
    "penalty": "penalties",
}

REQUIRED_COLS = ["season", "circuit", "driver", "team", "qualifying_position", "finish_position"]
NUMERIC_COLS = ["season", "qualifying_position", "pole_position", "finish_position",
                "pit_stops", "incidents", "penalties", "points", "podium", "win", "round"]
CATEGORICAL_COLS = ["circuit", "driver", "team", "weather", "tire_strategy", "location"]

VALID_WEATHER = {"Dry", "Wet", "Mixed"}
VALID_TIRE_STRATEGY = {"1-stop", "2-stop", "3-stop", "0-stop"}


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    df.rename(columns={k: v for k, v in COLUMN_ALIASES.items() if k in df.columns}, inplace=True)
    logger.info(f"Normalized columns: {list(df.columns)}")
    return df


def add_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "season": 2024,
        "round": 1,
        "location": "Unknown",
        "pole_position": 0,
        "weather": "Dry",
        "tire_strategy": "2-stop",
        "pit_stops": 2,
        "incidents": 0,
        "penalties": 0,
        "points": 0,
        "podium": 0,
        "win": 0,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
            logger.info(f"Added missing column '{col}' with default={default}")
    return df


def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Remove duplicate columns if any
    df = df.loc[:, ~df.columns.duplicated()]
    for col in NUMERIC_COLS:
        if col in df.columns:
            original_nulls = df[col].isnull().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Fill strategy per column
            if col in ["qualifying_position", "finish_position"]:
                df[col].fillna(df[col].median(), inplace=True)
            elif col in ["incidents", "penalties", "win", "podium", "pole_position"]:
                df[col].fillna(0, inplace=True)
            elif col == "pit_stops":
                df[col].fillna(2, inplace=True)
            elif col == "points":
                # Recalculate from finish position if missing
                points_map = {1:25,2:18,3:15,4:12,5:10,6:8,7:6,8:4,9:2,10:1}
                mask = df[col].isnull()
                df.loc[mask, col] = df.loc[mask, "finish_position"].map(points_map).fillna(0)
            else:
                df[col].fillna(df[col].median(), inplace=True)
            df[col] = df[col].astype(float)
            cleaned = df[col].isnull().sum()
            if original_nulls > 0:
                logger.info(f"  '{col}': filled {original_nulls} nulls → {cleaned} remaining")
    return df


def clean_categorical_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
            null_count = (df[col].str.lower() == "nan").sum()
            if null_count > 0:
                if col == "weather":
                    df.loc[df[col].str.lower() == "nan", col] = "Dry"
                elif col == "tire_strategy":
                    df.loc[df[col].str.lower() == "nan", col] = "2-Stop"
                else:
                    df.loc[df[col].str.lower() == "nan", col] = "Unknown"
    
    # Normalize weather values
    if "weather" in df.columns:
        weather_map = {
            "Sunny": "Dry", "Clear": "Dry", "Fine": "Dry",
            "Rainy": "Wet", "Rain": "Wet", "Damp": "Wet",
            "Changeable": "Mixed", "Overcast": "Mixed", "Cloudy": "Mixed",
        }
        df["weather"] = df["weather"].replace(weather_map)
        invalid = ~df["weather"].isin(VALID_WEATHER)
        if invalid.sum() > 0:
            logger.warning(f"  {invalid.sum()} unknown weather values set to 'Dry'")
            df.loc[invalid, "weather"] = "Dry"
    
    # Normalize tire strategy
    if "tire_strategy" in df.columns:
        df["tire_strategy"] = df["tire_strategy"].str.lower().str.replace("tyre", "tire")
        strategy_map = {
            "one stop": "1-stop", "1 stop": "1-stop", "one-stop": "1-stop",
            "two stop": "2-stop", "2 stop": "2-stop", "two-stop": "2-stop",
            "three stop": "3-stop", "3 stop": "3-stop", "three-stop": "3-stop",
        }
        df["tire_strategy"] = df["tire_strategy"].replace(strategy_map).str.title()
    
    return df


def derive_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate podium/win/pole from positions if not explicitly set."""
    if "finish_position" in df.columns:
        df["finish_position"] = df["finish_position"].astype(float)
        df["podium"] = (df["finish_position"] <= 3).astype(int)
        df["win"] = (df["finish_position"] == 1).astype(int)
    if "qualifying_position" in df.columns:
        df["pole_position"] = (df["qualifying_position"].astype(float) == 1).astype(int)
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    subset = [c for c in ["season", "round", "circuit", "driver"] if c in df.columns]
    if subset:
        df.drop_duplicates(subset=subset, keep="last", inplace=True)
    after = len(df)
    if before != after:
        logger.info(f"Removed {before - after} duplicate rows")
    return df


def validate_positions(df: pd.DataFrame) -> pd.DataFrame:
    if "finish_position" in df.columns:
        invalid = df["finish_position"] < 1
        if invalid.sum():
            logger.warning(f"  {invalid.sum()} invalid finish positions clamped to >=1")
            df.loc[invalid, "finish_position"] = df["finish_position"].median()
    if "qualifying_position" in df.columns:
        invalid = df["qualifying_position"] < 1
        if invalid.sum():
            df.loc[invalid, "qualifying_position"] = df["qualifying_position"].median()
    return df


def clean_dataset(input_path: str, output_path: str = None) -> pd.DataFrame:
    logger.info(f"=== Starting data cleaning: {input_path} ===")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    df = normalize_column_names(df)
    df = add_missing_columns(df)
    df = clean_numeric_columns(df)
    df = clean_categorical_columns(df)
    df = derive_labels(df)
    df = validate_positions(df)
    df = remove_duplicates(df)
    df.reset_index(drop=True, inplace=True)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data → {output_path} ({len(df)} rows)")
    
    logger.info("=== Cleaning complete ===")
    return df


if __name__ == "__main__":
    clean_dataset(
        "data/raw_race_data.csv",
        "data/cleaned_race_data.csv"
    )
