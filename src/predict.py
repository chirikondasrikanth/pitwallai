"""
predict.py
Circuit-based race prediction engine with SHAP explanations.
Generates top-10 finishing order, podium probabilities, winner, and underdogs.
"""

import os
import sys
import json
import joblib
import logging
import numpy as np
import pandas as pd
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.feature_engineering import build_features, FEATURE_COLS

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")


def load_models():
    podium_model = joblib.load(os.path.join(MODELS_DIR, "podium_model.pkl"))
    win_model = joblib.load(os.path.join(MODELS_DIR, "win_model.pkl"))
    pos_model = joblib.load(os.path.join(MODELS_DIR, "position_model.pkl"))
    with open(os.path.join(MODELS_DIR, "model_meta.json")) as f:
        meta = json.load(f)
    return podium_model, win_model, pos_model, meta["feature_cols"]


def build_race_input(
    circuit: str,
    drivers: list,
    weather: str = "Dry",
    qualifying_order: list = None,
    historical_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """Build prediction DataFrame using enriched features if available."""
    rows = []
    for i, (driver, team) in enumerate(drivers):
        qual_pos = (qualifying_order.index(driver) + 1) if qualifying_order and driver in qualifying_order else (i + 1)
        rows.append({
            "season": 2026, "round": 99,
            "circuit": circuit,
            "location": circuit.replace(" Grand Prix", "").replace(" GP", ""),
            "driver": driver, "team": team,
            "qualifying_position": qual_pos,
            "pole_position": 1 if qual_pos == 1 else 0,
            "finish_position": qual_pos,
            "weather": weather, "tire_strategy": "2-Stop",
            "pit_stops": 2, "incidents": 0, "penalties": 0,
            "points": 0, "podium": 0, "win": 0,
        })

    pred_df = pd.DataFrame(rows)

    enriched_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "enriched_features.csv"
    )

    if os.path.exists(enriched_path):
        enriched_hist = pd.read_csv(enriched_path)
        latest_enriched = enriched_hist.sort_values(
            ["season", "round"]
        ).groupby("driver").last().reset_index()

        enrich_cols = [
            "expert_confidence_score", "expert_sentiment_score",
            "reg_power_unit_impact", "reg_aero_impact", "reg_combined_impact",
            "circuit_win_rate", "circuit_podium_rate", "circuit_performance_index",
            "circuit_appearances", "driver_form_momentum_score", "points_momentum",
            "team_upgrade_trajectory", "h2h_qual_win_rate", "h2h_race_win_rate",
            "combined_performance_index",
        ]
        available_enrich = [c for c in enrich_cols if c in latest_enriched.columns]

        pred_df = pred_df.merge(
            latest_enriched[["driver"] + available_enrich],
            on="driver", how="left"
        )

        defaults = {
            "expert_confidence_score": 0.5, "expert_sentiment_score": 0.0,
            "reg_power_unit_impact": 0.5, "reg_aero_impact": 0.5,
            "reg_combined_impact": 0.5, "circuit_win_rate": 0.0,
            "circuit_podium_rate": 0.0, "circuit_performance_index": 0.5,
            "circuit_appearances": 0, "driver_form_momentum_score": 0.5,
            "points_momentum": 0.0, "team_upgrade_trajectory": 0.0,
            "h2h_qual_win_rate": 0.5, "h2h_race_win_rate": 0.5,
            "combined_performance_index": 0.5,
        }
        for col, default in defaults.items():
            if col in pred_df.columns:
                pred_df[col] = pred_df[col].fillna(default)

        base_cols = [c for c in pred_df.columns if c not in available_enrich]
        if historical_df is not None:
            combined = pd.concat([historical_df, pred_df[base_cols]], ignore_index=True)
        else:
            combined = pred_df[base_cols].copy()

        combined = build_features(combined)
        pred_feats = combined[combined["round"] == 99].copy()

        for col in available_enrich:
            if col in pred_df.columns:
                pred_feats[col] = pred_df[col].values

        for col in ["driver", "team", "circuit", "weather"]:
            if col in pred_feats.columns:
                pred_feats[f"{col}_encoded"] = pd.Categorical(pred_feats[col]).codes

        if "qualifying_gap" not in pred_feats.columns:
            max_pos = pred_feats["qualifying_position"].max()
            pred_feats["qualifying_gap"] = (
                (pred_feats["qualifying_position"] - 1) / max(max_pos - 1, 1)
            ).clip(0, 1)

        if "weather_encoded" not in pred_feats.columns:
            pred_feats["weather_encoded"] = pred_feats["weather"].map(
                {"Dry": 0, "Mixed": 1, "Wet": 2}
            ).fillna(0).astype(int)

        return pred_feats

    else:
        if historical_df is not None:
            combined = pd.concat([historical_df, pred_df], ignore_index=True)
            combined = build_features(combined)
            return combined[combined["round"] == 99].copy()
        else:
            return build_features(pred_df)


