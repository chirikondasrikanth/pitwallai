"""
scheduler.py — Automated Race Data Pipeline
Runs automatically via GitHub Actions after every race weekend.
Can also run locally: python scheduler.py
"""
import os, sys, requests, json, subprocess
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DRIVER_NUMBERS = {
    12:"Kimi Antonelli", 63:"George Russell", 16:"Charles Leclerc",
    44:"Lewis Hamilton", 4:"Lando Norris", 81:"Oscar Piastri",
    1:"Max Verstappen", 6:"Isack Hadjar", 87:"Oliver Bearman",
    31:"Esteban Ocon", 10:"Pierre Gasly", 43:"Franco Colapinto",
    27:"Nico Hulkenberg", 5:"Gabriel Bortoleto", 7:"Arvid Lindblad",
    30:"Liam Lawson", 14:"Fernando Alonso", 18:"Lance Stroll",
    23:"Alexander Albon", 55:"Carlos Sainz", 11:"Sergio Perez", 77:"Valtteri Bottas",
}

DRIVER_TEAMS = {
    "Kimi Antonelli":"Mercedes","George Russell":"Mercedes",
    "Charles Leclerc":"Ferrari","Lewis Hamilton":"Ferrari",
    "Lando Norris":"McLaren","Oscar Piastri":"McLaren",
    "Max Verstappen":"Red Bull","Isack Hadjar":"Red Bull",
    "Oliver Bearman":"Haas","Esteban Ocon":"Haas",
    "Pierre Gasly":"Alpine","Franco Colapinto":"Alpine",
    "Nico Hulkenberg":"Audi","Gabriel Bortoleto":"Audi",
    "Arvid Lindblad":"Racing Bulls","Liam Lawson":"Racing Bulls",
    "Fernando Alonso":"Aston Martin","Lance Stroll":"Aston Martin",
    "Alexander Albon":"Williams","Carlos Sainz":"Williams",
    "Sergio Perez":"Cadillac","Valtteri Bottas":"Cadillac",
}

# 2026 Race calendar with OpenF1 circuit names
CALENDAR_2026 = [
    {"round":1, "name":"Australian Grand Prix",     "openf1":"albert_park", "date":"2026-03-15"},
    {"round":2, "name":"Chinese Grand Prix",         "openf1":"shanghai",    "date":"2026-03-22"},
    {"round":3, "name":"Japanese Grand Prix",        "openf1":"suzuka",      "date":"2026-03-29"},
    {"round":4, "name":"Bahrain Grand Prix",         "openf1":"bahrain",     "date":"2026-04-12"},
    {"round":5, "name":"Saudi Arabian Grand Prix",   "openf1":"jeddah",      "date":"2026-04-19"},
    {"round":6, "name":"Miami Grand Prix",           "openf1":"miami",       "date":"2026-05-03"},
    {"round":7, "name":"Emilia Romagna Grand Prix",  "openf1":"imola",       "date":"2026-05-17"},
    {"round":8, "name":"Monaco Grand Prix",          "openf1":"monaco",      "date":"2026-05-24"},
    {"round":9, "name":"Spanish Grand Prix",         "openf1":"barcelona",   "date":"2026-06-01"},
    {"round":10,"name":"Canadian Grand Prix",        "openf1":"villeneuve",  "date":"2026-06-14"},
    {"round":11,"name":"Austrian Grand Prix",        "openf1":"red_bull_ring","date":"2026-06-28"},
    {"round":12,"name":"British Grand Prix",         "openf1":"silverstone", "date":"2026-07-05"},
    {"round":13,"name":"Belgian Grand Prix",         "openf1":"spa",         "date":"2026-07-26"},
    {"round":14,"name":"Hungarian Grand Prix",       "openf1":"hungaroring", "date":"2026-08-02"},
    {"round":15,"name":"Dutch Grand Prix",           "openf1":"zandvoort",   "date":"2026-08-30"},
    {"round":16,"name":"Italian Grand Prix",         "openf1":"monza",       "date":"2026-09-06"},
    {"round":17,"name":"Azerbaijan Grand Prix",      "openf1":"baku",        "date":"2026-09-20"},
    {"round":18,"name":"Singapore Grand Prix",       "openf1":"marina_bay",  "date":"2026-10-04"},
    {"round":19,"name":"United States Grand Prix",   "openf1":"americas",    "date":"2026-10-18"},
    {"round":20,"name":"Mexico City Grand Prix",     "openf1":"rodriguez",   "date":"2026-10-25"},
    {"round":21,"name":"São Paulo Grand Prix",       "openf1":"interlagos",  "date":"2026-11-08"},
    {"round":22,"name":"Las Vegas Grand Prix",       "openf1":"las_vegas",   "date":"2026-11-21"},
    {"round":23,"name":"Qatar Grand Prix",           "openf1":"losail",      "date":"2026-11-29"},
    {"round":24,"name":"Abu Dhabi Grand Prix",       "openf1":"yas_marina",  "date":"2026-12-06"},
]


