"""
predict.py — ONE COMMAND DOES EVERYTHING
Usage: python predict.py "Japanese Grand Prix"
       python predict.py  (auto-detects next race)

Fetches qualifying automatically from OpenF1 API → runs prediction → prints results
"""

import sys
import os
import requests
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── CIRCUIT NAME MAPPING ──────────────────────────────────────────
CIRCUIT_MAP = {
    "japanese": {"full": "Japanese Grand Prix",    "openf1": "suzuka",       "country": "Japan"},
    "japan":    {"full": "Japanese Grand Prix",    "openf1": "suzuka",       "country": "Japan"},
    "suzuka":   {"full": "Japanese Grand Prix",    "openf1": "suzuka",       "country": "Japan"},
    "australian":{"full":"Australian Grand Prix",  "openf1": "albert_park",  "country": "Australia"},
    "australia":{"full": "Australian Grand Prix",  "openf1": "albert_park",  "country": "Australia"},
    "chinese":  {"full": "Chinese Grand Prix",     "openf1": "shanghai",     "country": "China"},
    "china":    {"full": "Chinese Grand Prix",     "openf1": "shanghai",     "country": "China"},
    "bahrain":  {"full": "Bahrain Grand Prix",     "openf1": "bahrain",      "country": "Bahrain"},
    "saudi":    {"full": "Saudi Arabian Grand Prix","openf1": "jeddah",      "country": "Saudi Arabia"},
    "miami":    {"full": "Miami Grand Prix",        "openf1": "miami",       "country": "USA"},
    "monaco":   {"full": "Monaco Grand Prix",       "openf1": "monaco",      "country": "Monaco"},
    "spanish":  {"full": "Spanish Grand Prix",      "openf1": "barcelona",   "country": "Spain"},
    "spain":    {"full": "Spanish Grand Prix",      "openf1": "barcelona",   "country": "Spain"},
    "canadian": {"full": "Canadian Grand Prix",     "openf1": "villeneuve",  "country": "Canada"},
    "canada":   {"full": "Canadian Grand Prix",     "openf1": "villeneuve",  "country": "Canada"},
    "british":  {"full": "British Grand Prix",      "openf1": "silverstone", "country": "UK"},
    "silverstone":{"full":"British Grand Prix",     "openf1": "silverstone", "country": "UK"},
    "belgian":  {"full": "Belgian Grand Prix",      "openf1": "spa",         "country": "Belgium"},
    "spa":      {"full": "Belgian Grand Prix",      "openf1": "spa",         "country": "Belgium"},
    "italian":  {"full": "Italian Grand Prix",      "openf1": "monza",       "country": "Italy"},
    "monza":    {"full": "Italian Grand Prix",      "openf1": "monza",       "country": "Italy"},
    "singapore":{"full": "Singapore Grand Prix",    "openf1": "marina_bay",  "country": "Singapore"},
    "lasvegas": {"full": "Las Vegas Grand Prix",    "openf1": "las_vegas",   "country": "USA"},
    "vegas":    {"full": "Las Vegas Grand Prix",    "openf1": "las_vegas",   "country": "USA"},
    "abudhabi": {"full": "Abu Dhabi Grand Prix",    "openf1": "yas_marina",  "country": "UAE"},
}