def predict_race(
    circuit: str,
    drivers: list,
    weather: str = "Dry",
    qualifying_order: list = None,
    historical_df: pd.DataFrame = None,
    explain: bool = True,
) -> dict:
    """
    Returns full race prediction dict:
      - top_10: ordered list with driver, team, predicted_position, podium_prob, win_prob
      - winner: dict
      - underdogs: list
      - explanations: per-driver SHAP explanations
    """
    podium_model, win_model, pos_model, feature_cols = load_models()
    
    pred_df = build_race_input(circuit, drivers, weather, qualifying_order, historical_df)
    
    # Ensure all feature cols exist
    available_features = [c for c in feature_cols if c in pred_df.columns]
    X = pred_df[available_features].fillna(0).astype(float)
    
    # Predictions
    podium_probs = podium_model.predict_proba(X)[:, 1]
    win_probs = win_model.predict_proba(X)[:, 1]
    
    # Normalize win probs to sum to 1
    win_probs = win_probs / (win_probs.sum() + 1e-9)
    podium_probs_norm = podium_probs / (podium_probs.sum() + 1e-9) * 3  # 3 podium spots
    
    pos_predictions = pos_model.predict(X)
    
    # Build results
    results = []
    for i, (driver, team) in enumerate(drivers):
        results.append({
            "driver": driver,
            "team": team,
            "predicted_position": float(pos_predictions[i]),
            "podium_prob": float(podium_probs[i]),
            "win_prob": float(win_probs[i]),
            "qualifying_position": int(pred_df.iloc[i]["qualifying_position"]) if i < len(pred_df) else i+1,
        })
    
    # Sort by predicted position
    results.sort(key=lambda x: x["predicted_position"])
    
    # Re-rank top-10
    for rank, r in enumerate(results[:10], 1):
        r["predicted_rank"] = rank
    
    winner = results[0]
    
    # Underdogs: drivers qualifying > 8th but with high podium prob
    underdogs = [
        r for r in results
        if r["qualifying_position"] > 8 and r["podium_prob"] > 0.15
    ]
    underdogs.sort(key=lambda x: x["podium_prob"], reverse=True)
    
    # SHAP Explanations
    explanations = {}
    if explain and HAS_SHAP:
        try:
            explainer = shap.TreeExplainer(podium_model)
            shap_values = explainer.shap_values(X)
            # For binary classifier, take class=1 SHAP values
            if isinstance(shap_values, list):
                sv = shap_values[1]
            else:
                sv = shap_values
            
            for i, (driver, team) in enumerate(drivers):
                driver_shap = dict(zip(available_features, sv[i]))
                top_pos = sorted(driver_shap.items(), key=lambda x: x[1], reverse=True)[:4]
                top_neg = sorted(driver_shap.items(), key=lambda x: x[1])[:2]
                explanations[driver] = {
                    "positive_factors": top_pos,
                    "negative_factors": top_neg,
                }
        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}")
            explanations = generate_rule_based_explanations(results, pred_df, circuit, weather)
    else:
        explanations = generate_rule_based_explanations(results, pred_df, circuit, weather)
    
    return {
        "circuit": circuit,
        "weather": weather,
        "top_10": results[:10],
        "full_grid": results,
        "winner": winner,
        "underdogs": underdogs[:3],
        "explanations": explanations,
        "feature_importances": get_feature_importances(podium_model, available_features),
    }


