"""
ingestion/feature_store.py
Feature Store — enriches the base race dataset with:

1. Expert Confidence Scores    → per driver, per circuit, per race weekend
2. Regulation Impact Scores    → how 2026 rules affect each team/driver
3. Circuit Intelligence        → circuit-specific performance multipliers
4. Driver Form Momentum        → weighted recent form (not just rolling avg)
5. Head-to-Head Stats          → driver vs teammate metrics
6. Team Upgrade Trajectory     → performance trend over last N races
7. Combined ML-Ready Dataset   → single enriched file ready for models

Output: data/enriched_features.csv
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CLEAN_CSV    = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
ENRICHED_CSV = os.path.join(BASE_DIR, "data", "enriched_features.csv")


# ─── TEAM REGULATION BENEFIT SCORES ──────────────────────────────
# How much each 2026 regulation benefits each team (0-1 scale)
# Based on REG data + expert analysis
TEAM_REG_BENEFIT = {
    # Power Unit regs (REG-2026-PU-001 impact=0.95)
    # Mercedes/Ferrari built better electric deployment
    "Mercedes":     {"power_unit": 0.95, "aerodynamics": 0.90, "tires": 0.75, "chassis": 0.80},
    "Ferrari":      {"power_unit": 0.92, "aerodynamics": 0.85, "tires": 0.78, "chassis": 0.82},
    "McLaren":      {"power_unit": 0.85, "aerodynamics": 0.92, "tires": 0.80, "chassis": 0.85},
    "Red Bull":     {"power_unit": 0.70, "aerodynamics": 0.75, "tires": 0.72, "chassis": 0.78},
    "Aston Martin": {"power_unit": 0.72, "aerodynamics": 0.70, "tires": 0.68, "chassis": 0.70},
    "Alpine":       {"power_unit": 0.68, "aerodynamics": 0.72, "tires": 0.65, "chassis": 0.68},
    "Haas":         {"power_unit": 0.75, "aerodynamics": 0.68, "tires": 0.65, "chassis": 0.67},
    "Williams":     {"power_unit": 0.73, "aerodynamics": 0.70, "tires": 0.66, "chassis": 0.68},
    "Racing Bulls": {"power_unit": 0.71, "aerodynamics": 0.69, "tires": 0.65, "chassis": 0.67},
    "Audi":         {"power_unit": 0.65, "aerodynamics": 0.66, "tires": 0.63, "chassis": 0.65},
    "Cadillac":     {"power_unit": 0.60, "aerodynamics": 0.62, "tires": 0.60, "chassis": 0.62},
    # 2024/2025 teams
    "Kick Sauber":  {"power_unit": 0.62, "aerodynamics": 0.60, "tires": 0.60, "chassis": 0.60},
    "RB":           {"power_unit": 0.70, "aerodynamics": 0.68, "tires": 0.65, "chassis": 0.66},
}

# Circuit type classification for regulation impact
CIRCUIT_TYPE_MAP = {
    "Bahrain Grand Prix":         "power",
    "Saudi Arabian Grand Prix":   "power",
    "Australian Grand Prix":      "balanced",
    "Japanese Grand Prix":        "downforce",
    "Chinese Grand Prix":         "balanced",
    "Miami Grand Prix":           "balanced",
    "Emilia Romagna Grand Prix":  "downforce",
    "Monaco Grand Prix":          "downforce",
    "Canadian Grand Prix":        "power",
    "Spanish Grand Prix":         "balanced",
    "Austrian Grand Prix":        "power",
    "British Grand Prix":         "balanced",
    "Belgian Grand Prix":         "power",
    "Hungarian Grand Prix":       "downforce",
    "Dutch Grand Prix":           "downforce",
    "Italian Grand Prix":         "power",
    "Azerbaijan Grand Prix":      "power",
    "Singapore Grand Prix":       "downforce",
    "United States Grand Prix":   "balanced",
    "Mexico City Grand Prix":     "power",
    "São Paulo Grand Prix":       "balanced",
    "Las Vegas Grand Prix":       "power",
    "Qatar Grand Prix":           "balanced",
    "Abu Dhabi Grand Prix":       "balanced",
}


class FeatureStore:

    def __init__(self, db_url: str = None):
        self.db_url = db_url
        self._session = None
        self._connect_db()

    def _connect_db(self):
        try:
            from ingestion.db.schema import get_session, get_engine, init_db
            engine = init_db(get_engine(self.db_url))
            self._session = get_session(engine)
            logger.info("Connected to relational DB")
        except Exception as e:
            logger.warning(f"DB not available — using CSV only: {e}")

    # ── PUBLIC: BUILD FULL FEATURE STORE ─────────────────────────

    def build(self, output_path: str = None) -> pd.DataFrame:
        """
        Main entry point. Builds complete enriched feature dataset.
        Returns enriched DataFrame and saves to CSV.
        """
        logger.info("="*50)
        logger.info("Building Feature Store...")
        logger.info("="*50)

        # Load base data
        df = pd.read_csv(CLEAN_CSV)
        logger.info(f"Base dataset: {len(df)} rows")

        # Add all feature layers
        df = self._add_expert_confidence_scores(df)
        df = self._add_regulation_impact_scores(df)
        df = self._add_circuit_intelligence(df)
        df = self._add_driver_form_momentum(df)
        df = self._add_team_upgrade_trajectory(df)
        df = self._add_head_to_head_stats(df)
        df = self._add_combined_performance_index(df)

        # Save
        out = output_path or ENRICHED_CSV
        df.to_csv(out, index=False)

        logger.info(f"\n✅ Feature Store built:")
        logger.info(f"   Rows:     {len(df)}")
        logger.info(f"   Columns:  {len(df.columns)} ({len(df.columns)-17} new features added)")
        logger.info(f"   Saved to: {out}")

        self._print_feature_summary(df)
        return df

    # ── LAYER 1: EXPERT CONFIDENCE SCORES ────────────────────────

    def _add_expert_confidence_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pull expert predictions from DB and map confidence scores
        onto each driver-race row.
        """
        logger.info("→ Layer 1: Expert confidence scores...")

        # Default scores
        df["expert_confidence_score"] = 0.5
        df["expert_sentiment_score"]  = 0.0
        df["expert_prediction_count"] = 0

        if self._session is None:
            logger.warning("  No DB — using default expert scores")
            return df

        try:
            from ingestion.db.schema import ExpertPrediction
            preds = self._session.query(ExpertPrediction).all()

            if not preds:
                logger.info("  No expert predictions in DB yet")
                return df

            # Build per-driver score map
            driver_scores = {}
            for p in preds:
                if not p.driver_name:
                    continue
                key = p.driver_name.lower()
                if key not in driver_scores:
                    driver_scores[key] = {
                        "confidences": [], "sentiments": [], "count": 0
                    }
                driver_scores[key]["confidences"].append(p.confidence_score or 0.5)
                driver_scores[key]["sentiments"].append(p.sentiment_score or 0.0)
                driver_scores[key]["count"] += 1

            # Map onto DataFrame
            for driver_key, scores in driver_scores.items():
                avg_conf = np.mean(scores["confidences"])
                avg_sent = np.mean(scores["sentiments"])
                count    = scores["count"]

                mask = df["driver"].str.lower().str.contains(
                    driver_key.split()[-1], na=False  # match on last name
                )
                df.loc[mask, "expert_confidence_score"] = round(avg_conf, 3)
                df.loc[mask, "expert_sentiment_score"]  = round(avg_sent, 3)
                df.loc[mask, "expert_prediction_count"] = count

            logger.info(f"  Applied scores for {len(driver_scores)} drivers "
                        f"from {len(preds)} predictions")

        except Exception as e:
            logger.error(f"  Expert score error: {e}")

        return df

    # ── LAYER 2: REGULATION IMPACT SCORES ────────────────────────

    def _add_regulation_impact_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate how 2026 regulations impact each team's performance.
        Only applied to 2026 season rows.
        """
        logger.info("→ Layer 2: Regulation impact scores...")

        df["reg_power_unit_impact"]  = 0.5
        df["reg_aero_impact"]        = 0.5
        df["reg_tire_impact"]        = 0.5
        df["reg_combined_impact"]    = 0.5
        df["circuit_type"]           = "balanced"

        # Get regulation weights from DB or use defaults
        reg_weights = self._get_regulation_weights()

        # Add circuit type
        df["circuit_type"] = df["circuit"].map(CIRCUIT_TYPE_MAP).fillna("balanced")

        # Only apply reg impact to 2026 rows
        mask_2026 = df["season"] == 2026

        for team, impacts in TEAM_REG_BENEFIT.items():
            team_mask = mask_2026 & (df["team"].str.lower() == team.lower())

            if not team_mask.any():
                continue

            pu_impact   = impacts.get("power_unit", 0.5)
            aero_impact = impacts.get("aerodynamics", 0.5)
            tire_impact = impacts.get("tires", 0.5)

            # Weight by regulation importance scores
            combined = (
                pu_impact   * reg_weights.get("power_unit", 0.95) +
                aero_impact * reg_weights.get("aerodynamics", 0.90) +
                tire_impact * reg_weights.get("tires", 0.75)
            ) / 3

            # Adjust for circuit type
            circuit_types = df.loc[team_mask, "circuit_type"]
            circuit_boost = circuit_types.map({
                "power":     pu_impact,
                "downforce": aero_impact,
                "balanced":  combined,
            }).fillna(combined)

            df.loc[team_mask, "reg_power_unit_impact"] = round(pu_impact, 3)
            df.loc[team_mask, "reg_aero_impact"]       = round(aero_impact, 3)
            df.loc[team_mask, "reg_tire_impact"]       = round(tire_impact, 3)
            df.loc[team_mask, "reg_combined_impact"]   = circuit_boost.round(3)

        logger.info(f"  Applied regulation impacts to "
                    f"{mask_2026.sum()} 2026 rows")
        return df

    def _get_regulation_weights(self) -> dict:
        """Pull regulation impact scores from DB."""
        weights = {"power_unit": 0.95, "aerodynamics": 0.90, "tires": 0.75}
        if self._session is None:
            return weights
        try:
            from ingestion.db.schema import Regulation
            regs = self._session.query(Regulation).filter_by(
                effective_season=2026
            ).all()
            for r in regs:
                cat = r.category.lower()
                if cat in weights:
                    weights[cat] = r.impact_score or weights.get(cat, 0.5)
        except Exception as e:
            logger.debug(f"Regulation weight error: {e}")
        return weights

    # ── LAYER 3: CIRCUIT INTELLIGENCE ────────────────────────────

    def _add_circuit_intelligence(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Per-driver circuit-specific performance scores:
        - Historical win rate at circuit
        - Historical podium rate at circuit
        - Average qualifying position at circuit
        - Average finishing position at circuit
        """
        logger.info("→ Layer 3: Circuit intelligence...")

        circuit_stats = df.groupby(["driver", "circuit"]).agg(
            circuit_win_rate    = ("win",              "mean"),
            circuit_podium_rate = ("podium",           "mean"),
            circuit_avg_finish  = ("finish_position",  "mean"),
            circuit_avg_qual    = ("qualifying_position","mean"),
            circuit_appearances = ("finish_position",  "count"),
        ).reset_index()

        circuit_stats["circuit_win_rate"]    = circuit_stats["circuit_win_rate"].round(3)
        circuit_stats["circuit_podium_rate"] = circuit_stats["circuit_podium_rate"].round(3)
        circuit_stats["circuit_avg_finish"]  = circuit_stats["circuit_avg_finish"].round(2)
        circuit_stats["circuit_avg_qual"]    = circuit_stats["circuit_avg_qual"].round(2)

        # Normalize avg finish to 0-1 score (lower position = higher score)
        max_pos = df["finish_position"].max()
        circuit_stats["circuit_performance_index"] = (
            1 - (circuit_stats["circuit_avg_finish"] / max_pos)
        ).round(3)

        df = df.merge(circuit_stats, on=["driver", "circuit"], how="left")

        # Fill new drivers with circuit averages
        df["circuit_win_rate"]         = df["circuit_win_rate"].fillna(0)
        df["circuit_podium_rate"]      = df["circuit_podium_rate"].fillna(0)
        df["circuit_avg_finish"]       = df["circuit_avg_finish"].fillna(10)
        df["circuit_avg_qual"]         = df["circuit_avg_qual"].fillna(10)
        df["circuit_appearances"]      = df["circuit_appearances"].fillna(0)
        df["circuit_performance_index"]= df["circuit_performance_index"].fillna(0.5)

        logger.info(f"  Circuit intelligence added for "
                    f"{df['circuit'].nunique()} circuits")
        return df

    # ── LAYER 4: DRIVER FORM MOMENTUM ────────────────────────────

    def _add_driver_form_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Weighted recent form — recent races matter more than older ones.
        Uses exponential decay: most recent race = weight 1.0,
        5 races ago = weight 0.5
        """
        logger.info("→ Layer 4: Driver form momentum...")

        df = df.sort_values(["season", "round"]).reset_index(drop=True)

        def weighted_form(group, window=5):
            positions = group["finish_position"].values
            n = len(positions)
            results = np.full(n, np.nan)

            for i in range(n):
                if i == 0:
                    results[i] = positions[i]
                    continue
                # Look back up to `window` races
                start = max(0, i - window)
                hist  = positions[start:i]
                # Exponential decay weights
                weights = np.exp(np.linspace(-1, 0, len(hist)))
                weights /= weights.sum()
                results[i] = np.average(hist, weights=weights)

            return pd.Series(results, index=group.index)

        df["driver_form_momentum"] = df.groupby(
            "driver", group_keys=False
        ).apply(weighted_form)

        max_pos = df["finish_position"].max()
        df["driver_form_momentum_score"] = (
            1 - (df["driver_form_momentum"] / max_pos)
        ).clip(0, 1).round(3)

        # Points momentum — weighted avg of recent points
        def points_momentum(group, window=5):
            pts = group["points"].values
            n = len(pts)
            results = np.full(n, np.nan)
            for i in range(n):
                if i == 0:
                    results[i] = pts[i]
                    continue
                start = max(0, i - window)
                hist = pts[start:i]
                weights = np.exp(np.linspace(-1, 0, len(hist)))
                weights /= weights.sum()
                results[i] = np.average(hist, weights=weights)
            return pd.Series(results, index=group.index)

        df["points_momentum"] = df.groupby(
            "driver", group_keys=False
        ).apply(points_momentum).round(2)

        df["driver_form_momentum_score"] = df["driver_form_momentum_score"].fillna(0.5)
        df["points_momentum"]            = df["points_momentum"].fillna(0)

        logger.info("  Driver form momentum calculated")
        return df

    # ── LAYER 5: TEAM UPGRADE TRAJECTORY ─────────────────────────

    def _add_team_upgrade_trajectory(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Team performance trend over last 4 races.
        Positive = improving, Negative = declining.
        """
        logger.info("→ Layer 5: Team upgrade trajectory...")

        df = df.sort_values(["season", "round"])

        # Average team finish per race
        team_race_avg = df.groupby(
            ["season", "round", "team"]
        )["finish_position"].mean().reset_index()
        team_race_avg.rename(
            columns={"finish_position": "team_race_avg_pos"}, inplace=True
        )
        team_race_avg = team_race_avg.sort_values(["season", "round"])

        def trajectory(group, window=4):
            vals = group["team_race_avg_pos"].values
            n = len(vals)
            trends = np.zeros(n)
            for i in range(1, n):
                start = max(0, i - window)
                hist  = vals[start:i]
                if len(hist) >= 2:
                    # Negative slope = improving (lower position is better)
                    trend = np.polyfit(range(len(hist)), hist, 1)[0]
                    trends[i] = -trend  # flip: positive = improving
            return pd.Series(trends, index=group.index)

        team_race_avg["team_upgrade_trajectory"] = team_race_avg.groupby(
            "team", group_keys=False
        ).apply(trajectory)

        # Normalize trajectory to -1 to 1
        max_traj = team_race_avg["team_upgrade_trajectory"].abs().max()
        if max_traj > 0:
            team_race_avg["team_upgrade_trajectory"] = (
                team_race_avg["team_upgrade_trajectory"] / max_traj
            ).round(3)

        df = df.merge(
            team_race_avg[["season", "round", "team", "team_upgrade_trajectory"]],
            on=["season", "round", "team"], how="left"
        )
        df["team_upgrade_trajectory"] = df["team_upgrade_trajectory"].fillna(0)

        logger.info("  Team upgrade trajectory calculated")
        return df

    # ── LAYER 6: HEAD-TO-HEAD STATS ───────────────────────────────

    def _add_head_to_head_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Driver vs teammate head-to-head metrics:
        - How often driver beats teammate in qualifying
        - How often driver beats teammate in race
        """
        logger.info("→ Layer 6: Head-to-head stats...")

        df["h2h_qual_win_rate"]  = 0.5
        df["h2h_race_win_rate"]  = 0.5

        # Per season, pair teammates
        for (season, team), group in df.groupby(["season", "team"]):
            drivers = group["driver"].unique()
            if len(drivers) < 2:
                continue

            d1, d2 = drivers[0], drivers[1]

            # Get matching rounds
            d1_rows = group[group["driver"] == d1].set_index("round")
            d2_rows = group[group["driver"] == d2].set_index("round")
            common  = d1_rows.index.intersection(d2_rows.index)

            if len(common) < 2:
                continue

            # Qualifying H2H
            d1_qual = d1_rows.loc[common, "qualifying_position"]
            d2_qual = d2_rows.loc[common, "qualifying_position"]
            d1_qual_wins = (d1_qual < d2_qual).sum()
            d1_qual_rate = d1_qual_wins / len(common)
            d2_qual_rate = 1 - d1_qual_rate

            # Race H2H
            d1_race = d1_rows.loc[common, "finish_position"]
            d2_race = d2_rows.loc[common, "finish_position"]
            d1_race_wins = (d1_race < d2_race).sum()
            d1_race_rate = d1_race_wins / len(common)
            d2_race_rate = 1 - d1_race_rate

            mask_d1 = (df["season"] == season) & (df["driver"] == d1)
            mask_d2 = (df["season"] == season) & (df["driver"] == d2)

            df.loc[mask_d1, "h2h_qual_win_rate"] = round(d1_qual_rate, 3)
            df.loc[mask_d1, "h2h_race_win_rate"] = round(d1_race_rate, 3)
            df.loc[mask_d2, "h2h_qual_win_rate"] = round(d2_qual_rate, 3)
            df.loc[mask_d2, "h2h_race_win_rate"] = round(d2_race_rate, 3)

        logger.info("  Head-to-head stats calculated")
        return df

    # ── LAYER 7: COMBINED PERFORMANCE INDEX ──────────────────────

    def _add_combined_performance_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Single composite score combining all signals:
        - Circuit performance
        - Driver form momentum
        - Expert confidence
        - Team regulation benefit
        - H2H dominance

        This is the master feature the ML model should weight heavily.
        """
        logger.info("→ Layer 7: Combined Performance Index...")

        # Weights for each signal
        WEIGHTS = {
            "circuit_performance_index": 0.25,
            "driver_form_momentum_score": 0.25,
            "expert_confidence_score":    0.15,
            "reg_combined_impact":        0.15,
            "h2h_race_win_rate":          0.10,
            "team_upgrade_trajectory":    0.10,
        }

        cpi = pd.Series(0.0, index=df.index)

        for feature, weight in WEIGHTS.items():
            if feature in df.columns:
                col = df[feature].fillna(0.5)
                # Normalize to 0-1 if needed
                col_min, col_max = col.min(), col.max()
                if col_max > col_min:
                    col = (col - col_min) / (col_max - col_min)
                cpi += col * weight

        df["combined_performance_index"] = cpi.round(4)

        # Also create a simplified rank within each race
        df["cpi_race_rank"] = df.groupby(
            ["season", "round"]
        )["combined_performance_index"].rank(ascending=False).astype(int)

        logger.info("  Combined Performance Index calculated")
        return df

    # ── SUMMARY ───────────────────────────────────────────────────

    def _print_feature_summary(self, df: pd.DataFrame):
        new_features = [
            "expert_confidence_score", "expert_sentiment_score",
            "reg_power_unit_impact", "reg_aero_impact", "reg_combined_impact",
            "circuit_win_rate", "circuit_podium_rate", "circuit_performance_index",
            "driver_form_momentum_score", "points_momentum",
            "team_upgrade_trajectory",
            "h2h_qual_win_rate", "h2h_race_win_rate",
            "combined_performance_index", "cpi_race_rank",
        ]

        print("\n" + "="*60)
        print("  FEATURE STORE SUMMARY")
        print("="*60)
        print(f"\n  {'Feature':<35} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}")
        print(f"  {'-'*67}")

        for feat in new_features:
            if feat in df.columns:
                col = df[feat].dropna()
                print(f"  {feat:<35} "
                      f"{col.mean():>8.3f} "
                      f"{col.std():>8.3f} "
                      f"{col.min():>8.3f} "
                      f"{col.max():>8.3f}")

        print(f"\n  Total features: {len(df.columns)}")
        print(f"  New features:   {len(new_features)}")
        print(f"  Rows:           {len(df)}")

    def get_driver_profile(self, driver_name: str) -> dict:
        """
        Get a complete enriched profile for a driver.
        Useful for dashboard and prediction explanations.
        """
        if not os.path.exists(ENRICHED_CSV):
            logger.warning("Enriched CSV not found — run build() first")
            return {}

        df = pd.read_csv(ENRICHED_CSV)
        d = df[df["driver"].str.lower().str.contains(
            driver_name.split()[-1].lower(), na=False
        )]

        if d.empty:
            return {}

        latest = d.sort_values(["season","round"]).iloc[-1]
        all_seasons = d.groupby("season").agg(
            races=("finish_position","count"),
            wins=("win","sum"),
            podiums=("podium","sum"),
            points=("points","sum"),
            avg_finish=("finish_position","mean"),
        ).to_dict("index")

        return {
            "driver":                    latest["driver"],
            "team":                      latest["team"],
            "expert_confidence":         float(latest.get("expert_confidence_score", 0.5)),
            "expert_sentiment":          float(latest.get("expert_sentiment_score", 0.0)),
            "form_momentum":             float(latest.get("driver_form_momentum_score", 0.5)),
            "points_momentum":           float(latest.get("points_momentum", 0)),
            "reg_impact":                float(latest.get("reg_combined_impact", 0.5)),
            "h2h_qual_rate":             float(latest.get("h2h_qual_win_rate", 0.5)),
            "h2h_race_rate":             float(latest.get("h2h_race_win_rate", 0.5)),
            "combined_performance_index":float(latest.get("combined_performance_index", 0.5)),
            "seasons": all_seasons,
        }

    def get_race_preview(self, circuit: str, season: int = 2026) -> pd.DataFrame:
        """
        Get enriched feature snapshot for all drivers at a specific circuit.
        Used by the prediction engine.
        """
        if not os.path.exists(ENRICHED_CSV):
            return pd.DataFrame()

        df = pd.read_csv(ENRICHED_CSV)

        # Get most recent data per driver
        latest = df.sort_values(["season","round"]).groupby("driver").last().reset_index()

        # Get circuit-specific stats
        circuit_df = df[df["circuit"].str.lower() == circuit.lower()]
        if not circuit_df.empty:
            circuit_stats = circuit_df.groupby("driver").agg(
                circuit_win_rate    = ("win","mean"),
                circuit_podium_rate = ("podium","mean"),
                circuit_avg_finish  = ("finish_position","mean"),
            ).reset_index()
            latest = latest.merge(circuit_stats, on="driver", how="left",
                                   suffixes=("","_circuit_specific"))

        return latest


if __name__ == "__main__":
    store = FeatureStore()

    print("\n🏗️  Building Feature Store...\n")
    df = store.build()

    print("\n📊 Sample: Top drivers by Combined Performance Index (2026)")
    df_2026 = df[df["season"] == 2026].sort_values(
        "combined_performance_index", ascending=False
    ).drop_duplicates("driver")

    cols = ["driver","team","combined_performance_index",
            "expert_confidence_score","reg_combined_impact",
            "driver_form_momentum_score","circuit_performance_index"]
    print(df_2026[cols].head(10).to_string(index=False))

    print("\n📋 Driver profile — George Russell:")
    profile = store.get_driver_profile("George Russell")
    for k, v in profile.items():
        if k != "seasons":
            print(f"  {k:<35} {v}")
