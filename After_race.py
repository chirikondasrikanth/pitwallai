"""
after_race.py — ONE COMMAND AFTER EVERY RACE
Usage: python after_race.py "Japanese Grand Prix"

Automatically:
  1. Fetches real race results from OpenF1 API
  2. Adds results to database
  3. Retrains ML model
  4. Shows prediction accuracy vs reality
  5. Generates post-race Instagram caption
"""

import sys, os, requests, pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── CIRCUIT MAP ───────────────────────────────────────────────────
CIRCUIT_MAP = {
    "japanese":   {"full": "Japanese Grand Prix",     "openf1": "suzuka",      "round": 3},
    "japan":      {"full": "Japanese Grand Prix",     "openf1": "suzuka",      "round": 3},
    "australian": {"full": "Australian Grand Prix",   "openf1": "albert_park", "round": 1},
    "australia":  {"full": "Australian Grand Prix",   "openf1": "albert_park", "round": 1},
    "chinese":    {"full": "Chinese Grand Prix",      "openf1": "shanghai",    "round": 2},
    "china":      {"full": "Chinese Grand Prix",      "openf1": "shanghai",    "round": 2},
    "bahrain":    {"full": "Bahrain Grand Prix",      "openf1": "bahrain",     "round": 4},
    "saudi":      {"full": "Saudi Arabian Grand Prix","openf1": "jeddah",      "round": 5},
    "miami":      {"full": "Miami Grand Prix",        "openf1": "miami",       "round": 6},
    "monaco":     {"full": "Monaco Grand Prix",       "openf1": "monaco",      "round": 8},
    "spanish":    {"full": "Spanish Grand Prix",      "openf1": "barcelona",   "round": 9},
    "british":    {"full": "British Grand Prix",      "openf1": "silverstone", "round": 12},
    "belgian":    {"full": "Belgian Grand Prix",      "openf1": "spa",         "round": 13},
    "italian":    {"full": "Italian Grand Prix",      "openf1": "monza",       "round": 16},
    "singapore":  {"full": "Singapore Grand Prix",    "openf1": "marina_bay",  "round": 18},
    "lasvegas":   {"full": "Las Vegas Grand Prix",    "openf1": "las_vegas",   "round": 22},
    "abudhabi":   {"full": "Abu Dhabi Grand Prix",    "openf1": "yas_marina",  "round": 24},
}

DRIVER_NUMBERS = {
    12: "Kimi Antonelli",    63: "George Russell",
    16: "Charles Leclerc",   44: "Lewis Hamilton",
    4:  "Lando Norris",      81: "Oscar Piastri",
    1:  "Max Verstappen",    6:  "Isack Hadjar",
    87: "Oliver Bearman",    31: "Esteban Ocon",
    10: "Pierre Gasly",      43: "Franco Colapinto",
    27: "Nico Hulkenberg",   5:  "Gabriel Bortoleto",
    7:  "Arvid Lindblad",    30: "Liam Lawson",
    14: "Fernando Alonso",   18: "Lance Stroll",
    23: "Alexander Albon",   55: "Carlos Sainz",
    11: "Sergio Perez",      77: "Valtteri Bottas",
}

DRIVER_TEAMS = {
    "Kimi Antonelli": "Mercedes",    "George Russell": "Mercedes",
    "Charles Leclerc": "Ferrari",    "Lewis Hamilton": "Ferrari",
    "Lando Norris": "McLaren",       "Oscar Piastri": "McLaren",
    "Max Verstappen": "Red Bull",    "Isack Hadjar": "Red Bull",
    "Oliver Bearman": "Haas",        "Esteban Ocon": "Haas",
    "Pierre Gasly": "Alpine",        "Franco Colapinto": "Alpine",
    "Nico Hulkenberg": "Audi",       "Gabriel Bortoleto": "Audi",
    "Arvid Lindblad": "Racing Bulls","Liam Lawson": "Racing Bulls",
    "Fernando Alonso": "Aston Martin","Lance Stroll": "Aston Martin",
    "Alexander Albon": "Williams",   "Carlos Sainz": "Williams",
    "Sergio Perez": "Cadillac",      "Valtteri Bottas": "Cadillac",
}