def generate_rule_based_explanations(results, pred_df, circuit, weather):
    """Fallback rule-based explanations when SHAP unavailable."""
    explanations = {}
    for r in results[:5]:
        driver = r["driver"]
        factors = []
        
        if r["qualifying_position"] == 1:
            factors.append("Starting from pole position — historically strong advantage")
        elif r["qualifying_position"] <= 3:
            factors.append(f"Strong qualifying (P{r['qualifying_position']}) provides front-row advantage")
        
        if r["win_prob"] > 0.25:
            factors.append("High historical win rate at similar circuits")
        
        row = pred_df[pred_df["driver"] == driver]
        if not row.empty:
            form = row.iloc[0].get("driver_recent_form", 0.5)
            if form > 0.7:
                factors.append("Excellent recent form — performing consistently well")
            circ = row.iloc[0].get("circuit_perf_score", 0.5)
            if circ > 0.7:
                factors.append(f"Strong historical performance at {circuit}")
            team_trend = row.iloc[0].get("team_performance_trend", 0.5)
            if team_trend > 0.7:
                factors.append("Car showing strong pace this season")
        
        if weather == "Wet":
            factors.append("Weather conditions may create unpredictability — driver wet-weather skill is key")
        
        if not factors:
            factors.append("Competitive package expected to challenge for points")
        
        explanations[driver] = {"factors": factors}
    
    return explanations


def get_feature_importances(model, feature_cols):
    try:
        fi = model.feature_importances_
        return sorted(zip(feature_cols, fi.tolist()), key=lambda x: x[1], reverse=True)[:8]
    except Exception:
        return []


def format_prediction_output(pred: dict) -> str:
    """Human-readable prediction summary."""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  🏁 RACE PREDICTION: {pred['circuit'].upper()}")
    lines.append(f"  Weather: {pred['weather']}")
    lines.append(f"{'='*60}")
    
    lines.append("\n📊 PREDICTED TOP 10 FINISHING ORDER:")
    lines.append(f"  {'Pos':<5} {'Driver':<22} {'Team':<18} {'Podium%':<10} {'Win%'}")
    lines.append(f"  {'-'*65}")
    for r in pred["top_10"]:
        lines.append(
            f"  P{r['predicted_rank']:<4} {r['driver']:<22} {r['team']:<18} "
            f"{r['podium_prob']*100:.1f}%{'':6} {r['win_prob']*100:.1f}%"
        )
    
    w = pred["winner"]
    lines.append(f"\n🏆 PREDICTED WINNER: {w['driver']} ({w['team']})")
    lines.append(f"   Win probability: {w['win_prob']*100:.1f}%")
    lines.append(f"   Qualifying position: P{w['qualifying_position']}")
    
    if pred["underdogs"]:
        lines.append(f"\n⚡ POTENTIAL SURPRISES:")
        for u in pred["underdogs"]:
            lines.append(f"  • {u['driver']} (starts P{u['qualifying_position']}, podium prob: {u['podium_prob']*100:.1f}%)")
    
    lines.append(f"\n💡 KEY PREDICTION FACTORS:")
    winner_name = pred["winner"]["driver"]
    exp = pred["explanations"].get(winner_name, {})
    factors = exp.get("factors", [])
    if not factors:
        pos_factors = exp.get("positive_factors", [])
        factors = [f"{k.replace('_', ' ').title()}" for k, v in pos_factors[:4]]
    for f in factors[:5]:
        lines.append(f"  • {f}")
    
    lines.append(f"\n{'='*60}\n")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    historical_df = pd.read_csv(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "cleaned_race_data.csv"
    ))
    
    DRIVERS_2026 = [
        ("Max Verstappen", "Red Bull"), ("Liam Lawson", "Red Bull"),
        ("Lewis Hamilton", "Ferrari"), ("Charles Leclerc", "Ferrari"),
        ("George Russell", "Mercedes"), ("Kimi Antonelli", "Mercedes"),
        ("Lando Norris", "McLaren"), ("Oscar Piastri", "McLaren"),
        ("Fernando Alonso", "Aston Martin"), ("Lance Stroll", "Aston Martin"),
        ("Pierre Gasly", "Alpine"), ("Jack Doohan", "Alpine"),
        ("Nico Hulkenberg", "Kick Sauber"), ("Gabriel Bortoleto", "Kick Sauber"),
        ("Yuki Tsunoda", "RB"), ("Isack Hadjar", "RB"),
        ("Oliver Bearman", "Haas"), ("Esteban Ocon", "Haas"),
        ("Alexander Albon", "Williams"), ("Carlos Sainz", "Williams"),
    ]
    
    result = predict_race(
        circuit="Australian Grand Prix",
        drivers=DRIVERS_2026,
        weather="Dry",
        qualifying_order=["Charles Leclerc", "Lando Norris", "Max Verstappen",
                          "Oscar Piastri", "Lewis Hamilton", "George Russell",
                          "Carlos Sainz", "Fernando Alonso", "Yuki Tsunoda",
                          "Alexander Albon"] + [d for d, t in DRIVERS_2026[10:]],
        historical_df=historical_df,
    )
    print(format_prediction_output(result))
