"""
update_2026.py
Enters real 2026 race results and generates Japan GP prediction.

REAL RESULTS:
  Round 1 — Australian GP (8 Mar 2026)   ← already in system
  Round 2 — Chinese GP   (15 Mar 2026)   ← adding now

Then generates Japan GP (Round 3, 29 Mar 2026) prediction.
"""

import os, sys, pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV  = os.path.join(BASE_DIR, "data", "raw_race_data.csv")
CLEAN_CSV = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")

# ─── REAL 2026 CHINESE GP RESULTS (15 Mar 2026) ───────────────────
# Sources: Formula1.com, Sky Sports, Wikipedia, The Race, Crash.net
# Qualifying: Antonelli P1, Russell P2, Hamilton P3, Leclerc P4
# Gasly P5, Verstappen P6, Bearman P7, Hadjar P8, Norris P9, Piastri P10
# DNS: Norris, Piastri (McLaren electrical), Bortoleto (Audi), Albon (Williams)
# DNF: Verstappen (10 laps from end), Alonso (Aston Martin), Stroll (safety car)

CHINA_2026 = [
    # (driver, team, qual_pos, finish_pos, tire_strategy, pit_stops, incidents, penalties, points)
    ("Kimi Antonelli",    "Mercedes",      1,  1, "2-Stop", 2, 0, 0, 26),  # +FL point
    ("George Russell",    "Mercedes",      2,  2, "2-Stop", 2, 0, 0, 18),
    ("Lewis Hamilton",    "Ferrari",       3,  3, "2-Stop", 2, 0, 0, 15),  # 1st Ferrari podium
    ("Charles Leclerc",   "Ferrari",       4,  4, "2-Stop", 2, 0, 0, 12),
    ("Oliver Bearman",    "Haas",          7,  5, "2-Stop", 2, 0, 0, 10),
    ("Pierre Gasly",      "Alpine",        5,  6, "2-Stop", 2, 0, 0,  8),
    ("Liam Lawson",       "Racing Bulls",  8,  7, "2-Stop", 2, 0, 0,  6),
    ("Isack Hadjar",      "Red Bull",      8,  8, "2-Stop", 2, 0, 0,  4),  # spun lap 1, recovered
    ("Carlos Sainz",      "Williams",     14,  9, "2-Stop", 2, 0, 0,  2),  # 1st Williams points
    ("Franco Colapinto",  "Alpine",       12, 10, "2-Stop", 2, 1, 0,  1),  # collision w/ Ocon
    ("Nico Hulkenberg",   "Audi",         11, 11, "2-Stop", 2, 0, 0,  0),
    ("Arvid Lindblad",    "Racing Bulls", 15, 12, "2-Stop", 2, 0, 0,  0),  # spun at T14
    ("Valtteri Bottas",   "Cadillac",     16, 13, "2-Stop", 2, 0, 0,  0),
    ("Esteban Ocon",      "Haas",         13, 14, "2-Stop", 2, 1, 5,  0),  # collision penalty
    ("Sergio Perez",      "Cadillac",     20, 15, "3-Stop", 3, 1, 0,  0),  # spun T3 lap 1
    ("Max Verstappen",    "Red Bull",      6,  0, "2-Stop", 2, 1, 0,  0),  # DNF lap 46
    ("Fernando Alonso",   "Aston Martin", 17,  0, "1-Stop", 1, 1, 0,  0),  # DNF retired
    ("Lance Stroll",      "Aston Martin", 18,  0, "0-Stop", 0, 1, 0,  0),  # DNF safety car cause
    ("Lando Norris",      "McLaren",       9,  0, "0-Stop", 0, 1, 0,  0),  # DNS electrical
    ("Oscar Piastri",     "McLaren",      10,  0, "0-Stop", 0, 1, 0,  0),  # DNS electrical
    ("Gabriel Bortoleto", "Audi",         13,  0, "0-Stop", 0, 1, 0,  0),  # DNS car issue
    ("Alexander Albon",   "Williams",     18,  0, "0-Stop", 0, 1, 0,  0),  # DNS pit lane
]

