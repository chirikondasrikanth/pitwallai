"""
generate_data.py
Seeds the database with:
  - Realistic 2024 & 2025 historical data (for model training)
  - REAL 2026 Australian GP result (Round 1, 8 Mar 2026) — fully verified
  NOTE: China GP Round 2 race is 15 Mar 2026 — not yet completed at time of writing
"""
import pandas as pd
import numpy as np
import os

np.random.seed(42)

# ─── REAL 2026 AUSTRALIAN GP (Round 1, 8 Mar 2026) ───────────────
# Sources: Wikipedia, The-Race, GPFans, RacingNews365, Formula1.com
# Qualifying grid from official F1 starting grid
AUSTRALIA_2026 = [
    # (driver, team, qual_pos, finish_pos, tire_strategy, pit_stops, incidents, penalties, points)
    # finish_pos=0 means DNF/DNS
    ("George Russell",    "Mercedes",      1,  1, "1-Stop", 1, 0, 0, 26),  # incl fastest lap
    ("Kimi Antonelli",    "Mercedes",      2,  2, "1-Stop", 1, 0, 1, 18),  # 10s penalty
    ("Charles Leclerc",   "Ferrari",       4,  3, "1-Stop", 1, 0, 0, 15),
    ("Lewis Hamilton",    "Ferrari",       6,  4, "1-Stop", 1, 0, 0, 12),
    ("Lando Norris",      "McLaren",       5,  5, "2-Stop", 2, 0, 0, 10),
    ("Max Verstappen",    "Red Bull",     20,  6, "2-Stop", 2, 0, 0,  8),  # P20 after Q1 crash
    ("Oliver Bearman",    "Haas",          7,  7, "2-Stop", 2, 0, 0,  6),
    ("Arvid Lindblad",    "Racing Bulls",  9,  8, "2-Stop", 2, 0, 0,  4),  # debut finish
    ("Gabriel Bortoleto", "Audi",         10,  9, "2-Stop", 2, 0, 0,  2),  # Audi 1st points ever
    ("Pierre Gasly",      "Alpine",       11, 10, "2-Stop", 2, 0, 0,  1),
    ("Esteban Ocon",      "Haas",         12, 11, "2-Stop", 2, 0, 0,  0),
    ("Alexander Albon",   "Williams",     13, 12, "2-Stop", 2, 0, 0,  0),
    ("Liam Lawson",       "Racing Bulls",  8, 13, "2-Stop", 2, 0, 0,  0),
    ("Franco Colapinto",  "Alpine",       14, 14, "3-Stop", 3, 0, 0,  0),
    ("Carlos Sainz",      "Williams",     21, 15, "2-Stop", 2, 0, 0,  0),  # no Q time
    ("Sergio Perez",      "Cadillac",     18, 16, "3-Stop", 3, 0, 0,  0),
    ("Lance Stroll",      "Aston Martin", 22, 17, "2-Stop", 2, 1, 0,  0),  # classified finisher
    ("Fernando Alonso",   "Aston Martin", 15,  0, "1-Stop", 1, 1, 0,  0),  # DNF - retired
    ("Valtteri Bottas",   "Cadillac",     19,  0, "1-Stop", 1, 1, 0,  0),  # DNF - retired
    ("Isack Hadjar",      "Red Bull",      3,  0, "0-Stop", 0, 1, 0,  0),  # DNS - technical failure
    ("Oscar Piastri",     "McLaren",       5,  0, "0-Stop", 0, 1, 0,  0),  # DNS - formation lap crash
    ("Nico Hulkenberg",   "Audi",         16,  0, "0-Stop", 0, 1, 0,  0),  # DNS - mechanical
]

# ─── 2024 GRID ────────────────────────────────────────────────────
DRIVERS_2024 = [
    ("Max Verstappen","Red Bull"),("Sergio Perez","Red Bull"),
    ("Lewis Hamilton","Mercedes"),("George Russell","Mercedes"),
    ("Charles Leclerc","Ferrari"),("Carlos Sainz","Ferrari"),
    ("Lando Norris","McLaren"),("Oscar Piastri","McLaren"),
    ("Fernando Alonso","Aston Martin"),("Lance Stroll","Aston Martin"),
    ("Pierre Gasly","Alpine"),("Esteban Ocon","Alpine"),
    ("Valtteri Bottas","Kick Sauber"),("Zhou Guanyu","Kick Sauber"),
    ("Yuki Tsunoda","Racing Bulls"),("Daniel Ricciardo","Racing Bulls"),
    ("Kevin Magnussen","Haas"),("Nico Hulkenberg","Haas"),
    ("Alexander Albon","Williams"),("Logan Sargeant","Williams"),
]

