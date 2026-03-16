#!/bin/bash
# scripts/start.sh
# Boots the full PitWall AI platform

set -e
echo ""
echo "============================================"
echo "  PitWall AI — Starting Platform"
echo "============================================"

# Setup
echo "→ Setting up database..."
python ingestion/run_ingestion.py --setup

echo "→ Rebuilding feature store..."
python ingestion/run_ingestion.py --features

echo "→ Checking for new race results..."
python ingestion/run_ingestion.py --sync-api

# Start API in background
echo "→ Starting FastAPI on port 8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start scheduler in background
echo "→ Starting background scheduler..."
python ingestion/schedulers/auto_updater.py &
SCHEDULER_PID=$!

# Start dashboard (foreground)
echo "→ Starting Streamlit dashboard on port 8501..."
echo ""
echo "  Dashboard: http://localhost:8501"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
streamlit run dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true

# Cleanup on exit
trap "kill $API_PID $SCHEDULER_PID 2>/dev/null" EXIT