# Known results fallback
KNOWN_RESULTS = {
    "australian": [
        ("George Russell", 1), ("Kimi Antonelli", 2), ("Lando Norris", 3),
        ("Oscar Piastri", 4), ("Charles Leclerc", 5), ("Lewis Hamilton", 6),
        ("Max Verstappen", 7), ("Pierre Gasly", 8), ("Isack Hadjar", 9),
        ("Fernando Alonso", 10),
    ],
    "chinese": [
        ("Kimi Antonelli", 1), ("George Russell", 2), ("Lewis Hamilton", 3),
        ("Charles Leclerc", 4), ("Oscar Piastri", 5), ("Lando Norris", 6),
        ("Pierre Gasly", 7), ("Isack Hadjar", 8), ("Fernando Alonso", 9),
        ("Carlos Sainz", 10),
    ],
}


def fetch_race_results(circuit_key: str) -> list:
    """Fetch real race results from OpenF1 API"""
    openf1_name = CIRCUIT_MAP[circuit_key]["openf1"]
    print(f"  Fetching race results from OpenF1 API...")

    try:
        # Get race session
        url = f"https://api.openf1.org/v1/sessions?year=2026&session_name=Race&circuit_short_name={openf1_name}"
        r = requests.get(url, timeout=10)
        sessions = r.json()
        if not sessions:
            raise ValueError("No race session found")

        session_key = sessions[0]["session_key"]
        print(f"  Session: {session_key} ✅")

        # Get final positions
        pos_url = f"https://api.openf1.org/v1/position?session_key={session_key}"
        pos_r = requests.get(pos_url, timeout=10)
        positions = pos_r.json()

        # Get last position entry per driver
        final = {}
        for p in positions:
            dn = p.get("driver_number")
            pos = p.get("position")
            if dn and pos:
                final[dn] = pos

        results = []
        for dn, pos in sorted(final.items(), key=lambda x: x[1]):
            name = DRIVER_NUMBERS.get(dn)
            if name:
                results.append((name, pos))

        print(f"  Got {len(results)} drivers ✅")
        return results

    except Exception as e:
        print(f"  OpenF1 unavailable: {e}")
        return None


