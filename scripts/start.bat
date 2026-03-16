@echo off
REM scripts/start.bat — Windows launcher for PitWall AI

echo.
echo ============================================
echo   PitWall AI — Starting Platform
echo ============================================
echo.

REM Setup
echo [1/5] Setting up database...
python ingestion\run_ingestion.py --setup

echo [2/5] Rebuilding feature store...
python ingestion\run_ingestion.py --features

echo [3/5] Syncing race results...
python ingestion\run_ingestion.py --sync-api

echo [4/5] Starting FastAPI on port 8000...
start /B python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

echo [5/5] Starting Streamlit dashboard...
echo.
echo   Dashboard: http://localhost:8501
echo   API:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.

python -m streamlit run dashboard\app.py --server.port=8501

pause
