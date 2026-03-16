"""
ingestion/llm_reasoning.py
LLM Reasoning Layer — uses Claude API to generate natural language
explanations for every F1 race prediction.

Takes structured prediction data + enriched features and produces:
  - Plain English race preview
  - Per-driver prediction reasoning
  - Strategy insights
  - Risk factors
  - Confidence narrative

Uses: Anthropic Claude API (claude-sonnet-4-20250514)
Fallback: Rule-based template reasoning (no API key needed)
"""

import os
import sys
import json
import logging
import requests
import pandas as pd
import numpy as np
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

BASE_DIR     = os.path.dirname(os.path.dirname(__file__))
ENRICHED_CSV = os.path.join(BASE_DIR, "data", "enriched_features.csv")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL             = "claude-sonnet-4-20250514"


class LLMReasoning:
    """
    Generates natural language explanations for F1 predictions.
    Uses Claude API when key is available, falls back to
    rule-based template engine otherwise.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.has_api = bool(self.api_key and self.api_key.startswith("sk-ant"))
        self._enriched_df = None

        if self.has_api:
            logger.info("Claude API available — using LLM reasoning")
        else:
            logger.info("No API key — using rule-based reasoning engine")

    def _load_enriched(self) -> pd.DataFrame:
        if self._enriched_df is None:
            if os.path.exists(ENRICHED_CSV):
                self._enriched_df = pd.read_csv(ENRICHED_CSV)
            else:
                self._enriched_df = pd.DataFrame()
        return self._enriched_df

    # ── PUBLIC API ────────────────────────────────────────────────

    def explain_race_prediction(
        self,
        circuit: str,
        prediction: dict,
        weather: str = "Dry",
        season: int = 2026,
    ) -> dict:
        """
        Generate full race explanation for a circuit prediction.

        Args:
            circuit:    Circuit name e.g. "Japanese Grand Prix"
            prediction: Dict from predict.py with top_10, winner, underdogs
            weather:    Race weather condition
            season:     Season year

        Returns:
            Dict with:
              race_preview      — 2-3 sentence race intro
              winner_reasoning  — why the predicted winner is picked
              podium_reasoning  — P2 and P3 analysis
              dark_horses       — underdog reasoning
              strategy_insight  — tire/pit strategy factors
              risk_factors      — what could upset the prediction
              confidence_level  — HIGH / MEDIUM / LOW with reason
              driver_summaries  — per-driver 1-line explanation
        """
        enriched = self._load_enriched()
        driver_data = self._get_driver_enriched_data(
            prediction.get("top_10", []), enriched, circuit, season
        )

        if self.has_api:
            return self._llm_explain(circuit, prediction, weather, season, driver_data)
        else:
            return self._rule_based_explain(circuit, prediction, weather, season, driver_data)

    def explain_driver(
        self,
        driver_name: str,
        circuit: str,
        prediction_rank: int,
        season: int = 2026,
    ) -> str:
        """Single driver explanation — used in dashboard cards."""
        enriched = self._load_enriched()
        driver_row = enriched[
            enriched["driver"].str.lower().str.contains(
                driver_name.split()[-1].lower(), na=False
            )
        ]

        if driver_row.empty:
            return f"{driver_name} prediction based on current season form and qualifying pace."

        row = driver_row.sort_values(["season","round"]).iloc[-1]

        if self.has_api:
            return self._llm_driver_explanation(driver_name, circuit, prediction_rank, row)
        else:
            return self._rule_driver_explanation(driver_name, circuit, prediction_rank, row)

    def generate_race_preview_post(
        self,
        circuit: str,
        prediction: dict,
        weather: str = "Dry",
        platform: str = "instagram",
    ) -> str:
        """
        Generate social media ready race preview post.
        Platform: instagram, twitter, linkedin
        """
        explanation = self.explain_race_prediction(circuit, prediction, weather)

        if self.has_api:
            return self._llm_social_post(circuit, prediction, explanation, platform)
        else:
            return self._rule_social_post(circuit, prediction, explanation, platform)

    # ── LLM ENGINE (Claude API) ───────────────────────────────────

    def _llm_explain(
        self, circuit, prediction, weather, season, driver_data
    ) -> dict:
        """Call Claude API for full race explanation."""
        top_10     = prediction.get("top_10", [])[:5]
        winner     = prediction.get("winner", {})
        underdogs  = prediction.get("dark_horses", prediction.get("underdogs", []))

        prompt = f"""You are an expert Formula 1 analyst. Generate a structured prediction 
