"""
train_model.py — Enriched Feature Training Pipeline
"""

import os, sys, json, joblib, logging
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, mean_absolute_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

CORE_FEATURES = [
    "qualifying_gap", "pole_position", "weather_encoded",
    "pit_stops", "penalties", "driver_encoded", "team_encoded", "circuit_encoded",
]

ENRICHED_FEATURES = [
    "expert_confidence_score", "expert_sentiment_score",
    "reg_power_unit_impact", "reg_aero_impact", "reg_combined_impact",
    "circuit_win_rate", "circuit_podium_rate", "circuit_performance_index",
    "circuit_appearances", "driver_form_momentum_score", "points_momentum",
    "team_upgrade_trajectory", "h2h_qual_win_rate", "h2h_race_win_rate",
    "combined_performance_index",
]

ALL_FEATURES = CORE_FEATURES + ENRICHED_FEATURES


def encode_categoricals(df):
    for col in ["driver", "team", "circuit", "weather"]:
        if col in df.columns:
            df[f"{col}_encoded"] = pd.Categorical(df[col]).codes
    return df


def add_core_features(df):
    if "qualifying_gap" not in df.columns:
        max_pos = df.groupby(["season", "round"])["qualifying_position"].transform("max")
        df["qualifying_gap"] = ((df["qualifying_position"] - 1) /
                                (max_pos - 1).replace(0, 1)).fillna(0).clip(0, 1)
    if "weather_encoded" not in df.columns:
        df["weather_encoded"] = df["weather"].map({"Dry": 0, "Mixed": 1, "Wet": 2}).fillna(0).astype(int)
    return df


def load_and_prepare(data_path=None):
    enriched_path = os.path.join(BASE_DIR, "data", "enriched_features.csv")
    clean_path    = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")

    if os.path.exists(enriched_path):
        logger.info(f"✅ Loading enriched dataset")
        df = pd.read_csv(enriched_path)
        logger.info(f"   {len(df)} rows | {len(df.columns)} columns")
    elif data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
        from src.feature_engineering import build_features
        df = build_features(df)
    elif os.path.exists(clean_path):
        df = pd.read_csv(clean_path)
        from src.feature_engineering import build_features
        df = build_features(df)
    else:
        raise FileNotFoundError("No dataset found. Run setup.py first.")

    df = encode_categoricals(df)
    df = add_core_features(df)

    available = [f for f in ALL_FEATURES if f in df.columns]
    missing   = [f for f in ALL_FEATURES if f not in df.columns]
    if missing:
        logger.warning(f"   Missing {len(missing)} features: {missing}")
    logger.info(f"   Using {len(available)}/{len(ALL_FEATURES)} features")

    df = df.dropna(subset=available + ["finish_position", "podium", "win"]).reset_index(drop=True)

    X        = df[available].astype(float)
    y_podium = df["podium"].astype(int)
    y_win    = df["win"].astype(int)
    y_pos    = df["finish_position"].astype(float)

    logger.info(f"   Final: X={X.shape} | podiums={y_podium.sum()} | wins={y_win.sum()}")
    return X, y_podium, y_win, y_pos, available


def train_podium_model(X_tr, y_tr, X_te, y_te):
    logger.info("\nTraining podium classifier...")
    models = {}

    rf = RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=3,
                                class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    rf_auc = roc_auc_score(y_te, rf.predict_proba(X_te)[:, 1])
    rf_acc = accuracy_score(y_te, rf.predict(X_te))
    logger.info(f"  RF  → AUC: {rf_auc:.4f} | Acc: {rf_acc:.4f}")
    models["rf"] = (rf, rf_auc)

    if HAS_XGB:
        scale = (y_tr == 0).sum() / max(1, (y_tr == 1).sum())
        xgb = XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.04,
                            subsample=0.85, colsample_bytree=0.85,
                            scale_pos_weight=scale, random_state=42,
                            eval_metric="logloss", verbosity=0)
        xgb.fit(X_tr, y_tr)
        xgb_auc = roc_auc_score(y_te, xgb.predict_proba(X_te)[:, 1])
        xgb_acc = accuracy_score(y_te, xgb.predict(X_te))
        logger.info(f"  XGB → AUC: {xgb_auc:.4f} | Acc: {xgb_acc:.4f}")
        models["xgb"] = (xgb, xgb_auc)

    best = max(models, key=lambda k: models[k][1])
    logger.info(f"  ✅ Best: {best.upper()} (AUC={models[best][1]:.4f})")
    return models[best][0], models