# ─── JAPAN GP QUALIFYING (29 Mar 2026) ────────────────────────────
# Based on 2026 form, Suzuka characteristics, expert predictions
# Mercedes dominant but Ferrari improving, Suzuka suits downforce cars
JAPAN_QUALI_ORDER = [
    "George Russell",    # P1 - pole, Mercedes pace
    "Kimi Antonelli",    # P2 - China winner, momentum
    "Charles Leclerc",   # P3 - strong Suzuka history
    "Lewis Hamilton",    # P4 - 6x Suzuka winner
    "Max Verstappen",    # P5 - recovering form
    "Lando Norris",      # P6 - McLaren back after DNS
    "Oscar Piastri",     # P7 - McLaren back
    "Fernando Alonso",   # P8 - Suzuka specialist
    "Pierre Gasly",      # P9 - strong Alpine form
    "Oliver Bearman",    # P10 - Haas consistency
    "Isack Hadjar",      # P11
    "Liam Lawson",       # P12
    "Carlos Sainz",      # P13
    "Esteban Ocon",      # P14
    "Nico Hulkenberg",   # P15
    "Franco Colapinto",  # P16
    "Arvid Lindblad",    # P17
    "Lance Stroll",      # P18
    "Valtteri Bottas",   # P19
    "Gabriel Bortoleto", # P20
    "Alexander Albon",   # P21
    "Sergio Perez",      # P22
]

DRIVERS_2026 = [
    ("George Russell",    "Mercedes"),    ("Kimi Antonelli",    "Mercedes"),
    ("Charles Leclerc",   "Ferrari"),     ("Lewis Hamilton",    "Ferrari"),
    ("Lando Norris",      "McLaren"),     ("Oscar Piastri",     "McLaren"),
    ("Max Verstappen",    "Red Bull"),    ("Isack Hadjar",      "Red Bull"),
    ("Oliver Bearman",    "Haas"),        ("Esteban Ocon",      "Haas"),
    ("Pierre Gasly",      "Alpine"),      ("Franco Colapinto",  "Alpine"),
    ("Nico Hulkenberg",   "Audi"),        ("Gabriel Bortoleto", "Audi"),
    ("Arvid Lindblad",    "Racing Bulls"),("Liam Lawson",       "Racing Bulls"),
    ("Fernando Alonso",   "Aston Martin"),("Lance Stroll",      "Aston Martin"),
    ("Alexander Albon",   "Williams"),    ("Carlos Sainz",      "Williams"),
    ("Sergio Perez",      "Cadillac"),    ("Valtteri Bottas",   "Cadillac"),
]


def add_china_results():
    print("\n" + "="*55)
    print("  STEP I — ADDING CHINA GP REAL RESULTS")
    print("="*55)

    rows = []
    for (driver, team, qual_pos, finish_pos,
         tire_strategy, pit_stops, incidents, penalties, points) in CHINA_2026:

        actual_finish = finish_pos if finish_pos > 0 else 20
        rows.append({
            "season": 2026, "round": 2,
            "circuit": "Chinese Grand Prix", "location": "Shanghai",
            "driver": driver, "team": team,
            "qualifying_position": qual_pos,
            "pole_position": 1 if qual_pos == 1 else 0,
            "finish_position": actual_finish,
            "weather": "Dry",
            "tire_strategy": tire_strategy,
            "pit_stops": pit_stops,
            "incidents": incidents,
            "penalties": penalties,
            "points": points,
            "podium": 1 if finish_pos in [1, 2, 3] else 0,
            "win": 1 if finish_pos == 1 else 0,
            "dnf": 1 if finish_pos == 0 else 0,
        })

    df_china = pd.DataFrame(rows)

    # Load existing data
    if os.path.exists(RAW_CSV):
        existing = pd.read_csv(RAW_CSV)
        # Remove any existing China 2026 rows
        existing = existing[
            ~((existing["season"] == 2026) & (existing["round"] == 2))
        ]
        combined = pd.concat([existing, df_china], ignore_index=True)
    else:
        combined = df_china

    combined.to_csv(RAW_CSV, index=False)
    print(f"  ✅ Added {len(df_china)} China GP entries")
    print(f"  🏆 Winner: Kimi Antonelli (Mercedes)")
    print(f"  🥈 P2: George Russell (Mercedes)")
    print(f"  🥉 P3: Lewis Hamilton (Ferrari) — 1st Ferrari podium")
    print(f"  ⚠️  DNF: Verstappen, Alonso, Stroll")
    print(f"  ❌ DNS: Norris, Piastri, Bortoleto, Albon")

    # Clean
    from src.data_cleaner import clean_dataset
    clean_df = clean_dataset(RAW_CSV, CLEAN_CSV)
    print(f"\n  Dataset: {len(clean_df)} rows | "
          f"2026 rounds: {len(clean_df[clean_df['season']==2026]['round'].unique())}")

    return clean_df