explanation for the {season} {circuit}.

RACE CONDITIONS:
- Circuit: {circuit}
- Weather: {weather}
- Season: {season}

PREDICTED RESULTS (from ML model):
{json.dumps([{
    'position': r.get('predicted_rank', i+1),
    'driver': r['driver'],
    'team': r['team'],
    'win_probability': f"{r['win_prob']*100:.1f}%",
    'podium_probability': f"{r['podium_prob']*100:.1f}%",
    'qualifying_position': r.get('qualifying_position', 'N/A'),
} for i, r in enumerate(top_10)], indent=2)}

ENRICHED DRIVER DATA:
{json.dumps(driver_data, indent=2)}

Generate a JSON response with exactly these fields:
{{
  "race_preview": "2-3 sentence intro about this race prediction",
  "winner_reasoning": "2-3 sentences explaining why {winner.get('driver','the predicted winner')} is picked to win",
  "podium_reasoning": "1-2 sentences on P2 and P3 picks",
  "dark_horses": "1-2 sentences on drivers who could surprise",
  "strategy_insight": "1-2 sentences on tire/pit strategy factors",
  "risk_factors": "1-2 sentences on what could upset the prediction",
  "confidence_level": "HIGH, MEDIUM, or LOW",
  "confidence_reason": "One sentence explaining confidence level",
  "driver_summaries": {{
    "driver_name": "one line explanation"
  }}
}}

Be specific, data-driven, and use F1 terminology. Reference actual stats from the enriched data."""

        try:
            response = requests.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30,
            )

            if response.status_code == 200:
                content = response.json()["content"][0]["text"]
                # Parse JSON from response
                clean = content.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                elif "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                return json.loads(clean)
            else:
                logger.warning(f"API error {response.status_code} — using rule-based")
                return self._rule_based_explain(circuit, prediction, weather, 2026, driver_data)

        except Exception as e:
            logger.warning(f"LLM call failed: {e} — using rule-based")
            return self._rule_based_explain(circuit, prediction, weather, 2026, driver_data)

    def _llm_driver_explanation(
        self, driver, circuit, rank, row
    ) -> str:
        """Single driver LLM explanation."""
        prompt = f"""In one concise sentence (max 25 words), explain why {driver} 
is predicted to finish P{rank} at the {circuit} based on this data:
- Combined Performance Index: {row.get('combined_performance_index', 0.5):.3f}
- Expert Confidence: {row.get('expert_confidence_score', 0.5):.2f}
- Recent Form: {row.get('driver_form_momentum_score', 0.5):.2f}
- Circuit History: {row.get('circuit_performance_index', 0.5):.2f}
- Regulation Benefit: {row.get('reg_combined_impact', 0.5):.2f}
- H2H vs Teammate: {row.get('h2h_race_win_rate', 0.5):.2f}

One sentence only. Be specific and use F1 terminology."""

        try:
            response = requests.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=15,
            )
            if response.status_code == 200:
                return response.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.debug(f"Driver LLM failed: {e}")

        return self._rule_driver_explanation(driver, circuit, rank, row)

    def _llm_social_post(self, circuit, prediction, explanation, platform) -> str:
        """Generate platform-specific social media post."""
        winner = prediction.get("winner", {})
        limits = {"instagram": 300, "twitter": 280, "linkedin": 500}
        limit  = limits.get(platform, 300)

        prompt = f"""Generate a {platform} post for this F1 race prediction.

Race: {circuit}
Predicted winner: {winner.get('driver')} ({winner.get('team')})
Win probability: {winner.get('win_prob',0)*100:.1f}%
Race preview: {explanation.get('race_preview','')}

Requirements:
- Maximum {limit} characters
- {"Include 5-8 relevant hashtags" if platform in ["instagram","twitter"] else "Professional tone, minimal hashtags"}
- {"Use emojis" if platform != "linkedin" else "No emojis"}
- Sound like a passionate F1 data analyst, not a robot
- Reference the ML model prediction
- End with engagement hook