def get_latest_completed_race():
    """Find the most recently completed race from OpenF1"""
    today = datetime.now().strftime("%Y-%m-%d")
    completed = [r for r in CALENDAR_2026 if r["date"] <= today]
    return completed[-1] if completed else None


def fetch_session_key(openf1_name: str, session_type: str = "Race") -> int:
    """Get OpenF1 session key"""
    url = f"https://api.openf1.org/v1/sessions?year=2026&session_name={session_type}&circuit_short_name={openf1_name}"
    r = requests.get(url, timeout=15)
    sessions = r.json()
    return sessions[0]["session_key"] if sessions else None


def fetch_results(openf1_name: str, session_type: str = "Race") -> list:
    """Fetch race or qualifying results from OpenF1"""
    session_key = fetch_session_key(openf1_name, session_type)
    if not session_key:
        return []

    pos_r = requests.get(f"https://api.openf1.org/v1/position?session_key={session_key}", timeout=15)
    positions = pos_r.json()

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
            results.append({"driver": name, "team": DRIVER_TEAMS.get(name,""), "position": pos})
    return results


def update_database(race: dict, results: list):
    """Save race results to database"""
    try:
        import sqlite3
        db_path = os.path.join("data", "pitwall.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS race_results_2026 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round INTEGER, circuit TEXT, driver TEXT, team TEXT,
            finish_position INTEGER, season INTEGER DEFAULT 2026,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        # Remove existing entries for this race
        c.execute("DELETE FROM race_results_2026 WHERE round=? AND season=2026", (race["round"],))

        for r in results:
            c.execute("""INSERT INTO race_results_2026
                (round, circuit, driver, team, finish_position)
                VALUES (?,?,?,?,?)""",
                (race["round"], race["name"], r["driver"], r["team"], r["position"]))

        conn.commit()
        conn.close()
        print(f"  ✅ {len(results)} results saved to database")
        return True
    except Exception as e:
        print(f"  ❌ DB error: {e}")
        return False


def retrain_model():
    """Retrain ML model with latest data"""
    print("  Rebuilding features...")
    subprocess.run(["python", "ingestion/run_ingestion.py", "--features"],
                   capture_output=True, timeout=120)
    print("  Retraining model...")
    result = subprocess.run(["python", "src/train_model.py"],
                            capture_output=True, text=True, timeout=300)
    if result.returncode == 0:
        print("  ✅ Model retrained successfully")
    else:
        print(f"  ⚠️  Retrain issue: {result.stderr[-100:]}")


def fetch_next_quali_and_predict(next_race: dict):
    """Fetch qualifying for next race and generate prediction"""
    try:
        quali = fetch_results(next_race["openf1"], "Qualifying")
        if not quali:
            return None

        quali_order = [r["driver"] for r in quali]

        from src.predict import predict_race
        import pandas as pd

        clean_path = os.path.join("data", "cleaned_race_data.csv")
        hist_df = pd.read_csv(clean_path) if os.path.exists(clean_path) else None

        from src.utils import DRIVERS_2026
        pred = predict_race(
            circuit=next_race["name"],
            drivers=DRIVERS_2026,
            weather="Dry",
            qualifying_order=quali_order,
            historical_df=hist_df,
            explain=True,
        )

        # Save prediction to file
        pred_path = os.path.join("data", "latest_prediction.json")
        save_data = {
            "circuit": next_race["name"],
            "round": next_race["round"],
            "generated_at": datetime.now().isoformat(),
            "quali_order": quali_order,
            "winner": pred["top_10"][0]["driver"] if pred["top_10"] else "",
            "top_3": [r["driver"] for r in pred["top_10"][:3]],
            "top_10": pred["top_10"],
        }
        with open(pred_path, "w") as f:
            json.dump(save_data, f, indent=2)

        print(f"  ✅ Prediction saved: {save_data['winner']} to win")
        return save_data
    except Exception as e:
        print(f"  ⚠️  Prediction error: {e}")
        return None


def send_email_notifications(race: dict, results: list, prediction: dict = None):
    """Send race recap email to all subscribers"""
    smtp_user = os.environ.get("EMAIL_USER", "")
    smtp_pass = os.environ.get("EMAIL_PASS", "")
    subscribers_path = os.path.join("data", "subscribers.json")

    if not smtp_user or not smtp_pass:
        print("  ⚠️  Email not configured (set EMAIL_USER + EMAIL_PASS env vars)")
        return

    if not os.path.exists(subscribers_path):
        print("  ⚠️  No subscribers yet")
        return

    with open(subscribers_path) as f:
        subscribers = json.load(f)

    if not subscribers:
        return

    top3 = results[:3]
    winner = top3[0]["driver"] if top3 else "TBD"
    p2 = top3[1]["driver"] if len(top3) > 1 else "TBD"
    p3 = top3[2]["driver"] if len(top3) > 2 else "TBD"

    pred_text = ""
    if prediction:
        pred_top3 = prediction.get("top_3", [])
        correct = sum(1 for i, d in enumerate(pred_top3[:3]) if i < len(top3) and d == top3[i]["driver"])
        pred_text = f"""
        <h3>🤖 How Our ML Model Did</h3>
        <p>Predicted podium: {', '.join(pred_top3[:3])}</p>
        <p>Actual podium: {winner}, {p2}, {p3}</p>
        <p><strong>Accuracy: {correct}/3 correct</strong></p>
        """

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#08090E;color:#E8E4D8;padding:24px;">
    <div style="max-width:600px;margin:0 auto;">
    <div style="background:#0D0E16;border:1px solid rgba(201,168,76,0.3);border-radius:16px;padding:32px;">

    <h1 style="font-family:monospace;color:#C9A84C;letter-spacing:3px;">PITWALL AI</h1>
    <h2 style="color:#E8E4D8;">{race['name']} — Race Recap</h2>

    <div style="background:#0A0B12;border-radius:12px;padding:20px;margin:20px 0;">
        <h3 style="color:#C9A84C;">🏆 Race Results</h3>
        <p>🥇 <strong>{winner}</strong></p>
        <p>🥈 <strong>{p2}</strong></p>
        <p>🥉 <strong>{p3}</strong></p>
    </div>

    {pred_text}

    <div style="margin-top:24px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06);">
        <p style="color:rgba(232,228,216,0.4);font-size:0.8rem;">
        View full analysis at <a href="https://sportsbrainai.pro" style="color:#C9A84C;">sportsbrainai.pro</a>
        </p>
    </div>
    </div></div></body></html>
    """

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(smtp_user, smtp_pass)

        sent = 0
        for sub in subscribers:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🏁 {race['name']} Results — PitWall AI"
            msg["From"] = smtp_user
            msg["To"] = sub["email"]
            msg.attach(MIMEText(html, "html"))
            server.sendmail(smtp_user, sub["email"], msg.as_string())
            sent += 1

        server.quit()
        print(f"  ✅ Emails sent to {sent} subscribers")
    except Exception as e:
        print(f"  ❌ Email error: {e}")


def run():
    print(f"\n{'='*60}")
    print(f"  PITWALL AI — AUTOMATED SCHEDULER")
    print(f"  {datetime.now().strftime('%B %d, %Y %H:%M UTC')}")
    print(f"{'='*60}\n")

    # Find latest completed race
    latest = get_latest_completed_race()
    if not latest:
        print("  No completed races yet in 2026")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"  Latest race: {latest['name']} ({latest['date']})")

    # Step 1 — Fetch race results
    print(f"\n  [1/5] Fetching race results...")
    results = fetch_results(latest["openf1"], "Race")
    if results:
        print(f"  Winner: {results[0]['driver']} ✅")
        for r in results[:3]:
            medal = ["🥇","🥈","🥉"][r["position"]-1]
            print(f"    {medal} {r['driver']}")
    else:
        print(f"  ⚠️  Results not available yet — race may still be running")
        return

    # Step 2 — Update database
    print(f"\n  [2/5] Updating database...")
    update_database(latest, results)

    # Step 3 — Retrain model
    print(f"\n  [3/5] Retraining model...")
    retrain_model()

    # Step 4 — Predict next race
    print(f"\n  [4/5] Predicting next race...")
    completed_rounds = {r["round"] for r in CALENDAR_2026 if r["date"] <= today}
    upcoming = [r for r in CALENDAR_2026 if r["round"] not in completed_rounds]
    prediction = None
    if upcoming:
        next_race = upcoming[0]
        print(f"  Next race: {next_race['name']}")
        prediction = fetch_next_quali_and_predict(next_race)
    else:
        print("  Season complete!")

    # Step 5 — Send email notifications
    print(f"\n  [5/5] Sending email notifications...")
    send_email_notifications(latest, results, prediction)

    print(f"\n{'='*60}")
    print(f"  ✅ All done! sportsbrainai.pro is updated.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
