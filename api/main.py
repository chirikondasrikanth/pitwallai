
# © 2026 Srikanth Chirikonda | PitWall AI | github.com/chirikondasrikanth/pitwallai

"""
api/main.py
FastAPI REST API — exposes all platform capabilities as endpoints.
Runs alongside the Streamlit dashboard.

Endpoints:
  GET  /health                    — system health check
  GET  /api/standings/{season}    — driver standings
  GET  /api/prediction/{circuit}  — race prediction
  GET  /api/driver/{name}         — driver profile
  GET  /api/calendar/{season}     — race calendar
  GET  /api/model/metrics         — model performance
  POST /api/ingest/race           — add race result
  POST /api/ingest/expert         — add expert insight
  POST /api/sync                  — trigger API sync
  POST /api/retrain               — trigger model retrain
  POST /api/features              — rebuild feature store
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── APP ───────────────────────────────────────────────────────────
app = FastAPI(
    title="PitWall AI — F1 Analytics API",
    description="Live Formula 1 race prediction and analytics platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

_assets_dir = os.path.join(BASE_DIR, "dashboard", "assets")
if os.path.isdir(_assets_dir):
    app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

@app.get("/prediction", include_in_schema=False)
async def prediction_page():
    html_path = os.path.join(BASE_DIR, "dashboard", "f1_prediction.html")
    if not os.path.isfile(html_path):
        raise HTTPException(status_code=404, detail="f1_prediction.html not found in dashboard/")
    return FileResponse(html_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── PYDANTIC MODELS ───────────────────────────────────────────────

class RaceResultInput(BaseModel):
    season: int = 2026
    round: int
    circuit: str
    driver: str
    team: str
    qualifying_position: int
    finish_position: int
    weather: str = "Dry"
    tire_strategy: str = "2-Stop"
    pit_stops: int = 2
    incidents: int = 0
    penalties: int = 0

class ExpertInsightInput(BaseModel):
    text: str
    source: str = "Manual"
    race_weekend: Optional[str] = None

class PredictionRequest(BaseModel):
    circuit: str
    weather: str = "Dry"
    qualifying_order: Optional[List[str]] = None
    season: int = 2026

# ── BACKGROUND TASK TRACKER ──────────────────────────────────────
task_status = {}

def run_sync():
    task_status["sync"] = {"status": "running", "started": datetime.now().isoformat()}
    try:
        from ingestion.scrapers.auto_sync import AutoSync
        sync = AutoSync()
        result = sync.check_and_sync(2026)
        task_status["sync"] = {
            "status": "complete",
            "result": result,
            "finished": datetime.now().isoformat()
        }
    except Exception as e:
        task_status["sync"] = {"status": "failed", "error": str(e)}

def run_retrain():
    task_status["retrain"] = {"status": "running", "started": datetime.now().isoformat()}
    try:
        from src.train_model import train_pipeline
        _, _, _, _, metrics = train_pipeline()
        task_status["retrain"] = {
            "status": "complete",
            "metrics": {k: v for k, v in metrics.items() if isinstance(v, (int, float))},
            "finished": datetime.now().isoformat()
        }
    except Exception as e:
        task_status["retrain"] = {"status": "failed", "error": str(e)}

def run_features():
    task_status["features"] = {"status": "running", "started": datetime.now().isoformat()}
    try:
        from ingestion.feature_store import FeatureStore
        store = FeatureStore()
        df = store.build()
        task_status["features"] = {
            "status": "complete",
            "rows": len(df),
            "columns": len(df.columns),
            "finished": datetime.now().isoformat()
        }
    except Exception as e:
        task_status["features"] = {"status": "failed", "error": str(e)}


# ── ROUTES ────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """System health check — verifies DB, models, and data."""
    checks = {}

    # DB check
    try:
        from ingestion.db.data_layer import get_db_status
        status = get_db_status()
        checks["database"] = {
            "status": "ok" if status.get("available") else "offline",
            "race_results": status.get("race_results", 0),
            "last_ingest": status.get("last_ingest", "unknown"),
        }
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}

    # Models check
    models_ok = all(
        os.path.exists(os.path.join(BASE_DIR, "models", f))
        for f in ["podium_model.pkl", "win_model.pkl", "position_model.pkl"]
    )
    meta_path = os.path.join(BASE_DIR, "models", "model_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        checks["models"] = {
            "status": "ok" if models_ok else "missing",
            "podium_auc": meta.get("metrics", {}).get("podium_auc", 0),
            "position_mae": meta.get("metrics", {}).get("position_mae", 0),
            "n_features": meta.get("metrics", {}).get("n_features", 0),
        }
    else:
        checks["models"] = {"status": "not_trained"}

    # Data check
    csv_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
    if os.path.exists(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        df26 = df[df["season"] == 2026]
        checks["data"] = {
            "status": "ok",
            "total_rows": len(df),
            "seasons": int(df["season"].nunique()),
            "races_2026": int(df26["round"].nunique()),
        }
    else:
        checks["data"] = {"status": "missing"}

    overall = "healthy" if all(
        c.get("status") == "ok" for c in checks.values()
    ) else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "checks": checks,
    }


@app.get("/api/standings/{season}", tags=["Analytics"])
async def get_standings(season: int = 2026):
    """Driver championship standings for a season."""
    try:
        from ingestion.db.data_layer import get_season_standings
        df = get_season_standings(season)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No standings for season {season}")
        return {
            "season": season,
            "standings": df.to_dict("records"),
            "total_drivers": len(df),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/constructors/{season}", tags=["Analytics"])
async def get_constructors(season: int = 2026):
    """Constructor championship standings."""
    try:
        from ingestion.db.data_layer import get_constructor_standings
        df = get_constructor_standings(season)
        if df.empty:
            raise HTTPException(status_code=404, detail="No constructor data found")
        return {"season": season, "constructors": df.to_dict("records")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/{season}", tags=["Analytics"])
async def get_calendar(season: int = 2026):
    """Race calendar with completion status."""
    try:
        from ingestion.db.data_layer import get_season_race_calendar
        df = get_season_race_calendar(season)
        if df.empty:
            raise HTTPException(status_code=404, detail="Calendar not found")
        completed = len(df[df["status"] == "completed"])
        scheduled = len(df[df["status"] == "scheduled"])
        return {
            "season": season,
            "total_races": len(df),
            "completed": completed,
            "scheduled": scheduled,
            "races": df.to_dict("records"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/driver/{name}", tags=["Analytics"])
async def get_driver(name: str, season: Optional[int] = None):
    """Full driver profile with enriched features."""
    try:
        from ingestion.db.data_layer import get_driver_stats
        stats = get_driver_stats(name, season)
        if not stats:
            raise HTTPException(status_code=404, detail=f"Driver '{name}' not found")
        return {"driver": name, "season": season, "stats": stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cpi/{season}", tags=["Analytics"])
async def get_cpi_rankings(season: int = 2026):
    """Combined Performance Index rankings."""
    try:
        from ingestion.db.data_layer import get_driver_cpi_ranking
        df = get_driver_cpi_ranking(season)
        if df.empty:
            raise HTTPException(status_code=404, detail="CPI data not available")
        return {
            "season": season,
            "rankings": df.to_dict("records"),
            "note": "CPI combines circuit history, form, expert confidence, regulation impact, H2H stats"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prediction", tags=["Prediction"])
async def get_prediction(request: PredictionRequest):
    """Generate race prediction for a circuit."""
    try:
        import pandas as pd
        from src.predict import predict_race
        from src.utils import DRIVERS_2026

        clean_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
        hist_df = pd.read_csv(clean_path) if os.path.exists(clean_path) else None

        pred = predict_race(
            circuit=request.circuit,
            drivers=DRIVERS_2026,
            weather=request.weather,
            qualifying_order=request.qualifying_order,
            historical_df=hist_df,
            explain=False,
        )

        return {
            "circuit": request.circuit,
            "weather": request.weather,
            "season": request.season,
            "generated_at": datetime.now().isoformat(),
            "winner": {
                "driver": pred["winner"]["driver"],
                "team": pred["winner"]["team"],
                "win_probability": round(pred["winner"]["win_prob"], 4),
                "qualifying_position": pred["winner"]["qualifying_position"],
            },
            "top_10": [
                {
                    "position": r["predicted_rank"],
                    "driver": r["driver"],
                    "team": r["team"],
                    "win_prob": round(r["win_prob"], 4),
                    "podium_prob": round(r["podium_prob"], 4),
                    "qualifying_position": r["qualifying_position"],
                }
                for r in pred["top_10"]
            ],
            "dark_horses": pred.get("underdogs", [])[:3],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prediction/{circuit}", tags=["Prediction"])
async def get_prediction_get(circuit: str, weather: str = "Dry"):
    """GET endpoint for quick predictions."""
    req = PredictionRequest(circuit=circuit, weather=weather)
    return await get_prediction(req)


@app.get("/api/reasoning/{circuit}", tags=["Prediction"])
async def get_reasoning(circuit: str, weather: str = "Dry"):
    """Get AI reasoning for a circuit prediction."""
    try:
        import pandas as pd
        from src.predict import predict_race
        from src.utils import DRIVERS_2026
        from ingestion.llm_reasoning import LLMReasoning

        clean_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
        hist_df = pd.read_csv(clean_path) if os.path.exists(clean_path) else None

        pred = predict_race(
            circuit=circuit, drivers=DRIVERS_2026,
            weather=weather, historical_df=hist_df, explain=False,
        )

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        reasoner = LLMReasoning(api_key=api_key)
        reasoning = reasoner.explain_race_prediction(
            circuit=circuit, prediction=pred,
            weather=weather, season=2026,
        )

        return {
            "circuit": circuit,
            "reasoning": reasoning,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/model/metrics", tags=["Model"])
async def get_model_metrics():
    """Current model performance metrics."""
    meta_path = os.path.join(BASE_DIR, "models", "model_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Models not trained yet")
    with open(meta_path) as f:
        meta = json.load(f)
    return {
        "metrics": meta.get("metrics", {}),
        "feature_count": len(meta.get("feature_cols", [])),
        "features": meta.get("feature_cols", []),
        "trained_on": meta.get("metrics", {}).get("trained_on", "unknown"),
    }


@app.post("/api/ingest/race", tags=["Ingestion"])
async def ingest_race(result: RaceResultInput, background_tasks: BackgroundTasks):
    """Add a single race result."""
    try:
        from src.crm_ingest import ingest_single_result
        data = result.model_dump()
        res = ingest_single_result(data, auto_retrain=False)
        if res["success"]:
            background_tasks.add_task(run_features)
            return {
                "success": True,
                "message": res["message"],
                "total_rows": res.get("rows", 0),
            }
        else:
            raise HTTPException(status_code=400, detail=res.get("errors", []))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/expert", tags=["Ingestion"])
async def ingest_expert(insight: ExpertInsightInput):
    """Add an expert insight via NLP extraction."""
    try:
        from ingestion.scrapers.expert_ingester import ExpertIngester
        ingester = ExpertIngester()
        result = ingester.ingest_text(
            insight.text,
            source=insight.source,
            race_weekend=insight.race_weekend,
        )
        if result.get("success"):
            return {
                "success": True,
                "extracted": result["extracted"],
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sync", tags=["Pipeline"])
async def trigger_sync(background_tasks: BackgroundTasks):
    """Trigger API sync for missing race results."""
    if task_status.get("sync", {}).get("status") == "running":
        return {"message": "Sync already running", "status": task_status["sync"]}
    background_tasks.add_task(run_sync)
    return {"message": "Sync started in background", "check": "/api/tasks/sync"}


@app.post("/api/retrain", tags=["Pipeline"])
async def trigger_retrain(background_tasks: BackgroundTasks):
    """Trigger model retraining."""
    if task_status.get("retrain", {}).get("status") == "running":
        return {"message": "Retrain already running"}
    background_tasks.add_task(run_retrain)
    return {"message": "Retraining started in background", "check": "/api/tasks/retrain"}


@app.post("/api/features", tags=["Pipeline"])
async def trigger_features(background_tasks: BackgroundTasks):
    """Rebuild feature store."""
    background_tasks.add_task(run_features)
    return {"message": "Feature store rebuild started", "check": "/api/tasks/features"}


@app.get("/api/tasks/{task_name}", tags=["Pipeline"])
async def get_task_status(task_name: str):
    """Check status of a background task."""
    status = task_status.get(task_name)
    if not status:
        return {"task": task_name, "status": "not_started"}
    return {"task": task_name, **status}


@app.get("/api/regulations/{season}", tags=["Analytics"])
async def get_regulations(season: int = 2026):
    """Get regulation data for a season."""
    try:
        from ingestion.db.data_layer import get_regulations
        df = get_regulations(season)
        if df.empty:
            raise HTTPException(status_code=404, detail="No regulations found")
        return {"season": season, "regulations": df.to_dict("records")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/expert/{driver}", tags=["Analytics"])
async def get_expert_predictions(driver: str):
    """Get expert predictions for a driver."""
    try:
        from ingestion.db.data_layer import get_expert_predictions
        df = get_expert_predictions(driver_name=driver)
        return {
            "driver": driver,
            "predictions": df.to_dict("records") if not df.empty else [],
            "count": len(df),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "PitWall AI — F1 Analytics API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "dashboard": "http://localhost:8501",
        "endpoints": {
            "standings":   "/api/standings/{season}",
            "calendar":    "/api/calendar/{season}",
            "prediction":  "/api/prediction/{circuit}",
            "reasoning":   "/api/reasoning/{circuit}",
            "cpi":         "/api/cpi/{season}",
            "driver":      "/api/driver/{name}",
            "model":       "/api/model/metrics",
            "sync":        "POST /api/sync",
            "retrain":     "POST /api/retrain",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