def rebuild_features():
    print("\n" + "="*55)
    print("  REBUILDING FEATURE STORE")
    print("="*55)
    from ingestion.feature_store import FeatureStore
    store = FeatureStore()
    df = store.build()
    print(f"  ✅ Enriched features rebuilt: {df.shape}")
    return df


def retrain_models():
    print("\n" + "="*55)
    print("  RETRAINING MODELS WITH 2 REAL 2026 RACES")
    print("="*55)
    from src.train_model import train_pipeline
    _, _, _, feature_cols, metrics = train_pipeline()
    print(f"\n  ✅ Retrained with {metrics['n_features']} features")
    print(f"  Podium AUC:   {metrics['podium_auc']:.4f}")
    print(f"  Position MAE: {metrics['position_mae']:.4f}")
    return metrics


def predict_japan():
    print("\n" + "="*55)
    print("  STEP H — JAPAN GP PREDICTION (Round 3)")
    print("  Suzuka Circuit — 29 March 2026")
    print("="*55)

    import pandas as pd
    from src.predict import predict_race, format_prediction_output

    hist_df = pd.read_csv(CLEAN_CSV)

    pred = predict_race(
        circuit="Japanese Grand Prix",
        drivers=DRIVERS_2026,
        weather="Dry",
        qualifying_order=JAPAN_QUALI_ORDER,
        historical_df=hist_df,
        explain=True,
    )

    print(format_prediction_output(pred))

    # LLM Reasoning
    print("\n" + "="*55)
    print("  AI RACE ANALYSIS — JAPAN GP")
    print("="*55)
    try:
        from ingestion.llm_reasoning import LLMReasoning
        import os as _os
        reasoner = LLMReasoning(api_key=_os.environ.get("ANTHROPIC_API_KEY", ""))
        reasoning = reasoner.explain_race_prediction(
            circuit="Japanese Grand Prix",
            prediction=pred,
            weather="Dry",
            season=2026,
        )
        print(f"\n📖 {reasoning['race_preview']}")
        print(f"\n🏆 {reasoning['winner_reasoning']}")
        print(f"\n🔧 {reasoning['strategy_insight']}")
        print(f"\n⚡ {reasoning['dark_horses']}")
        print(f"\n⚠️  {reasoning['risk_factors']}")
        print(f"\n📊 Confidence: {reasoning['confidence_level']} — {reasoning['confidence_reason']}")

        print(f"\n{'='*55}")
        print(f"  📸 INSTAGRAM CAPTION — @boxboxdata")
        print(f"{'='*55}")
        caption = reasoner.generate_race_preview_post(
            "Japanese Grand Prix", pred, "Dry", "instagram"
        )
        print(caption)

    except Exception as e:
        print(f"LLM reasoning: {e}")

    # Championship standings
    print(f"\n{'='*55}")
    print(f"  2026 DRIVERS CHAMPIONSHIP (after Round 2)")
    print(f"{'='*55}")
    standings_data = [
        ("George Russell",    "Mercedes",     43),
        ("Kimi Antonelli",    "Mercedes",     39),
        ("Charles Leclerc",   "Ferrari",      27),
        ("Lewis Hamilton",    "Ferrari",      27),
        ("Oliver Bearman",    "Haas",         16),
        ("Lando Norris",      "McLaren",      10),
        ("Max Verstappen",    "Red Bull",      8),
        ("Pierre Gasly",      "Alpine",        9),
        ("Liam Lawson",       "Racing Bulls",  6),
        ("Isack Hadjar",      "Red Bull",      4),
    ]
    print(f"  {'Pos':<4} {'Driver':<22} {'Team':<14} {'Points'}")
    print(f"  {'-'*50}")
    for i, (driver, team, pts) in enumerate(standings_data, 1):
        print(f"  P{i:<3} {driver:<22} {team:<14} {pts}")

    return pred


if __name__ == "__main__":
    # Step I — Add China results
    add_china_results()

    # Rebuild features with new data
    rebuild_features()

    # Retrain with 2 real races
    retrain_models()

    # Step H — Japan prediction
    predict_japan()

    print(f"\n{'='*55}")
    print(f"  ALL DONE")
    print(f"  Round 1 Australia ✅ (real)")
    print(f"  Round 2 China     ✅ (real)")
    print(f"  Round 3 Japan     🔮 (prediction ready)")
    print(f"{'='*55}")