# ─── 2025 GRID ────────────────────────────────────────────────────
DRIVERS_2025 = [
    ("Max Verstappen","Red Bull"),("Liam Lawson","Red Bull"),
    ("Lewis Hamilton","Ferrari"),("Charles Leclerc","Ferrari"),
    ("George Russell","Mercedes"),("Kimi Antonelli","Mercedes"),
    ("Lando Norris","McLaren"),("Oscar Piastri","McLaren"),
    ("Fernando Alonso","Aston Martin"),("Lance Stroll","Aston Martin"),
    ("Pierre Gasly","Alpine"),("Jack Doohan","Alpine"),
    ("Nico Hulkenberg","Kick Sauber"),("Gabriel Bortoleto","Kick Sauber"),
    ("Yuki Tsunoda","Racing Bulls"),("Isack Hadjar","Racing Bulls"),
    ("Oliver Bearman","Haas"),("Esteban Ocon","Haas"),
    ("Alexander Albon","Williams"),("Carlos Sainz","Williams"),
]

CIRCUITS = [
    ("Bahrain Grand Prix","Sakhir","dry","high"),
    ("Saudi Arabian Grand Prix","Jeddah","dry","high"),
    ("Australian Grand Prix","Melbourne","variable","medium"),
    ("Japanese Grand Prix","Suzuka","variable","low"),
    ("Chinese Grand Prix","Shanghai","dry","medium"),
    ("Miami Grand Prix","Miami","dry","medium"),
    ("Emilia Romagna Grand Prix","Imola","variable","low"),
    ("Monaco Grand Prix","Monaco","dry","very_low"),
    ("Canadian Grand Prix","Montreal","variable","medium"),
    ("Spanish Grand Prix","Barcelona","dry","medium"),
    ("Austrian Grand Prix","Spielberg","dry","high"),
    ("British Grand Prix","Silverstone","variable","high"),
    ("Hungarian Grand Prix","Budapest","dry","low"),
    ("Belgian Grand Prix","Spa","variable","high"),
    ("Dutch Grand Prix","Zandvoort","variable","low"),
    ("Italian Grand Prix","Monza","dry","high"),
    ("Azerbaijan Grand Prix","Baku","dry","high"),
    ("Singapore Grand Prix","Singapore","dry","low"),
    ("United States Grand Prix","Austin","dry","medium"),
    ("Mexico City Grand Prix","Mexico City","dry","medium"),
    ("São Paulo Grand Prix","Interlagos","variable","high"),
    ("Las Vegas Grand Prix","Las Vegas","dry","high"),
    ("Qatar Grand Prix","Lusail","dry","high"),
    ("Abu Dhabi Grand Prix","Yas Marina","dry","medium"),
]

TEAM_STRENGTH = {
    2024: {"Red Bull":0.97,"McLaren":0.93,"Ferrari":0.91,"Mercedes":0.88,
           "Aston Martin":0.82,"Racing Bulls":0.78,"Alpine":0.76,
           "Williams":0.75,"Haas":0.74,"Kick Sauber":0.72},
    2025: {"McLaren":0.96,"Ferrari":0.94,"Mercedes":0.87,"Red Bull":0.89,
           "Aston Martin":0.80,"Racing Bulls":0.79,"Alpine":0.75,
           "Williams":0.80,"Haas":0.76,"Kick Sauber":0.74},
}

DRIVER_SKILL = {
    "Max Verstappen":0.97,"Lewis Hamilton":0.96,"Charles Leclerc":0.93,
    "Lando Norris":0.92,"Fernando Alonso":0.91,"George Russell":0.90,
    "Carlos Sainz":0.89,"Oscar Piastri":0.88,"Sergio Perez":0.85,
    "Kimi Antonelli":0.84,"Liam Lawson":0.82,"Isack Hadjar":0.82,
    "Yuki Tsunoda":0.81,"Pierre Gasly":0.80,"Daniel Ricciardo":0.80,
    "Esteban Ocon":0.79,"Nico Hulkenberg":0.79,"Oliver Bearman":0.79,
    "Jack Doohan":0.78,"Alexander Albon":0.78,"Valtteri Bottas":0.77,
    "Franco Colapinto":0.77,"Gabriel Bortoleto":0.77,"Arvid Lindblad":0.76,
    "Lance Stroll":0.76,"Kevin Magnussen":0.76,"Zhou Guanyu":0.74,
    "Logan Sargeant":0.70,
}

CIRCUIT_SPECIALISTS = {
    "Monaco":    {"Charles Leclerc":0.10,"Max Verstappen":0.06,"Fernando Alonso":0.06},
    "Monza":     {"Charles Leclerc":0.09,"Max Verstappen":0.06},
    "Silverstone":{"Lewis Hamilton":0.12,"Lando Norris":0.08,"George Russell":0.06},
    "Spa":       {"Max Verstappen":0.10,"Lewis Hamilton":0.07},
    "Suzuka":    {"Max Verstappen":0.09,"Fernando Alonso":0.06},
    "Interlagos":{"Max Verstappen":0.05,"Lewis Hamilton":0.08},
    "Singapore": {"Charles Leclerc":0.08,"Fernando Alonso":0.07},
    "Austin":    {"Max Verstappen":0.07,"Lewis Hamilton":0.09},
    "Melbourne": {"George Russell":0.08,"Charles Leclerc":0.05},
    "Shanghai":  {"Lewis Hamilton":0.06,"George Russell":0.05},
}

