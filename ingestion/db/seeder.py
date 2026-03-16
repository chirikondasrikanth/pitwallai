"""
ingestion/db/seeder.py
Seeds all reference tables: drivers, teams, circuits, races, regulations.
Run once after init_db() to populate master data.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ingestion.db.schema import (
    init_db, get_session, Driver, Team, Circuit, Race, Regulation
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ─── MASTER DATA ──────────────────────────────────────────────────

TEAMS_2026 = [
    {"name": "Mercedes",      "full_name": "Mercedes-AMG PETRONAS F1 Team", "nationality": "German",   "power_unit": "Mercedes",  "active_season": 2026},
    {"name": "Ferrari",       "full_name": "Scuderia Ferrari HP",            "nationality": "Italian",  "power_unit": "Ferrari",   "active_season": 2026},
    {"name": "McLaren",       "full_name": "McLaren Formula 1 Team",         "nationality": "British",  "power_unit": "Mercedes",  "active_season": 2026},
    {"name": "Red Bull",      "full_name": "Oracle Red Bull Racing",         "nationality": "Austrian", "power_unit": "Ford RBPT", "active_season": 2026},
    {"name": "Aston Martin",  "full_name": "Aston Martin Aramco F1 Team",    "nationality": "British",  "power_unit": "Honda",     "active_season": 2026},
    {"name": "Alpine",        "full_name": "BWT Alpine F1 Team",             "nationality": "French",   "power_unit": "Renault",   "active_season": 2026},
    {"name": "Haas",          "full_name": "MoneyGram Haas F1 Team",         "nationality": "American", "power_unit": "Ferrari",   "active_season": 2026},
    {"name": "Williams",      "full_name": "Williams Racing",                 "nationality": "British",  "power_unit": "Mercedes",  "active_season": 2026},
    {"name": "Racing Bulls",  "full_name": "Visa Cash App RB F1 Team",       "nationality": "Italian",  "power_unit": "Ford RBPT", "active_season": 2026},
    {"name": "Audi",          "full_name": "Audi F1 Team",                   "nationality": "German",   "power_unit": "Audi",      "active_season": 2026},
    {"name": "Cadillac",      "full_name": "Cadillac F1 Team",               "nationality": "American", "power_unit": "GM",        "active_season": 2026},
]

DRIVERS_2026 = [
    {"full_name": "George Russell",    "abbreviation": "RUS", "nationality": "British",    "driver_number": 63,  "active_season": 2026},
    {"full_name": "Kimi Antonelli",    "abbreviation": "ANT", "nationality": "Italian",    "driver_number": 12,  "active_season": 2026},
    {"full_name": "Charles Leclerc",   "abbreviation": "LEC", "nationality": "Monégasque", "driver_number": 16,  "active_season": 2026},
    {"full_name": "Lewis Hamilton",    "abbreviation": "HAM", "nationality": "British",    "driver_number": 44,  "active_season": 2026},
    {"full_name": "Lando Norris",      "abbreviation": "NOR", "nationality": "British",    "driver_number": 4,   "active_season": 2026},
    {"full_name": "Oscar Piastri",     "abbreviation": "PIA", "nationality": "Australian", "driver_number": 81,  "active_season": 2026},
    {"full_name": "Max Verstappen",    "abbreviation": "VER", "nationality": "Dutch",      "driver_number": 1,   "active_season": 2026},
    {"full_name": "Isack Hadjar",      "abbreviation": "HAD", "nationality": "French",     "driver_number": 6,   "active_season": 2026},
    {"full_name": "Oliver Bearman",    "abbreviation": "BEA", "nationality": "British",    "driver_number": 87,  "active_season": 2026},
    {"full_name": "Esteban Ocon",      "abbreviation": "OCO", "nationality": "French",     "driver_number": 31,  "active_season": 2026},
    {"full_name": "Pierre Gasly",      "abbreviation": "GAS", "nationality": "French",     "driver_number": 10,  "active_season": 2026},
    {"full_name": "Franco Colapinto",  "abbreviation": "COL", "nationality": "Argentine",  "driver_number": 43,  "active_season": 2026},
    {"full_name": "Nico Hulkenberg",   "abbreviation": "HUL", "nationality": "German",     "driver_number": 27,  "active_season": 2026},
    {"full_name": "Gabriel Bortoleto", "abbreviation": "BOR", "nationality": "Brazilian",  "driver_number": 5,   "active_season": 2026},
    {"full_name": "Arvid Lindblad",    "abbreviation": "LIN", "nationality": "Swedish",    "driver_number": 7,   "active_season": 2026},
    {"full_name": "Liam Lawson",       "abbreviation": "LAW", "nationality": "New Zealander","driver_number": 30, "active_season": 2026},
    {"full_name": "Fernando Alonso",   "abbreviation": "ALO", "nationality": "Spanish",    "driver_number": 14,  "active_season": 2026},
    {"full_name": "Lance Stroll",      "abbreviation": "STR", "nationality": "Canadian",   "driver_number": 18,  "active_season": 2026},
    {"full_name": "Alexander Albon",   "abbreviation": "ALB", "nationality": "Thai",       "driver_number": 23,  "active_season": 2026},
    {"full_name": "Carlos Sainz",      "abbreviation": "SAI", "nationality": "Spanish",    "driver_number": 55,  "active_season": 2026},
    {"full_name": "Sergio Perez",      "abbreviation": "PER", "nationality": "Mexican",    "driver_number": 11,  "active_season": 2026},
    {"full_name": "Valtteri Bottas",   "abbreviation": "BOT", "nationality": "Finnish",    "driver_number": 77,  "active_season": 2026},
]

CIRCUITS_2026 = [
    {"name": "Australian Grand Prix",     "location": "Melbourne",    "country": "Australia",     "circuit_type": "park",       "total_laps": 58,  "circuit_length_km": 5.278, "overtaking_difficulty": "medium", "drs_zones": 3},
    {"name": "Chinese Grand Prix",        "location": "Shanghai",     "country": "China",         "circuit_type": "permanent",  "total_laps": 56,  "circuit_length_km": 5.451, "overtaking_difficulty": "medium", "drs_zones": 2},
    {"name": "Japanese Grand Prix",       "location": "Suzuka",       "country": "Japan",         "circuit_type": "permanent",  "total_laps": 53,  "circuit_length_km": 5.807, "overtaking_difficulty": "low",    "drs_zones": 1},
    {"name": "Bahrain Grand Prix",        "location": "Sakhir",       "country": "Bahrain",       "circuit_type": "permanent",  "total_laps": 57,  "circuit_length_km": 5.412, "overtaking_difficulty": "high",   "drs_zones": 3},
    {"name": "Saudi Arabian Grand Prix",  "location": "Jeddah",       "country": "Saudi Arabia",  "circuit_type": "street",     "total_laps": 50,  "circuit_length_km": 6.174, "overtaking_difficulty": "high",   "drs_zones": 3},
    {"name": "Miami Grand Prix",          "location": "Miami",        "country": "USA",           "circuit_type": "street",     "total_laps": 57,  "circuit_length_km": 5.412, "overtaking_difficulty": "medium", "drs_zones": 3},
    {"name": "Emilia Romagna Grand Prix", "location": "Imola",        "country": "Italy",         "circuit_type": "permanent",  "total_laps": 63,  "circuit_length_km": 4.909, "overtaking_difficulty": "low",    "drs_zones": 1},
    {"name": "Monaco Grand Prix",         "location": "Monaco",       "country": "Monaco",        "circuit_type": "street",     "total_laps": 78,  "circuit_length_km": 3.337, "overtaking_difficulty": "very_low","drs_zones": 1},
    {"name": "Spanish Grand Prix",        "location": "Barcelona",    "country": "Spain",         "circuit_type": "permanent",  "total_laps": 66,  "circuit_length_km": 4.657, "overtaking_difficulty": "medium", "drs_zones": 2},
    {"name": "Canadian Grand Prix",       "location": "Montreal",     "country": "Canada",        "circuit_type": "semi-street","total_laps": 70,  "circuit_length_km": 4.361, "overtaking_difficulty": "medium", "drs_zones": 2},
    {"name": "Austrian Grand Prix",       "location": "Spielberg",    "country": "Austria",       "circuit_type": "permanent",  "total_laps": 71,  "circuit_length_km": 4.318, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "British Grand Prix",        "location": "Silverstone",  "country": "UK",            "circuit_type": "permanent",  "total_laps": 52,  "circuit_length_km": 5.891, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "Belgian Grand Prix",        "location": "Spa",          "country": "Belgium",       "circuit_type": "permanent",  "total_laps": 44,  "circuit_length_km": 7.004, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "Hungarian Grand Prix",      "location": "Budapest",     "country": "Hungary",       "circuit_type": "permanent",  "total_laps": 70,  "circuit_length_km": 4.381, "overtaking_difficulty": "low",    "drs_zones": 1},
    {"name": "Dutch Grand Prix",          "location": "Zandvoort",    "country": "Netherlands",   "circuit_type": "permanent",  "total_laps": 72,  "circuit_length_km": 4.259, "overtaking_difficulty": "low",    "drs_zones": 2},
    {"name": "Italian Grand Prix",        "location": "Monza",        "country": "Italy",         "circuit_type": "permanent",  "total_laps": 53,  "circuit_length_km": 5.793, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "Azerbaijan Grand Prix",     "location": "Baku",         "country": "Azerbaijan",    "circuit_type": "street",     "total_laps": 51,  "circuit_length_km": 6.003, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "Singapore Grand Prix",      "location": "Singapore",    "country": "Singapore",     "circuit_type": "street",     "total_laps": 62,  "circuit_length_km": 4.940, "overtaking_difficulty": "low",    "drs_zones": 2},
    {"name": "United States Grand Prix",  "location": "Austin",       "country": "USA",           "circuit_type": "permanent",  "total_laps": 56,  "circuit_length_km": 5.513, "overtaking_difficulty": "medium", "drs_zones": 2},
    {"name": "Mexico City Grand Prix",    "location": "Mexico City",  "country": "Mexico",        "circuit_type": "permanent",  "total_laps": 71,  "circuit_length_km": 4.304, "overtaking_difficulty": "medium", "drs_zones": 3},
    {"name": "São Paulo Grand Prix",      "location": "Interlagos",   "country": "Brazil",        "circuit_type": "permanent",  "total_laps": 71,  "circuit_length_km": 4.309, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "Las Vegas Grand Prix",      "location": "Las Vegas",    "country": "USA",           "circuit_type": "street",     "total_laps": 50,  "circuit_length_km": 6.201, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "Qatar Grand Prix",          "location": "Lusail",       "country": "Qatar",         "circuit_type": "permanent",  "total_laps": 57,  "circuit_length_km": 5.380, "overtaking_difficulty": "high",   "drs_zones": 2},
    {"name": "Abu Dhabi Grand Prix",      "location": "Yas Marina",   "country": "UAE",           "circuit_type": "permanent",  "total_laps": 58,  "circuit_length_km": 5.281, "overtaking_difficulty": "medium", "drs_zones": 2},
]

RACES_2026 = [
    {"season": 2026, "round_number": 1,  "race_name": "Australian Grand Prix",     "race_date": "2026-03-08", "is_sprint_weekend": False, "status": "completed"},
    {"season": 2026, "round_number": 2,  "race_name": "Chinese Grand Prix",        "race_date": "2026-03-15", "is_sprint_weekend": True,  "status": "completed"},
    {"season": 2026, "round_number": 3,  "race_name": "Japanese Grand Prix",       "race_date": "2026-03-29", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 4,  "race_name": "Bahrain Grand Prix",        "race_date": "2026-04-12", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 5,  "race_name": "Saudi Arabian Grand Prix",  "race_date": "2026-04-19", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 6,  "race_name": "Miami Grand Prix",          "race_date": "2026-05-03", "is_sprint_weekend": True,  "status": "scheduled"},
    {"season": 2026, "round_number": 7,  "race_name": "Emilia Romagna Grand Prix", "race_date": "2026-05-17", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 8,  "race_name": "Monaco Grand Prix",         "race_date": "2026-05-24", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 9,  "race_name": "Spanish Grand Prix",        "race_date": "2026-06-01", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 10, "race_name": "Canadian Grand Prix",       "race_date": "2026-06-15", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 11, "race_name": "Austrian Grand Prix",       "race_date": "2026-06-28", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 12, "race_name": "British Grand Prix",        "race_date": "2026-07-05", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 13, "race_name": "Belgian Grand Prix",        "race_date": "2026-07-26", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 14, "race_name": "Hungarian Grand Prix",      "race_date": "2026-08-02", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 15, "race_name": "Dutch Grand Prix",          "race_date": "2026-08-30", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 16, "race_name": "Italian Grand Prix",        "race_date": "2026-09-06", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 17, "race_name": "Azerbaijan Grand Prix",     "race_date": "2026-09-20", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 18, "race_name": "Singapore Grand Prix",      "race_date": "2026-10-04", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 19, "race_name": "United States Grand Prix",  "race_date": "2026-10-18", "is_sprint_weekend": True,  "status": "scheduled"},
    {"season": 2026, "round_number": 20, "race_name": "Mexico City Grand Prix",    "race_date": "2026-10-25", "is_sprint_weekend": False, "status": "scheduled"},
    {"season": 2026, "round_number": 21, "race_name": "São Paulo Grand Prix",      "race_date": "2026-11-08", "is_sprint_weekend": True,  "status": "scheduled"},
    {"season": 2026, "round_number": 22, "race_name": "Las Vegas Grand Prix",      "race_date": "2026-11-21", "is_sprint_weekend": True,  "status": "scheduled"},
    {"season": 2026, "round_number": 23, "race_name": "Qatar Grand Prix",          "race_date": "2026-11-29", "is_sprint_weekend": True,  "status": "scheduled"},
    {"season": 2026, "round_number": 24, "race_name": "Abu Dhabi Grand Prix",      "race_date": "2026-12-06", "is_sprint_weekend": False, "status": "scheduled"},
]

CIRCUIT_NAMES = [
    "Bahrain Grand Prix", "Saudi Arabian Grand Prix", "Australian Grand Prix",
    "Japanese Grand Prix", "Chinese Grand Prix", "Miami Grand Prix",
    "Emilia Romagna Grand Prix", "Monaco Grand Prix", "Canadian Grand Prix",
    "Spanish Grand Prix", "Austrian Grand Prix", "British Grand Prix",
    "Hungarian Grand Prix", "Belgian Grand Prix", "Dutch Grand Prix",
    "Italian Grand Prix", "Azerbaijan Grand Prix", "Singapore Grand Prix",
    "United States Grand Prix", "Mexico City Grand Prix", "São Paulo Grand Prix",
    "Las Vegas Grand Prix", "Qatar Grand Prix", "Abu Dhabi Grand Prix",
]

RACES_2024 = [
    {"season": 2024, "round_number": i+1, "race_name": name,
     "race_date": "2024-01-01", "is_sprint_weekend": False, "status": "completed"}
    for i, name in enumerate(CIRCUIT_NAMES)
]

RACES_2025 = [
    {"season": 2025, "round_number": i+1, "race_name": name,
     "race_date": "2025-01-01", "is_sprint_weekend": False, "status": "completed"}
    for i, name in enumerate(CIRCUIT_NAMES)
]

REGULATIONS_2026 = [
    {"rule_id":"REG-2026-PU-001","category":"power_unit","sub_category":"electric","rule_description":"Increased electric energy deployment — 350kW electric motor vs 150kW in 2025. Equal split between ICE and electric power.","effective_season":2026,"potential_race_impact":"Higher acceleration out of slow corners. Faster starts. Overtaking easier on straights.","potential_strategy_impact":"Battery management critical. Teams with better energy harvesting gain strategic advantage.","impact_score":0.95,"teams_affected":{"benefited":["Mercedes","Ferrari"],"challenged":["Red Bull","Audi"]}},
    {"rule_id":"REG-2026-PU-002","category":"power_unit","sub_category":"fuel","rule_description":"100% sustainable fuel mandatory across all teams.","effective_season":2026,"potential_race_impact":"Marginal power reduction vs 2025 fossil fuel cars.","potential_strategy_impact":"Fuel load management more critical — energy density slightly lower.","impact_score":0.4,"teams_affected":{}},
    {"rule_id":"REG-2026-AERO-001","category":"aerodynamics","sub_category":"front_wing","rule_description":"Simplified front wing with reduced outwash. Active aerodynamics introduced — moveable elements in low and high drag modes.","effective_season":2026,"potential_race_impact":"Higher top speeds on straights with drag reduction. Better wheel-to-wheel racing.","potential_strategy_impact":"DRS concept replaced by active aero — always on. Qualifying vs race trim less distinct.","impact_score":0.9,"teams_affected":{"benefited":["Mercedes","McLaren"],"challenged":["Red Bull"]}},
    {"rule_id":"REG-2026-AERO-002","category":"aerodynamics","sub_category":"underfloor","rule_description":"Ground effect underfloor retained but refined. Reduced porpoising risk vs 2022-generation cars.","effective_season":2026,"potential_race_impact":"More consistent car balance. Closer racing expected.","potential_strategy_impact":"Tire deg profiles changed — teams must recalibrate pit windows.","impact_score":0.7,"teams_affected":{}},
    {"rule_id":"REG-2026-TIRE-001","category":"tires","sub_category":"construction","rule_description":"New Pirelli tire construction for 2026 regulations. 18-inch wheels retained. New compounds optimized for higher electric torque.","effective_season":2026,"potential_race_impact":"Different degradation curve. Higher torque stress on rear tires at slow circuits.","potential_strategy_impact":"1-stop strategies more viable at certain circuits. Tire warm-up quicker.","impact_score":0.75,"teams_affected":{}},
    {"rule_id":"REG-2026-CAR-001","category":"chassis","sub_category":"weight","rule_description":"Minimum car weight reduced to 768kg (from 798kg in 2024). Narrower cars — 1900mm vs 2000mm.","effective_season":2026,"potential_race_impact":"Faster cornering. Better mechanical grip. Lap times faster than 2025 in most corners.","potential_strategy_impact":"Lighter cars use fuel more efficiently — strategy windows shift slightly.","impact_score":0.65,"teams_affected":{}},
    {"rule_id":"REG-2026-ENTRY-001","category":"entries","sub_category":"new_teams","rule_description":"Audi F1 Team and Cadillac F1 Team join as 11th and 12th constructors. Maximum grid size 24 cars.","effective_season":2026,"potential_race_impact":"More competitive midfield. Points harder to score. Q1/Q2 more intense.","potential_strategy_impact":"New teams bring different supplier relationships and pit stop learning curves.","impact_score":0.5,"teams_affected":{"new_entrants":["Audi","Cadillac"]}},
    {"rule_id":"REG-2026-SPRINT-001","category":"format","sub_category":"sprint","rule_description":"Sprint weekends reduced to 6 per season. Only 1 practice session before Sprint Qualifying.","effective_season":2026,"potential_race_impact":"Less track time amplifies qualifying importance. Setup gambles more likely.","potential_strategy_impact":"Teams with better simulation tools gain bigger edge on sprint weekends.","impact_score":0.55,"teams_affected":{}},
]


def seed_all(session=None):
    if session is None:
        engine = init_db()
        session = get_session(engine)

    inserted = {"teams": 0, "drivers": 0, "circuits": 0, "races": 0, "regulations": 0}

    # Teams
    for t in TEAMS_2026:
        exists = session.query(Team).filter_by(name=t["name"]).first()
        if not exists:
            session.add(Team(**t))
            inserted["teams"] += 1
    session.commit()

    # Drivers
    for d in DRIVERS_2026:
        exists = session.query(Driver).filter_by(full_name=d["full_name"]).first()
        if not exists:
            session.add(Driver(**d))
            inserted["drivers"] += 1
    session.commit()

    # Circuits
    circuit_map = {}
    for c in CIRCUITS_2026:
        exists = session.query(Circuit).filter_by(name=c["name"]).first()
        if not exists:
            obj = Circuit(**c)
            session.add(obj)
            session.flush()
            circuit_map[c["name"]] = obj.id
        else:
            circuit_map[c["name"]] = exists.id
        inserted["circuits"] += 1
    session.commit()

    # Races — 2024, 2025, 2026
    all_races = RACES_2024 + RACES_2025 + RACES_2026
    for r in all_races:
        exists = session.query(Race).filter_by(season=r["season"], round_number=r["round_number"]).first()
        if not exists:
            circuit_id = circuit_map.get(r["race_name"])
            obj = Race(
                season=r["season"], round_number=r["round_number"],
                circuit_id=circuit_id, race_name=r["race_name"],
                race_date=r["race_date"], is_sprint_weekend=r["is_sprint_weekend"],
                status=r["status"],
            )
            session.add(obj)
            inserted["races"] += 1
    session.commit()

    # Regulations
    for reg in REGULATIONS_2026:
        exists = session.query(Regulation).filter_by(rule_id=reg["rule_id"]).first()
        if not exists:
            session.add(Regulation(**reg))
            inserted["regulations"] += 1
    session.commit()

    print(f"✅ Seeding complete:")
    for k, v in inserted.items():
        print(f"   {k}: {v} inserted")

    return inserted


if __name__ == "__main__":
    engine = init_db()
    session = get_session(engine)
    seed_all(session)