def train_win_model(X_tr, y_tr, X_te, y_te):
    logger.info("\nTraining win classifier...")
    models = {}

    rf = RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=5,
                                class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    try:
        rf_auc = roc_auc_score(y_te, rf.predict_proba(X_te)[:, 1])
    except Exception:
        rf_auc = 0.5
    logger.info(f"  RF  → AUC: {rf_auc:.4f}")
    models["rf"] = (rf, rf_auc)

    if HAS_XGB:
        scale = max(1, (y_tr == 0).sum() / max(1, (y_tr == 1).sum()))
        xgb = XGBClassifier(n_estimators=400, max_depth=5, learning_rate=0.03,
                            subsample=0.85, colsample_bytree=0.85,
                            scale_pos_weight=scale, random_state=42,
                            eval_metric="logloss", verbosity=0)
        xgb.fit(X_tr, y_tr)
        try:
            xgb_auc = roc_auc_score(y_te, xgb.predict_proba(X_te)[:, 1])
        except Exception:
            xgb_auc = 0.5
        logger.info(f"  XGB → AUC: {xgb_auc:.4f}")
        models["xgb"] = (xgb, xgb_auc)

    best = max(models, key=lambda k: models[k][1])
    logger.info(f"  ✅ Best: {best.upper()} (AUC={models[best][1]:.4f})")
    return models[best][0], models