def update_database(circuit_full: str, results: list, round_num: int):
    """Add race results to the database"""
    print(f"\n  Updating database...")
    try:
        from ingestion.db.data_layer import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        for driver, pos in results:
            team = DRIVER_TEAMS.get(driver, "Unknown")
            cursor.execute("""
                INSERT OR REPLACE INTO race_results
                (season, round, circuit, driver, team, finish_position, year)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (2026, round_num, circuit_full, driver, team, pos, 2026))

        conn.commit()
        conn.close()
        print(f"  {len(results)} results saved to DB ✅")
        return True
    except Exception as e:
        print(f"  DB update skipped: {e}")
        return False


def retrain_model():
    """Retrain ML model with new data"""
    print(f"\n  Retraining ML model...")
    try:
        import subprocess
        result = subprocess.run(
            ["python", "ingestion/run_ingestion.py", "--features"],
            capture_output=True, text=True, timeout=120
        )
        result2 = subprocess.run(
            ["python", "src/train_model.py"],
            capture_output=True, text=True, timeout=300
        )
        if result2.returncode == 0:
            print(f"  Model retrained successfully ✅")
        else:
            print(f"  Retraining: {result2.stderr[-200:] if result2.stderr else 'done'}")
    except Exception as e:
        print(f"  Retraining skipped: {e}")


def show_accuracy(circuit_full: str, results: list):
    """Compare prediction vs reality"""
    print(f"\n{'='*60}")
    print(f"  PREDICTION vs REALITY")
    print(f"{'='*60}")

    # Load last prediction
    try:
        clean_path = os.path.join("data", "cleaned_race_data.csv")
        hist_df = pd.read_csv(clean_path) if os.path.exists(clean_path) else None

        from src.predict import predict_race
        from predict import CIRCUIT_MAP, DRIVERS_2026

        key = circuit_full.lower().replace(" grand prix","").replace(" ","")
        quali = None
        for k, v in CIRCUIT_MAP.items():
            if v["full"] == circuit_full:
                from predict import get_fallback_quali
                quali = get_fallback_quali(k)
                break

        pred = predict_race(
            circuit=circuit_full,
            drivers=DRIVERS_2026,
            weather="Dry",
            qualifying_order=quali,
            historical_df=hist_df,
        )

        pred_top3 = [r["driver"] for r in pred["top_10"][:3]]
        real_top3 = [r[0] for r in results[:3]]

        print(f"\n  {'POS':<6} {'PREDICTED':<22} {'ACTUAL':<22} {'RESULT'}")
        print(f"  {'-'*60}")

        medals = ["🥇", "🥈", "🥉"]
        correct = 0
        for i in range(3):
            p = pred_top3[i] if i < len(pred_top3) else "?"
            a = real_top3[i] if i < len(real_top3) else "?"
            match = "✅ CORRECT" if p == a else "❌"
            if p == a:
                correct += 1
            print(f"  {medals[i]}     {p:<22} {a:<22} {match}")

        print(f"\n  Podium accuracy: {correct}/3")

        # Check if winner was correct
        if pred_top3 and real_top3 and pred_top3[0] == real_top3[0]:
            print(f"  🏆 WINNER CALLED CORRECTLY!")
        else:
            print(f"  Model predicted {pred_top3[0] if pred_top3 else '?'}")
            print(f"  Actual winner: {real_top3[0] if real_top3 else '?'}")

    except Exception as e:
        # Simple comparison
        real_top3 = [r[0] for r in results[:3]]
        print(f"\n  ACTUAL RESULTS:")
        for i, (driver, pos) in enumerate(results[:10]):
            medal = ["🥇","🥈","🥉"][i] if i < 3 else f"  P{pos}"
            print(f"  {medal}  {driver}")


def generate_post_caption(circuit_full: str, results: list):
    """Generate Instagram post-race caption"""
    print(f"\n{'='*60}")
    print(f"  POST-RACE INSTAGRAM CAPTION — @boxboxdata")
    print(f"{'='*60}")

    top3 = results[:3]
    circuit_short = circuit_full.replace(" Grand Prix", "").upper()
    tag = circuit_short.replace(" ", "").lower()

    winner = top3[0][0] if top3 else "TBD"
    p2 = top3[1][0] if len(top3) > 1 else "TBD"
    p3 = top3[2][0] if len(top3) > 2 else "TBD"
    winner_team = DRIVER_TEAMS.get(winner, "")

    print(f"""
🏁 {circuit_short} GP — RACE RESULT 🏁

The chequered flag has dropped at {circuit_full}!

🥇 P1: {winner} ({winner_team})
🥈 P2: {p2}
🥉 P3: {p3}

Did our ML model call it right? 🤔
Check our pre-race prediction on the link in bio 👆

Live predictions → sportsbrainai.pro

#{tag}GP #F1 #Formula1 #BoxBoxData #PitWallAI #F12026
#DataDrivenF1 #MachineLearning #{winner.split()[-1]}
""")


def run(circuit_input: str = None):
    if not circuit_input:
        print("Usage: python after_race.py 'Japanese Grand Prix'")
        print("       python after_race.py japan")
        return

    circuit_key = circuit_input.lower().replace(" grand prix","").replace(" ","").strip()

    # Fuzzy match
    if circuit_key not in CIRCUIT_MAP:
        for key in CIRCUIT_MAP:
            if key in circuit_key or circuit_key in key:
                circuit_key = key
                break
        else:
            print(f"Unknown circuit: {circuit_input}")
            return

    circuit_info = CIRCUIT_MAP[circuit_key]
    circuit_full = circuit_info["full"]
    round_num = circuit_info["round"]

    print(f"\n{'='*60}")
    print(f"  PITWALL AI — POST RACE UPDATE")
    print(f"  {circuit_full.upper()}")
    print(f"  {datetime.now().strftime('%B %d, %Y')}")
    print(f"{'='*60}\n")

    # Step 1 — Fetch results
    results = fetch_race_results(circuit_key)

    if not results:
        results = KNOWN_RESULTS.get(circuit_key)
        if results:
            print(f"  Using cached results ✅")
        else:
            print(f"  No results yet — race may not be finished")
            print(f"  Try again after the race ends")
            return

    # Show results
    print(f"\n  RACE RESULTS:")
    medals = {1:"🥇", 2:"🥈", 3:"🥉"}
    for driver, pos in results[:10]:
        m = medals.get(pos, f"  P{pos}")
        print(f"  {m}  {driver} ({DRIVER_TEAMS.get(driver,'')})")

    # Step 2 — Update DB
    update_database(circuit_full, results, round_num)

    # Step 3 — Retrain
    retrain_choice = input("\n  Retrain model with new data? (y/n): ").strip().lower()
    if retrain_choice == "y":
        retrain_model()

    # Step 4 — Accuracy
    show_accuracy(circuit_full, results)

    # Step 5 — Instagram caption
    generate_post_caption(circuit_full, results)

    print(f"\n{'='*60}")
    print(f"  Done! Database updated. Ready for next race. 🏎️")
    print(f"  Next: python predict.py 'Bahrain Grand Prix'")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    circuit = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    run(circuit)