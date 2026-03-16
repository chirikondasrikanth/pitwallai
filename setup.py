#!/usr/bin/env python3
"""
setup.py — One-command setup for F1 Intelligence Platform
Generates synthetic data, cleans it, engineers features, and trains all models.
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def step(msg):
    print(f"\n  → {msg}...")

def success(msg):
    print(f"  ✅ {msg}")


if __name__ == "__main__":
    header("F1 Intelligence Platform — Setup")
    
    # Step 1: Generate data
    step("Generating historical race dataset (2024–2025)")
    exec(open(os.path.join(BASE_DIR, "generate_data.py"), encoding="utf-8").read())
    success("Raw data generated: data/raw_race_data.csv")
    
    # Step 2: Clean data
    step("Cleaning and normalizing dataset")
    from src.data_cleaner import clean_dataset
    df = clean_dataset(
        os.path.join(BASE_DIR, "data", "raw_race_data.csv"),
        os.path.join(BASE_DIR, "data", "cleaned_race_data.csv"),
    )
    success(f"Cleaned dataset: {len(df)} rows → data/cleaned_race_data.csv")
    
    # Step 3: Train models
    step("Training ML models (RandomForest + XGBoost)")
    from src.train_model import train_pipeline
    _, _, _, _, metrics = train_pipeline(
        os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
    )
    success(f"Models trained → models/")
    success(f"  Podium AUC: {metrics['podium_auc']:.4f}")
    success(f"  Position MAE: {metrics['position_mae']:.2f}")
    
    # Step 4: Run sample prediction
    step("Running sample prediction — Australian Grand Prix")
    import pandas as pd
    from src.predict import predict_race, format_prediction_output
    
    hist_df = pd.read_csv(os.path.join(BASE_DIR, "data", "cleaned_race_data.csv"))
    
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
    
    pred = predict_race(
        circuit="Australian Grand Prix",
        drivers=DRIVERS_2026,
        weather="Dry",
        qualifying_order=["Charles Leclerc", "Lando Norris", "Max Verstappen",
                          "Oscar Piastri", "Lewis Hamilton"] + [d for d, t in DRIVERS_2026[5:]],
        historical_df=hist_df,
    )
    print(format_prediction_output(pred))
    
    header("Setup Complete!")
    print("""
  To launch the dashboard, run:
  
    streamlit run dashboard/app.py
    
  Then open http://localhost:8501 in your browser.
    """)