def train_position_model(X_tr, y_tr, X_te, y_te):
    logger.info("\nTraining position regressor...")
    models = {}

    rf = RandomForestRegressor(n_estimators=300, max_depth=10, min_samples_leaf=3,
                               random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    rf_mae = mean_absolute_error(y_te, rf.predict(X_te))
    rf_r2  = r2_score(y_te, rf.predict(X_te))
    logger.info(f"  RF  → MAE: {rf_mae:.3f} | R²: {rf_r2:.4f}")
    models["rf"] = (rf, -rf_mae)

    if HAS_XGB:
        xgb = XGBRegressor(n_estimators=400, max_depth=6, learning_rate=0.04,
                           subsample=0.85, colsample_bytree=0.85,
                           random_state=42, verbosity=0)
        xgb.fit(X_tr, y_tr)
        xgb_mae = mean_absolute_error(y_te, xgb.predict(X_te))
        xgb_r2  = r2_score(y_te, xgb.predict(X_te))
        logger.info(f"  XGB → MAE: {xgb_mae:.3f} | R²: {xgb_r2:.4f}")
        models["xgb"] = (xgb, -xgb_mae)

    best = max(models, key=lambda k: models[k][1])
    logger.info(f"  ✅ Best: {best.upper()} (MAE={-models[best][1]:.3f})")
    return models[best][0], models


def compare_metrics(old, new):
    print("\n" + "="*58)
    print("  BEFORE vs AFTER — ENRICHED FEATURE RETRAINING")
    print("="*58)
    print(f"  {'Metric':<22} {'Before':>10} {'After':>10} {'Δ':>12}")
    print(f"  {'-'*55}")
    for label, key, higher_better in [
        ("Podium AUC",   "podium_auc",   True),
        ("Podium Acc",   "podium_acc",   True),
        ("Position MAE", "position_mae", False),
        ("Position R²",  "position_r2",  True),
    ]:
        o = old.get(key, old.get("metrics", {}).get(key, 0))
        n = new.get(key, 0)
        if isinstance(o, float) and isinstance(n, float):
            diff  = n - o
            icon  = "✅" if (diff > 0) == higher_better else "⚠️" if diff != 0 else "  "
            arrow = "▲" if diff > 0 else "▼" if diff < 0 else "━"
            print(f"  {label:<22} {o:>10.4f} {n:>10.4f} {icon} {arrow}{abs(diff):.4f}")
    print(f"  {'Features used':<22} {old.get('n_features', len(old.get('feature_cols', []))):>10} {new.get('n_features', 0):>10}")
    print()


def train_pipeline(data_path=None):
    logger.info("\n" + "="*55)
    logger.info("  ENRICHED FEATURE TRAINING PIPELINE")
    logger.info("="*55)

    old_metrics = {}
    meta_path = os.path.join(MODELS_DIR, "model_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            old_meta = json.load(f)
            old_metrics = old_meta.get("metrics", {})
            old_metrics["n_features"] = len(old_meta.get("feature_cols", []))

    X, y_podium, y_win, y_pos, feature_cols = load_and_prepare(data_path)

    X_tr, X_te, yp_tr, yp_te, yw_tr, yw_te, ypos_tr, ypos_te = train_test_split(
        X, y_podium, y_win, y_pos, test_size=0.2, random_state=42
    )
    logger.info(f"\nTrain: {len(X_tr)} rows | Test: {len(X_te)} rows")

    podium_model, _ = train_podium_model(X_tr, yp_tr, X_te, yp_te)
    win_model,    _ = train_win_model(X_tr, yw_tr, X_te, yw_te)
    pos_model,    _ = train_position_model(X_tr, ypos_tr, X_te, ypos_te)

    metrics = {
        "podium_auc":   float(roc_auc_score(yp_te, podium_model.predict_proba(X_te)[:, 1])),
        "podium_acc":   float(accuracy_score(yp_te, podium_model.predict(X_te))),
        "position_mae": float(mean_absolute_error(ypos_te, pos_model.predict(X_te))),
        "position_r2":  float(r2_score(ypos_te, pos_model.predict(X_te))),
        "n_train":      len(X_tr),
        "n_test":       len(X_te),
        "n_features":   len(feature_cols),
        "feature_cols": feature_cols,
        "trained_on":   "enriched_features.csv",
    }

    joblib.dump(podium_model, os.path.join(MODELS_DIR, "podium_model.pkl"))
    joblib.dump(win_model,    os.path.join(MODELS_DIR, "win_model.pkl"))
    joblib.dump(pos_model,    os.path.join(MODELS_DIR, "position_model.pkl"))
    with open(meta_path, "w") as f:
        json.dump({"feature_cols": feature_cols, "metrics": metrics}, f, indent=2)
    logger.info(f"\n✅ Models saved → {MODELS_DIR}/")

    if old_metrics:
        compare_metrics(old_metrics, metrics)

    logger.info("📊 Top 10 Features (Podium Model):")
    try:
        fi = sorted(zip(feature_cols, podium_model.feature_importances_),
                    key=lambda x: x[1], reverse=True)
        for feat, imp in fi[:10]:
            bar = "█" * int(imp * 200)
            logger.info(f"  {feat:<35} {imp:.4f}  {bar}")
    except Exception:
        pass

    return podium_model, win_model, pos_model, feature_cols, metrics


if __name__ == "__main__":
    _, _, _, feature_cols, metrics = train_pipeline()
    print(f"\n{'='*40}")
    print(f"  Features: {metrics['n_features']} (was 15)")
    print(f"  Podium AUC:   {metrics['podium_auc']:.4f}")
    print(f"  Podium Acc:   {metrics['podium_acc']:.4f}")
    print(f"  Position MAE: {metrics['position_mae']:.4f}")
    print(f"  Position R²:  {metrics['position_r2']:.4f}")
    print(f"{'='*40}")