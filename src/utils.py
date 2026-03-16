"""
utils.py
Shared utilities: DB helpers, color maps, circuit metadata, driver lookup.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEAM_COLORS = {
    "Red Bull":       "#3671C6",
    "Ferrari":        "#E8002D",
    "Mercedes":       "#27F4D2",
    "McLaren":        "#FF8000",
    "Aston Martin":   "#229971",
    "Alpine":         "#FF87BC",
    "Audi":           "#C6A84B",
    "Racing Bulls":   "#6692FF",
    "Haas":           "#B6BABD",
    "Williams":       "#64C4FF",
    "Cadillac":       "#CC1B21",
}

CIRCUIT_METADATA = {
    "Australian Grand Prix":      {"laps": 58, "distance_km": 307.6, "type": "Street/Park", "overtaking": "Medium"},
    "Chinese Grand Prix":         {"laps": 56, "distance_km": 305.1, "type": "Permanent", "overtaking": "Medium"},
    "Japanese Grand Prix":        {"laps": 53, "distance_km": 307.5, "type": "Permanent", "overtaking": "Low"},
    "Bahrain Grand Prix":         {"laps": 57, "distance_km": 308.2, "type": "Permanent", "overtaking": "High"},
    "Saudi Arabian Grand Prix":   {"laps": 50, "distance_km": 308.5, "type": "Street", "overtaking": "High"},
    "Miami Grand Prix":           {"laps": 57, "distance_km": 308.3, "type": "Street", "overtaking": "Medium"},
    "Emilia Romagna Grand Prix":  {"laps": 63, "distance_km": 309.1, "type": "Permanent", "overtaking": "Low"},
    "Monaco Grand Prix":          {"laps": 78, "distance_km": 260.3, "type": "Street", "overtaking": "Very Low"},
    "Spanish Grand Prix":         {"laps": 66, "distance_km": 307.2, "type": "Permanent", "overtaking": "Medium"},
    "Canadian Grand Prix":        {"laps": 70, "distance_km": 305.3, "type": "Semi-Street", "overtaking": "Medium"},
    "Austrian Grand Prix":        {"laps": 71, "distance_km": 307.0, "type": "Permanent", "overtaking": "High"},
    "British Grand Prix":         {"laps": 52, "distance_km": 306.2, "type": "Permanent", "overtaking": "High"},
    "Belgian Grand Prix":         {"laps": 44, "distance_km": 308.1, "type": "Permanent", "overtaking": "High"},
    "Hungarian Grand Prix":       {"laps": 70, "distance_km": 306.6, "type": "Permanent", "overtaking": "Low"},
    "Dutch Grand Prix":           {"laps": 72, "distance_km": 308.6, "type": "Permanent", "overtaking": "Low"},
    "Italian Grand Prix":         {"laps": 53, "distance_km": 306.7, "type": "Permanent", "overtaking": "High"},
    "Azerbaijan Grand Prix":      {"laps": 51, "distance_km": 306.0, "type": "Street", "overtaking": "High"},
    "Singapore Grand Prix":       {"laps": 62, "distance_km": 308.7, "type": "Street", "overtaking": "Low"},
    "United States Grand Prix":   {"laps": 56, "distance_km": 308.4, "type": "Permanent", "overtaking": "Medium"},
    "Mexico City Grand Prix":     {"laps": 71, "distance_km": 305.4, "type": "Permanent", "overtaking": "Medium"},
    "São Paulo Grand Prix":       {"laps": 71, "distance_km": 305.9, "type": "Permanent", "overtaking": "High"},
    "Las Vegas Grand Prix":       {"laps": 50, "distance_km": 309.0, "type": "Street", "overtaking": "High"},
    "Qatar Grand Prix":           {"laps": 57, "distance_km": 308.6, "type": "Permanent", "overtaking": "High"},
    "Abu Dhabi Grand Prix":       {"laps": 58, "distance_km": 306.2, "type": "Permanent", "overtaking": "Medium"},
}

CIRCUITS_2026 = list(CIRCUIT_METADATA.keys())

DRIVERS_2026 = [
    ("George Russell",    "Mercedes"),
    ("Kimi Antonelli",    "Mercedes"),
    ("Charles Leclerc",   "Ferrari"),
    ("Lewis Hamilton",    "Ferrari"),
    ("Lando Norris",      "McLaren"),
    ("Oscar Piastri",     "McLaren"),
    ("Max Verstappen",    "Red Bull"),
    ("Isack Hadjar",      "Red Bull"),
    ("Oliver Bearman",    "Haas"),
    ("Esteban Ocon",      "Haas"),
    ("Pierre Gasly",      "Alpine"),
    ("Franco Colapinto",  "Alpine"),
    ("Nico Hulkenberg",   "Audi"),
    ("Gabriel Bortoleto", "Audi"),
    ("Arvid Lindblad",    "Racing Bulls"),
    ("Liam Lawson",       "Racing Bulls"),
    ("Fernando Alonso",   "Aston Martin"),
    ("Lance Stroll",      "Aston Martin"),
    ("Alexander Albon",   "Williams"),
    ("Carlos Sainz",      "Williams"),
    ("Sergio Perez",      "Cadillac"),
    ("Valtteri Bottas",   "Cadillac"),
]

DRIVER_NATIONALITIES = {
    "George Russell":    "🇬🇧", "Kimi Antonelli":    "🇮🇹",
    "Charles Leclerc":   "🇲🇨", "Lewis Hamilton":    "🇬🇧",
    "Lando Norris":      "🇬🇧", "Oscar Piastri":     "🇦🇺",
    "Max Verstappen":    "🇳🇱", "Isack Hadjar":      "🇫🇷",
    "Oliver Bearman":    "🇬🇧", "Esteban Ocon":      "🇫🇷",
    "Pierre Gasly":      "🇫🇷", "Franco Colapinto":  "🇦🇷",
    "Nico Hulkenberg":   "🇩🇪", "Gabriel Bortoleto": "🇧🇷",
    "Arvid Lindblad":    "🇸🇪", "Liam Lawson":       "🇳🇿",
    "Fernando Alonso":   "🇪🇸", "Lance Stroll":      "🇨🇦",
    "Alexander Albon":   "🇹🇭", "Carlos Sainz":      "🇪🇸",
    "Sergio Perez":      "🇲🇽", "Valtteri Bottas":   "🇫🇮",
}


def get_driver_team(driver_name: str) -> Optional[str]:
    for d, t in DRIVERS_2026:
        if d.lower() == driver_name.lower():
            return t
    return None


def get_team_color(team: str) -> str:
    return TEAM_COLORS.get(team, "#AAAAAA")


def get_circuit_info(circuit: str) -> dict:
    return CIRCUIT_METADATA.get(circuit, {"laps": 55, "distance_km": 305, "type": "Permanent", "overtaking": "Medium"})


def load_clean_data() -> pd.DataFrame:
    path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def get_driver_stats(driver: str, df: pd.DataFrame = None) -> dict:
    if df is None:
        df = load_clean_data()
    if df.empty:
        return {}
    d = df[df["driver"].str.lower() == driver.lower()]
    if d.empty:
        return {}
    return {
        "races": len(d),
        "wins": int(d["win"].sum()),
        "podiums": int(d["podium"].sum()),
        "poles": int(d["pole_position"].sum()),
        "points": float(d["points"].sum()),
        "avg_finish": float(d["finish_position"].mean()),
        "avg_qual": float(d["qualifying_position"].mean()),
        "win_rate": float(d["win"].mean()),
        "podium_rate": float(d["podium"].mean()),
        "team": d.iloc[-1]["team"],
        "best_circuits": d.groupby("circuit")["finish_position"].mean().nsmallest(3).index.tolist(),
    }


def get_model_metrics() -> dict:
    meta_path = os.path.join(BASE_DIR, "models", "model_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            return json.load(f)
    return {}