Return only the post text, nothing else."""

        try:
            response = requests.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=15,
            )
            if response.status_code == 200:
                return response.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.debug(f"Social post LLM failed: {e}")

        return self._rule_social_post(circuit, prediction, explanation, platform)

    # ── RULE-BASED ENGINE (no API key needed) ─────────────────────

    def _rule_based_explain(
        self, circuit, prediction, weather, season, driver_data
    ) -> dict:
        """
        Fully rule-based explanation engine.
        Works without any API key.
        Produces high quality explanations from data patterns.
        """
        top_10    = prediction.get("top_10", [])
        winner    = prediction.get("winner", {})
        underdogs = prediction.get("dark_horses", prediction.get("underdogs", []))
        circuit_short = circuit.replace(" Grand Prix", "")

        # ── Race Preview ──
        w_driver = winner.get("driver", "Unknown")
        w_team   = winner.get("team", "Unknown")
        w_prob   = winner.get("win_prob", 0) * 100
        w_qual   = winner.get("qualifying_position", 1)

        preview = (
            f"The model predicts {w_driver} to take victory at {circuit_short} "
            f"with a {w_prob:.1f}% win probability. "
        )
        if weather == "Wet":
            preview += "Wet conditions add significant unpredictability to this prediction."
        elif weather == "Mixed":
            preview += "Changeable conditions could create strategic opportunities for the midfield."
        else:
            preview += f"{w_team} look to be the class of the field at this circuit."

        # ── Winner Reasoning ──
        w_data = driver_data.get(w_driver, {})
        reasons = []

        if w_qual == 1:
            reasons.append("starting from pole position — a decisive advantage here")
        elif w_qual <= 3:
            reasons.append(f"qualifying P{w_qual} giving a front-row start")

        cpi = w_data.get("combined_performance_index", 0)
        if cpi > 0.7:
            reasons.append(f"the highest Combined Performance Index in the field ({cpi:.3f})")

        conf = w_data.get("expert_confidence_score", 0)
        if conf > 0.8:
            reasons.append(f"strong expert analyst backing (confidence: {conf:.2f})")

        form = w_data.get("driver_form_momentum_score", 0)
        if form > 0.6:
            reasons.append("excellent recent form momentum")

        reg = w_data.get("reg_combined_impact", 0)
        if reg > 0.5:
            reasons.append(f"{w_team} clearly benefiting from 2026 regulation changes")

        circ_hist = w_data.get("circuit_performance_index", 0)
        if circ_hist > 0.7:
            reasons.append(f"strong historical performance at {circuit_short}")

        if reasons:
            winner_reasoning = f"{w_driver} is the model's top pick due to: {', '.join(reasons[:3])}."
        else:
            winner_reasoning = f"{w_driver} leads the prediction on combined pace and qualifying position."

        # ── Podium Reasoning ──
        p2 = top_10[1] if len(top_10) > 1 else {}
        p3 = top_10[2] if len(top_10) > 2 else {}
        podium_reasoning = (
            f"{p2.get('driver','P2')} ({p2.get('team','')}) takes P2 on race pace, "
            f"with {p3.get('driver','P3')} ({p3.get('team','')}) completing the podium."
        )

        # ── Dark Horses ──
        if underdogs:
            u = underdogs[0]
            dark_horses = (
                f"{u.get('driver','Unknown')} is the key dark horse — starting P{u.get('qualifying_position','?')} "
                f"but with {u.get('podium_prob',0)*100:.1f}% podium probability. "
                f"A safety car or strategy play could bring them into contention."
            )
        else:
            dark_horses = "No major upsets predicted — the front runners are expected to dominate."

        # ── Strategy Insight ──
        circuit_type = circuit.lower()
        if any(x in circuit_type for x in ["monaco", "singapore", "hungary"]):
            strategy_insight = (
                "This is a low overtaking circuit — qualifying position is critical. "
                "A one-stop strategy is likely optimal but the undercut window is narrow."
            )
        elif any(x in circuit_type for x in ["monza", "spa", "baku", "las vegas"]):
            strategy_insight = (
                "High speed circuit rewards power unit performance. "
                "DRS trains may form, making two-stop strategies viable for overtaking. "
                "Safety car risk is elevated at this venue."
            )
        else:
            strategy_insight = (
                "A two-stop strategy is the likely preferred approach. "
                "Teams with stronger tire deg management will have the edge in the final stint."
            )

        if weather == "Wet":
            strategy_insight = (
                "Wet conditions transform strategy completely — intermediate to slick timing "
                "will be the race-defining call. Drivers with strong wet-weather ability gain "
                "significant advantage."
            )

        # ── Risk Factors ──
        risks = []
        if weather in ["Wet", "Mixed"]:
            risks.append("unpredictable weather could randomize the result")
        if w_qual and w_qual > 3:
            risks.append(f"starting P{w_qual} means traffic and first lap incidents are a concern")
        if len(underdogs) > 0:
            risks.append(f"safety car deployment could gift {underdogs[0].get('driver','')} an unexpected result")
        risks.append("reliability concerns in the early 2026 season with new power unit regulations")

        risk_factors = f"Key risks: {'; '.join(risks[:2])}."

        # ── Confidence Level ──
        if w_prob > 25:
            confidence_level  = "HIGH"
            confidence_reason = f"{w_driver} has dominant stats across all key metrics."
        elif w_prob > 15:
            confidence_level  = "MEDIUM"
            confidence_reason = "Competitive field makes a clear winner difficult to call."
        else:
            confidence_level  = "LOW"
            confidence_reason = "Very open race — multiple drivers have realistic win chances."

        # ── Per-driver summaries ──
        driver_summaries = {}
        for r in top_10[:6]:
            driver   = r["driver"]
            d        = driver_data.get(driver, {})
            rank     = r.get("predicted_rank", 0)
            q_pos    = r.get("qualifying_position", 10)
            w_pr     = r.get("win_prob", 0) * 100
            pod_pr   = r.get("podium_prob", 0) * 100

            summary = self._rule_driver_explanation(driver, circuit_short, rank, pd.Series(d))
            driver_summaries[driver] = summary

        return {
            "race_preview":       preview,
            "winner_reasoning":   winner_reasoning,
            "podium_reasoning":   podium_reasoning,
            "dark_horses":        dark_horses,
            "strategy_insight":   strategy_insight,
            "risk_factors":       risk_factors,
            "confidence_level":   confidence_level,
            "confidence_reason":  confidence_reason,
            "driver_summaries":   driver_summaries,
            "generated_by":       "rule_based_engine",
        }

    def _rule_driver_explanation(
        self, driver: str, circuit: str, rank: int, row
    ) -> str:
        """One-line driver explanation from data."""
        cpi   = float(row.get("combined_performance_index", 0.5) or 0.5)
        form  = float(row.get("driver_form_momentum_score", 0.5) or 0.5)
        conf  = float(row.get("expert_confidence_score", 0.5) or 0.5)
        reg   = float(row.get("reg_combined_impact", 0.5) or 0.5)
        hist  = float(row.get("circuit_performance_index", 0.5) or 0.5)
        h2h   = float(row.get("h2h_race_win_rate", 0.5) or 0.5)

        # Build explanation from strongest signals
        signals = []

        if hist > 0.75:
            signals.append(f"strong {circuit} history")
        elif hist < 0.3:
            signals.append(f"limited {circuit} track record")

        if form > 0.7:
            signals.append("excellent recent form")
        elif form < 0.35:
            signals.append("inconsistent recent results")

        if conf > 0.8:
            signals.append("high analyst confidence")
        elif conf < 0.4:
            signals.append("below-par expert backing")

        if reg > 0.8:
            signals.append("major 2026 regulation benefit")
        elif reg < 0.45:
            signals.append("regulation disadvantage")

        if h2h > 0.7:
            signals.append("dominant vs teammate")
        elif h2h < 0.35:
            signals.append("struggling vs teammate")

        if not signals:
            signals = ["consistent mid-field pace"]

        if rank == 1:
            return f"Predicted winner — {' and '.join(signals[:2])} make {driver} the clear favourite."
        elif rank <= 3:
            return f"Podium contender — {signals[0]} supports a top-3 finish."
        elif rank <= 6:
            return f"Points scorer — {signals[0]}, expected solid points finish."
        else:
            return f"Outside top 5 — {signals[0]} but not enough for front-running pace."

    def _rule_social_post(
        self, circuit: str, prediction: dict, explanation: dict, platform: str
    ) -> str:
        """Rule-based social media post generation."""
        winner    = prediction.get("winner", {})
        w_driver  = winner.get("driver", "Unknown")
        w_team    = winner.get("team", "Unknown")
        w_prob    = winner.get("win_prob", 0) * 100
        circuit_short = circuit.replace(" Grand Prix", "")
        top_10    = prediction.get("top_10", [])
        conf      = explanation.get("confidence_level", "MEDIUM")

        if platform == "instagram":
            post = f"""🏎️ {circuit_short.upper()} — ML PREDICTION 🔮