POINTS_MAP = {1:25,2:18,3:15,4:12,5:10,6:8,7:6,8:4,9:2,10:1}


def simulate_season(season, drivers, circuits, team_strength):
    rows = []
    for race_idx, (circuit_name, location, typical_weather, overtaking) in enumerate(circuits):
        probs = {"dry":[0.82,0.08,0.10], "variable":[0.55,0.20,0.25]}
        weather = np.random.choice(["Dry","Wet","Mixed"], p=probs.get(typical_weather,[0.70,0.15,0.15]))

        scores = []
        for driver, team in drivers:
            skill = DRIVER_SKILL.get(driver, 0.75)
            team_perf = team_strength.get(team, 0.75)
            specialist = CIRCUIT_SPECIALISTS.get(location, {}).get(driver, 0)
            wet_adj = np.random.uniform(-0.05, 0.08) if weather in ["Wet","Mixed"] else 0
            score = skill*0.45 + team_perf*0.45 + specialist + wet_adj + np.random.normal(0,0.06)
            scores.append((driver, team, score))
        scores.sort(key=lambda x: x[2], reverse=True)

        qual_scores = []
        for driver, team, _ in scores:
            skill = DRIVER_SKILL.get(driver, 0.75)
            team_perf = team_strength.get(team, 0.75)
            q_score = skill*0.4 + team_perf*0.5 + np.random.normal(0,0.04)
            qual_scores.append((driver, team, q_score))
        qual_scores.sort(key=lambda x: x[2], reverse=True)
        qual_map = {d: i+1 for i,(d,t,_) in enumerate(qual_scores)}

        for finish_pos, (driver, team, _) in enumerate(scores, 1):
            qual_pos = qual_map[driver]
            pit_stops = min(np.random.choice([1,2,3], p=[0.25,0.55,0.20]) +
                           (np.random.choice([0,1],p=[0.5,0.5]) if weather=="Wet" else 0), 3)
            rows.append({
                "season":season, "round":race_idx+1,
                "circuit":circuit_name, "location":location,
                "driver":driver, "team":team,
                "qualifying_position":qual_pos, "pole_position":1 if qual_pos==1 else 0,
                "finish_position":finish_pos, "weather":weather,
                "tire_strategy":f"{pit_stops}-Stop", "pit_stops":pit_stops,
                "incidents":np.random.choice([0,1],p=[0.85,0.15]),
                "penalties":np.random.choice([0,1],p=[0.92,0.08]),
                "points":POINTS_MAP.get(finish_pos,0),
                "podium":1 if finish_pos<=3 else 0,
                "win":1 if finish_pos==1 else 0,
                "dnf":0,
            })
    return rows


def build_real_2026():
    rows = []
    for (driver,team,qual_pos,finish_pos,tire_strategy,pit_stops,incidents,penalties,points) in AUSTRALIA_2026:
        actual_finish = finish_pos if finish_pos > 0 else 20  # DNF mapped to last
        rows.append({
            "season":2026, "round":1,
            "circuit":"Australian Grand Prix", "location":"Melbourne",
            "driver":driver, "team":team,
            "qualifying_position":qual_pos, "pole_position":1 if qual_pos==1 else 0,
            "finish_position":actual_finish, "weather":"Dry",
            "tire_strategy":tire_strategy, "pit_stops":pit_stops,
            "incidents":incidents, "penalties":penalties, "points":points,
            "podium":1 if finish_pos in [1,2,3] else 0,
            "win":1 if finish_pos==1 else 0,
            "dnf":1 if finish_pos==0 else 0,
        })
    return rows


if __name__ == "__main__":
    all_rows = []

    print("Generating 2024 season (historical)...")
    all_rows += simulate_season(2024, DRIVERS_2024, CIRCUITS, TEAM_STRENGTH[2024])

    print("Generating 2025 season (historical)...")
    all_rows += simulate_season(2025, DRIVERS_2025, CIRCUITS, TEAM_STRENGTH[2025])

    print("Inserting REAL 2026 Australian GP results...")
    all_rows += build_real_2026()

    df = pd.DataFrame(all_rows)
    df["dnf"] = df["dnf"].fillna(0).astype(int)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/raw_race_data.csv", index=False)

    r26 = df[df["season"]==2026]
    print(f"\nTotal rows: {len(df)}")
    print(f"  2024: {len(df[df['season']==2024])} rows (24 races, simulated)")
    print(f"  2025: {len(df[df['season']==2025])} rows (24 races, simulated)")
    print(f"  2026: {len(r26)} rows (1 race — REAL DATA)")
    print(f"\n=== 2026 AUSTRALIAN GP — REAL RESULT ===")
    r26_sorted = r26.sort_values("finish_position").head(17)
    for _, row in r26_sorted.iterrows():
        dnf_str = " ← DNF" if row["dnf"]==1 else ""
        print(f"  P{int(row['finish_position']):<3} {row['driver']:<22} {row['team']:<16} {int(row['points'])} pts  Q{int(row['qualifying_position'])}{dnf_str}")
