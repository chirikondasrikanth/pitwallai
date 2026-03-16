# 🏎️ PitWall AI — F1 Intelligence Platform

A complete Python-based Machine Learning platform for Formula 1 race prediction and data management. Combines historical analytics, ML models (Random Forest + XGBoost), SHAP explainability, and a Streamlit dashboard.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd f1_platform
pip install -r requirements.txt
```

### 2. One-Command Setup (generates data + trains models)

```bash
python setup.py
```

### 3. Launch Dashboard

```bash
streamlit run dashboard/app.py
```

Open **http://localhost:8501** in your browser.

---

## 🗂️ Project Structure

```
f1_platform/
├── data/
│   ├── raw_race_data.csv          # Raw ingested data
│   └── cleaned_race_data.csv      # Auto-cleaned dataset
├── models/
│   ├── podium_model.pkl           # Best podium classifier
│   ├── win_model.pkl              # Best win classifier
│   ├── position_model.pkl         # Finish position regressor
│   └── model_meta.json            # Feature list + metrics
├── src/
│   ├── data_cleaner.py            # Automated data cleaning pipeline
│   ├── feature_engineering.py     # ML feature builder
│   ├── train_model.py             # Training pipeline (RF + XGB)
│   ├── predict.py                 # Race prediction engine + SHAP
│   ├── crm_ingest.py              # CRM-style data ingestion
│   └── utils.py                   # Shared utilities
├── dashboard/
│   └── app.py                     # Streamlit dashboard
├── generate_data.py               # Synthetic data generator
├── setup.py                       # Full setup script
└── requirements.txt
```

---

## 🧠 ML Models

| Task | Model | Metric |
|---|---|---|
| Podium prediction | RandomForest / XGBoost (best selected) | AUC ~0.90 |
| Win prediction | RandomForest / XGBoost | AUC ~0.85 |
| Finish position | RandomForest / XGBoost Regressor | MAE ~2.5 |

### Features Used
- `is_pole` — Pole position flag
- `qualifying_gap` — Normalized distance from pole
- `circuit_perf_score` — Historical driver performance at circuit
- `driver_recent_form` — Rolling avg finish over last 5 races
- `team_performance_trend` — Team rolling avg over last 3 races
- `weather_encoded` — Dry / Mixed / Wet (0/1/2)
- `driver_win_rate` — Career win rate
- `driver_podium_rate` — Career podium rate
- `circuit_overtaking` — Normalized overtaking difficulty
- `driver_incident_rate` — Historical incident frequency
- `pit_stops`, `penalties` — Strategic factors

---

## 📊 Dashboard Pages

| Page | Description |
|---|---|
| **Race Predictor** | Select circuit + weather + qualifying order → get Top 10, podium probabilities, and AI explanations |
| **Analytics** | Season standings, driver form charts, circuit analysis, constructor trends |
| **Driver Profile** | Career stats, per-season charts, best circuits |
| **CRM Data Entry** | Manual form or CSV upload to add new race results |
| **Model Management** | Train / retrain models, view feature importances, monitor metrics |

---

## 🔄 Adding New Race Results

### Via Dashboard (CRM Form)
1. Go to **CRM Data Entry**
2. Fill in the form fields
3. Click **Submit Race Result**
4. Optionally retrain models

### Via Python API

```python
from src.crm_ingest import ingest_single_result

result = ingest_single_result({
    "season": 2026,
    "round": 5,
    "circuit": "Monaco Grand Prix",
    "driver": "Lando Norris",
    "team": "McLaren",
    "qualifying_position": 1,
    "finish_position": 1,
    "weather": "Dry",
    "tire_strategy": "2-Stop",
    "pit_stops": 2,
})
print(result)
```

### Via CSV Upload

```python
from src.crm_ingest import ingest_race_csv
result = ingest_race_csv("my_race_results.csv", auto_retrain=True)
```

---

## 🔮 Making Predictions

```python
import pandas as pd
from src.predict import predict_race, format_prediction_output

hist_df = pd.read_csv("data/cleaned_race_data.csv")

DRIVERS_2026 = [
    ("Lando Norris", "McLaren"),
    ("Charles Leclerc", "Ferrari"),
    ("Max Verstappen", "Red Bull"),
    # ... all 20 drivers
]

pred = predict_race(
    circuit="Monaco Grand Prix",
    drivers=DRIVERS_2026,
    weather="Dry",
    qualifying_order=["Lando Norris", "Charles Leclerc", "Max Verstappen"],
    historical_df=hist_df,
)

print(format_prediction_output(pred))
```

---

## ⚙️ Manual Training

```bash
# Clean raw data
python -c "from src.data_cleaner import clean_dataset; clean_dataset('data/raw_race_data.csv', 'data/cleaned_race_data.csv')"

# Train models
python src/train_model.py
```

---

## 🔮 Roadmap

- [ ] Real-time FastF1 / Ergast API integration
- [ ] Circuit-specific models (Monaco, Spa, Monza, etc.)
- [ ] LLM reasoning engine (GPT / Claude API)
- [ ] Vector database for expert race insights
- [ ] Automated post-race data scraping
- [ ] Driver head-to-head prediction
- [ ] Weather forecast integration
- [ ] Instagram content auto-generator (@boxboxdata)

---

## 📦 Tech Stack

- **ML**: scikit-learn, XGBoost
- **Data**: pandas, numpy
- **Explainability**: SHAP
- **Dashboard**: Streamlit + Plotly
- **Serialization**: joblib
- **Storage**: CSV / SQLite (upgradeable to PostgreSQL)

---

*Built for F1 analytics enthusiasts. Data is synthetic for development — integrate real F1 APIs for production use.*