Our model has spoken 📊

🏆 Predicted Winner: {w_driver}
🎯 Win Probability: {w_prob:.1f}%
🏁 Team: {w_team}

Predicted Top 3:
🥇 {top_10[0]['driver'] if len(top_10)>0 else '?'}
🥈 {top_10[1]['driver'] if len(top_10)>1 else '?'}
🥉 {top_10[2]['driver'] if len(top_10)>2 else '?'}

{explanation.get('winner_reasoning','')}

Confidence: {conf} {"🔥" if conf=="HIGH" else "⚡" if conf=="MEDIUM" else "🎲"}

Think the model is right? Drop your prediction below 👇
.
.
#F1 #{circuit_short.replace(' ','')}GP #Formula1 #F1Predictions #BoxBoxData #PitWallAI #DataDrivenF1 #F12026 #MachineLearning"""

        elif platform == "twitter":
            post = f"""🏎️ {circuit_short} GP Prediction

Model picks: {w_driver} to WIN 🏆
Win prob: {w_prob:.1f}%

Top 3:
P1 {top_10[0]['driver'] if len(top_10)>0 else '?'}
P2 {top_10[1]['driver'] if len(top_10)>1 else '?'}
P3 {top_10[2]['driver'] if len(top_10)>2 else '?'}

Confidence: {conf}

#F1 #{circuit_short.replace(' ','')}GP #BoxBoxData"""

        else:  # linkedin
            post = f"""F1 Race Prediction — {circuit} 🏁

Our ML model, trained on 982 race entries across 3 seasons, predicts {w_driver} ({w_team}) to win the {circuit} with a {w_prob:.1f}% probability.

Predicted Podium:
1. {top_10[0]['driver'] if len(top_10)>0 else '?'} — {top_10[0]['team'] if len(top_10)>0 else '?'}
2. {top_10[1]['driver'] if len(top_10)>1 else '?'} — {top_10[1]['team'] if len(top_10)>1 else '?'}
3. {top_10[2]['driver'] if len(top_10)>2 else '?'} — {top_10[2]['team'] if len(top_10)>2 else '?'}

{explanation.get('winner_reasoning','')}

{explanation.get('strategy_insight','')}

Prediction confidence: {conf}

#F1 #MachineLearning #DataScience #Formula1 #PitWallAI"""

        return post

    # ── HELPERS ───────────────────────────────────────────────────

    def _get_driver_enriched_data(
        self, top_10: list, enriched: pd.DataFrame,
        circuit: str, season: int
    ) -> dict:
        """Extract enriched feature data for top 10 drivers."""
        result = {}
        if enriched.empty:
            return result

        for r in top_10:
            driver = r["driver"]
            rows = enriched[
                enriched["driver"].str.lower().str.contains(
                    driver.split()[-1].lower(), na=False
                )
            ]
            if rows.empty:
                continue

            latest = rows.sort_values(["season","round"]).iloc[-1]
            result[driver] = {
                "combined_performance_index": float(latest.get("combined_performance_index", 0.5) or 0.5),
                "expert_confidence_score":    float(latest.get("expert_confidence_score", 0.5) or 0.5),
                "expert_sentiment_score":     float(latest.get("expert_sentiment_score", 0.0) or 0.0),
                "driver_form_momentum_score": float(latest.get("driver_form_momentum_score", 0.5) or 0.5),
                "points_momentum":            float(latest.get("points_momentum", 0) or 0),
                "reg_combined_impact":        float(latest.get("reg_combined_impact", 0.5) or 0.5),
                "circuit_performance_index":  float(latest.get("circuit_performance_index", 0.5) or 0.5),
                "circuit_win_rate":           float(latest.get("circuit_win_rate", 0) or 0),
                "circuit_podium_rate":        float(latest.get("circuit_podium_rate", 0) or 0),
                "h2h_race_win_rate":          float(latest.get("h2h_race_win_rate", 0.5) or 0.5),
                "team_upgrade_trajectory":    float(latest.get("team_upgrade_trajectory", 0) or 0),
            }

        return result