DRIVERS_2026 = [
    ("Kimi Antonelli",    "Mercedes"),
    ("George Russell",    "Mercedes"),
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

# OpenF1 driver number → name mapping
DRIVER_NUMBERS = {
    12: "Kimi Antonelli",
    63: "George Russell",
    16: "Charles Leclerc",
    44: "Lewis Hamilton",
    4:  "Lando Norris",
    81: "Oscar Piastri",
    1:  "Max Verstappen",
    6:  "Isack Hadjar",
    87: "Oliver Bearman",
    31: "Esteban Ocon",
    10: "Pierre Gasly",
    43: "Franco Colapinto",
    27: "Nico Hulkenberg",
    5:  "Gabriel Bortoleto",
    7:  "Arvid Lindblad",
    30: "Liam Lawson",
    14: "Fernando Alonso",
    18: "Lance Stroll",
    23: "Alexander Albon",
    55: "Carlos Sainz",
    11: "Sergio Perez",
    77: "Valtteri Bottas",
}


def fetch_qualifying(circuit_key: str) -> list:
    """Fetch real qualifying order from OpenF1 API"""
    openf1_name = CIRCUIT_MAP[circuit_key]["openf1"]

    print(f"  Fetching qualifying from OpenF1 API...")

    try:
        # Get session ID for qualifying
        sess_url = f"https://api.openf1.org/v1/sessions?year=2026&session_name=Qualifying&circuit_short_name={openf1_name}"
        sess_r = requests.get(sess_url, timeout=10)
        sessions = sess_r.json()

        if not sessions:
            raise ValueError("No qualifying session found")

        session_key = sessions[0]["session_key"]
        print(f"  Session key: {session_key} ✅")

        # Get qualifying results
        pos_url = f"https://api.openf1.org/v1/position?session_key={session_key}"
        pos_r = requests.get(pos_url, timeout=10)
        positions = pos_r.json()

        if not positions:
            raise ValueError("No position data found")

        # Get final positions (last entry per driver)
        final = {}
        for p in positions:
            dn = p.get("driver_number")
            pos = p.get("position")
            if dn and pos:
                final[dn] = pos

        # Sort by position
        sorted_drivers = sorted(final.items(), key=lambda x: x[1])
        quali_order = []
        for driver_num, pos in sorted_drivers:
            name = DRIVER_NUMBERS.get(driver_num)
            if name:
                quali_order.append(name)

        print(f"  Got {len(quali_order)} drivers from API ✅")
        return quali_order

    except Exception as e:
        print(f"  OpenF1 API unavailable: {e}")
        print(f"  Using latest known qualifying order...")
        return None


def get_fallback_quali(circuit_key: str) -> list:
    """Hardcoded latest known qualifying orders as fallback"""
    KNOWN_QUALI = {
        "japanese": [
            "Kimi Antonelli", "George Russell", "Oscar Piastri",
            "Charles Leclerc", "Lando Norris", "Lewis Hamilton",
            "Pierre Gasly", "Isack Hadjar", "Gabriel Bortoleto",
            "Arvid Lindblad", "Max Verstappen", "Esteban Ocon",
            "Nico Hulkenberg", "Liam Lawson", "Franco Colapinto",
            "Carlos Sainz", "Alexander Albon", "Oliver Bearman",
            "Sergio Perez", "Valtteri Bottas", "Fernando Alonso", "Lance Stroll",
        ],
        "chinese": [
            "Kimi Antonelli", "George Russell", "Oscar Piastri",
            "Lando Norris", "Charles Leclerc", "Lewis Hamilton",
            "Max Verstappen", "Pierre Gasly", "Isack Hadjar",
            "Gabriel Bortoleto", "Fernando Alonso", "Nico Hulkenberg",
            "Franco Colapinto", "Lance Stroll", "Esteban Ocon",
            "Liam Lawson", "Carlos Sainz", "Alexander Albon",
            "Arvid Lindblad", "Sergio Perez", "Oliver Bearman", "Valtteri Bottas",
        ],
        "australian": [
            "George Russell", "Kimi Antonelli", "Charles Leclerc",
            "Lewis Hamilton", "Lando Norris", "Oscar Piastri",
            "Max Verstappen", "Pierre Gasly", "Fernando Alonso",
            "Carlos Sainz", "Lance Stroll", "Isack Hadjar",
            "Nico Hulkenberg", "Gabriel Bortoleto", "Franco Colapinto",
            "Liam Lawson", "Arvid Lindblad", "Oliver Bearman",
            "Alexander Albon", "Sergio Perez", "Valtteri Bottas", "Esteban Ocon",
        ],
    }
    return KNOWN_QUALI.get(circuit_key)


def run(circuit_input: str = None):
    # Parse circuit input
    if not circuit_input:
        # Auto-detect next race from calendar
        circuit_input = "japanese"
        print(f"  No circuit specified — defaulting to Japanese GP")

    circuit_key = circuit_input.lower().replace(" grand prix", "").replace(" ", "").strip()

    if circuit_key not in CIRCUIT_MAP:
        # Fuzzy match
        for key in CIRCUIT_MAP:
            if key in circuit_key or circuit_key in key:
                circuit_key = key
                break
        else:
            print(f"  Unknown circuit: {circuit_input}")
            print(f"  Available: {', '.join(CIRCUIT_MAP.keys())}")
            return

    circuit_info = CIRCUIT_MAP[circuit_key]
    circuit_full = circuit_info["full"]

    print("\n" + "="*60)
    print(f"  PITWALL AI — RACE PREDICTION")
    print(f"  {circuit_full.upper()}")
    print(f"  {datetime.now().strftime('%B %d, %Y')}")
    print("="*60)

    # Fetch qualifying
    quali_order = fetch_qualifying(circuit_key)

    # Fallback if API fails
    if not quali_order:
        quali_order = get_fallback_quali(circuit_key)
        if quali_order:
            print(f"  Using cached qualifying data ✅")
        else:
            print(f"  No qualifying data — using form-based order")

    # Show qualifying
    if quali_order:
        print(f"\n  QUALIFYING ORDER:")
        for i, d in enumerate(quali_order[:10], 1):
            print(f"    P{i:2}  {d}")
        print(f"    ...")

    # Load historical data
    clean_path = os.path.join(os.path.dirname(__file__), "data", "cleaned_race_data.csv")
    hist_df = pd.read_csv(clean_path) if os.path.exists(clean_path) else None

    # Run prediction
    print(f"\n  Running ML model...")
    from src.predict import predict_race, format_prediction_output
    pred = predict_race(
        circuit=circuit_full,
        drivers=DRIVERS_2026,
        weather="Dry",
        qualifying_order=quali_order,
        historical_df=hist_df,
        explain=True,
    )

    print(format_prediction_output(pred))

    # Instagram caption
    print(f"\n{'='*60}")
    print(f"  INSTAGRAM CAPTION — @boxboxdata")
    print(f"{'='*60}")
    try:
        from ingestion.llm_reasoning import LLMReasoning
        reasoner = LLMReasoning(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        caption = reasoner.generate_race_preview_post(circuit_full, pred, "Dry", "instagram")
        print(caption)
    except Exception as e:
        top3 = pred["top_10"][:3]
        print(f"🏎️ {circuit_full.upper().replace(' GRAND PRIX','')} GP — ML PREDICTION 🔮\n")
        print(f"🥇 P1: {top3[0]['driver']} ({top3[0]['win_prob']*100:.1f}%)")
        print(f"🥈 P2: {top3[1]['driver']} ({top3[1]['win_prob']*100:.1f}%)")
        print(f"🥉 P3: {top3[2]['driver']} ({top3[2]['win_prob']*100:.1f}%)")
        print(f"\n#F1 #{circuit_key.title()}GP #Formula1 #BoxBoxData #PitWallAI")


if __name__ == "__main__":
    circuit = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    run(circuit)