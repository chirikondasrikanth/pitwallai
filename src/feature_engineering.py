"""
feature_engineering.py
Builds ML features from cleaned race data:
  - Historical driver/team performance per circuit
  - Recent form (rolling windows)
  - Qualifying gap encoding
  - Weather & circuit encoded features
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Label-encode driver, team, circuit, weather for ML."""
    cat_cols = ["driver", "team", "circuit", "weather", "tire_strategy", "location"]
    for col in cat_cols:
        if col in df.columns:
            df[f"{col}_encoded"] = pd.Categorical(df[col]).codes
    return df


def add_pole_feature(df: pd.DataFrame) -> pd.DataFrame:
    df["is_pole"] = (df["qualifying_position"] == 1).astype(int)
    return df


def add_qualifying_gap(df: pd.DataFrame) -> pd.DataFrame:
    """How far back from pole is the driver's qualifying position (normalized 0-1)."""
    max_pos = df.groupby(["season", "round"])["qualifying_position"].transform("max")
    df["qualifying_gap"] = (df["qualifying_position"] - 1) / (max_pos - 1).replace(0, 1)
    df["qualifying_gap"] = df["qualifying_gap"].fillna(0).clip(0, 1)
    return df


def add_circuit_performance_score(df: pd.DataFrame) -> pd.DataFrame:
    """Historical avg finishing position per driver per circuit (lower = better)."""
    hist = df.groupby(["driver", "circuit"])["finish_position"].mean().reset_index()
    hist.rename(columns={"finish_position": "circuit_perf_score"}, inplace=True)
    
    # Normalize: convert to win-rate-style score (higher = better)
    worst = df["finish_position"].max()
    hist["circuit_perf_score"] = 1 - (hist["circuit_perf_score"] / worst)
    
    df = df.merge(hist, on=["driver", "circuit"], how="left")
    df["circuit_perf_score"] = df["circuit_perf_score"].fillna(0.5)
    return df


def add_driver_recent_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Rolling avg finish position for driver over last N races (per season, converted to score)."""
    df = df.sort_values(["season", "round"])
    
    def rolling_form(group):
        # Avg finish pos over last `window` races (shifted to avoid leakage)
        rolling = group["finish_position"].shift(1).rolling(window, min_periods=1).mean()
        return rolling
    
    df["recent_avg_finish"] = df.groupby("driver", group_keys=False).apply(rolling_form)
    worst = df["finish_position"].max()
    df["driver_recent_form"] = 1 - (df["recent_avg_finish"] / worst)
    df["driver_recent_form"] = df["driver_recent_form"].fillna(0.5).clip(0, 1)
    return df


def add_team_performance_trend(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Rolling avg finish position for the team over last N races."""
    df = df.sort_values(["season", "round"])
    
    team_avg = df.groupby(["season", "round", "team"])["finish_position"].mean().reset_index()
    team_avg.rename(columns={"finish_position": "team_avg_finish"}, inplace=True)
    team_avg = team_avg.sort_values(["season", "round"])
    
    team_avg["team_rolling"] = team_avg.groupby("team")["team_avg_finish"].transform(
        lambda x: x.shift(1).rolling(window, min_periods=1).mean()
    )
    
    worst = df["finish_position"].max()
    team_avg["team_performance_trend"] = 1 - (team_avg["team_rolling"] / worst)
    
    df = df.merge(
        team_avg[["season", "round", "team", "team_performance_trend"]],
        on=["season", "round", "team"], how="left"
    )
    df["team_performance_trend"] = df["team_performance_trend"].fillna(0.5).clip(0, 1)
    return df


def add_weather_encoded(df: pd.DataFrame) -> pd.DataFrame:
    weather_map = {"Dry": 0, "Mixed": 1, "Wet": 2}
    df["weather_encoded"] = df["weather"].map(weather_map).fillna(0).astype(int)
    return df


def add_driver_win_rate(df: pd.DataFrame) -> pd.DataFrame:
    win_rate = df.groupby("driver")["win"].mean().reset_index()
    win_rate.rename(columns={"win": "driver_win_rate"}, inplace=True)
    df = df.merge(win_rate, on="driver", how="left")
    df["driver_win_rate"] = df["driver_win_rate"].fillna(0)
    return df


def add_podium_rate(df: pd.DataFrame) -> pd.DataFrame:
    pod_rate = df.groupby("driver")["podium"].mean().reset_index()
    pod_rate.rename(columns={"podium": "driver_podium_rate"}, inplace=True)
    df = df.merge(pod_rate, on="driver", how="left")
    df["driver_podium_rate"] = df["driver_podium_rate"].fillna(0)
    return df


def add_circuit_overtaking_difficulty(df: pd.DataFrame) -> pd.DataFrame:
    """Proxy: std dev of positions gained at that circuit. High std = more overtaking."""
    if "qualifying_position" in df.columns:
        df["positions_gained"] = df["qualifying_position"] - df["finish_position"]
        circuit_std = df.groupby("circuit")["positions_gained"].std().reset_index()
        circuit_std.rename(columns={"positions_gained": "circuit_overtaking"}, inplace=True)
        df = df.merge(circuit_std, on="circuit", how="left")
        df["circuit_overtaking"] = df["circuit_overtaking"].fillna(df["circuit_overtaking"].mean()).clip(0)
        # Normalize
        max_ot = df["circuit_overtaking"].max()
        if max_ot > 0:
            df["circuit_overtaking"] = df["circuit_overtaking"] / max_ot
    return df


def add_incident_rate(df: pd.DataFrame) -> pd.DataFrame:
    inc_rate = df.groupby("driver")["incidents"].mean().reset_index()
    inc_rate.rename(columns={"incidents": "driver_incident_rate"}, inplace=True)
    df = df.merge(inc_rate, on="driver", how="left")
    df["driver_incident_rate"] = df["driver_incident_rate"].fillna(0)
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Building features...")
    df = df.copy()
    df = encode_categoricals(df)
    df = add_pole_feature(df)
    df = add_qualifying_gap(df)
    df = add_circuit_performance_score(df)
    df = add_driver_recent_form(df)
    df = add_team_performance_trend(df)
    df = add_weather_encoded(df)
    df = add_driver_win_rate(df)
    df = add_podium_rate(df)
    df = add_circuit_overtaking_difficulty(df)
    df = add_incident_rate(df)
    logger.info(f"Feature engineering complete. Shape: {df.shape}")
    return df


FEATURE_COLS = [
    "is_pole",
    "qualifying_gap",
    "circuit_perf_score",
    "driver_recent_form",
    "team_performance_trend",
    "weather_encoded",
    "driver_encoded",
    "team_encoded",
    "circuit_encoded",
    "driver_win_rate",
    "driver_podium_rate",
    "circuit_overtaking",
    "driver_incident_rate",
    "pit_stops",
    "penalties",
]


if __name__ == "__main__":
    df = pd.read_csv("data/cleaned_race_data.csv")
    df_feat = build_features(df)
    df_feat.to_csv("data/featured_race_data.csv", index=False)
    print(df_feat[FEATURE_COLS].describe())