def get_reasoner(api_key: str = None) -> LLMReasoning:
    """Convenience factory function."""
    return LLMReasoning(api_key=api_key)


if __name__ == "__main__":
    # Demo — works without API key using rule-based engine
    sys.path.insert(0, BASE_DIR)

    print("\n" + "="*60)
    print("  LLM REASONING ENGINE DEMO")
    print("="*60)

    # Build a mock prediction
    mock_prediction = {
        "circuit": "Japanese Grand Prix",
        "weather": "Dry",
        "winner": {
            "driver": "George Russell", "team": "Mercedes",
            "win_prob": 0.22, "podium_prob": 0.78,
            "qualifying_position": 1, "predicted_rank": 1,
        },
        "top_10": [
            {"driver":"George Russell",  "team":"Mercedes",     "predicted_rank":1, "win_prob":0.22, "podium_prob":0.78, "qualifying_position":1},
            {"driver":"Charles Leclerc", "team":"Ferrari",      "predicted_rank":2, "win_prob":0.18, "podium_prob":0.72, "qualifying_position":3},
            {"driver":"Max Verstappen",  "team":"Red Bull",     "predicted_rank":3, "win_prob":0.15, "podium_prob":0.60, "qualifying_position":2},
            {"driver":"Lewis Hamilton",  "team":"Ferrari",      "predicted_rank":4, "win_prob":0.12, "podium_prob":0.45, "qualifying_position":5},
            {"driver":"Lando Norris",    "team":"McLaren",      "predicted_rank":5, "win_prob":0.10, "podium_prob":0.38, "qualifying_position":4},
            {"driver":"Kimi Antonelli",  "team":"Mercedes",     "predicted_rank":6, "win_prob":0.08, "podium_prob":0.30, "qualifying_position":6},
            {"driver":"Oscar Piastri",   "team":"McLaren",      "predicted_rank":7, "win_prob":0.06, "podium_prob":0.20, "qualifying_position":7},
            {"driver":"Fernando Alonso", "team":"Aston Martin", "predicted_rank":8, "win_prob":0.04, "podium_prob":0.12, "qualifying_position":9},
            {"driver":"Isack Hadjar",    "team":"Red Bull",     "predicted_rank":9, "win_prob":0.03, "podium_prob":0.08, "qualifying_position":8},
            {"driver":"Pierre Gasly",    "team":"Alpine",       "predicted_rank":10,"win_prob":0.02, "podium_prob":0.05, "qualifying_position":11},
        ],
        "underdogs": [
            {"driver":"Fernando Alonso","qualifying_position":9,"podium_prob":0.12}
        ],
    }

    # Get API key from env if available
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    reasoner = LLMReasoning(api_key=api_key)

    print(f"\nUsing: {'Claude API 🤖' if reasoner.has_api else 'Rule-based engine 📐'}")

    explanation = reasoner.explain_race_prediction(
        circuit="Japanese Grand Prix",
        prediction=mock_prediction,
        weather="Dry",
        season=2026,
    )

    print(f"\n{'='*60}")
    print(f"  🏁 {mock_prediction['circuit'].upper()} PREDICTION EXPLAINED")
    print(f"{'='*60}")
    print(f"\n📖 RACE PREVIEW:")
    print(f"   {explanation['race_preview']}")
    print(f"\n🏆 WINNER REASONING:")
    print(f"   {explanation['winner_reasoning']}")
    print(f"\n🥈🥉 PODIUM:")
    print(f"   {explanation['podium_reasoning']}")
    print(f"\n⚡ DARK HORSES:")
    print(f"   {explanation['dark_horses']}")
    print(f"\n🔧 STRATEGY:")
    print(f"   {explanation['strategy_insight']}")
    print(f"\n⚠️  RISKS:")
    print(f"   {explanation['risk_factors']}")
    print(f"\n📊 CONFIDENCE: {explanation['confidence_level']} — {explanation['confidence_reason']}")
    print(f"\n👤 DRIVER SUMMARIES:")
    for driver, summary in list(explanation.get("driver_summaries",{}).items())[:5]:
        print(f"   {driver:<22} → {summary}")

    print(f"\n{'='*60}")
    print(f"  INSTAGRAM POST")
    print(f"{'='*60}")
    post = reasoner.generate_race_preview_post(
        "Japanese Grand Prix", mock_prediction, "Dry", "instagram"
    )
    print(post)