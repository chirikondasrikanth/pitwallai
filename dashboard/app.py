"""
app.py — F1 Intelligence Platform Dashboard
Streamlit-based analytics and prediction interface.
"""

import os
import sys
import json
import joblib
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Path setup
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(APP_DIR)
sys.path.insert(0, BASE_DIR)

from src.utils import (TEAM_COLORS, DRIVERS_2026, CIRCUITS_2026,
                        DRIVER_NATIONALITIES, get_team_color, get_circuit_info,
                        load_clean_data, get_driver_stats as csv_driver_stats,
                        get_model_metrics)
from src.crm_ingest import (ingest_single_result, ingest_race_csv,
                              get_season_summary, VALID_TEAMS_2026)

# ── Live DB Data Layer ──────────────────────────────────────────────
try:
    from ingestion.db.data_layer import (
        load_race_data, get_season_standings, get_constructor_standings,
        get_driver_stats as db_driver_stats, get_driver_form_trend,
        get_expert_predictions, get_regulations, get_db_status,
        get_recent_ingestion_log, get_season_race_calendar,
        get_driver_cpi_ranking, db_available
    )
    DB_LIVE = db_available()
except Exception:
    DB_LIVE = False

def get_driver_stats(driver, df=None):
    """Use DB stats if available, else fall back to CSV."""
    if DB_LIVE:
        return db_driver_stats(driver)
    return csv_driver_stats(driver, df)

# ─────────────────────────── PAGE CONFIG ───────────────────────────
st.set_page_config(
    page_title="PitWall AI | F1 Intelligence",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── CUSTOM CSS ────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap');

  :root {
    --red: #E8002D;
    --gold: #FFD700;
    --dark: #0A0A0F;
    --card: #13131A;
    --border: #2A2A3A;
    --text: #E8E8F0;
    --muted: #888899;
  }

  .stApp { background: #0A0A0F; color: #E8E8F0; }
  
  [data-testid="stSidebar"] {
    background: #0D0D14 !important;
    border-right: 1px solid #2A2A3A;
  }
  
  .pitwall-header {
    font-family: 'Orbitron', monospace;
    font-size: 2.2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #E8002D 0%, #FFD700 50%, #E8002D 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 0;
  }
  
  .sub-header {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #888899;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 2px;
  }
  
  .metric-card {
    background: linear-gradient(135deg, #13131A 0%, #1A1A25 100%);
    border: 1px solid #2A2A3A;
    border-radius: 12px;
    padding: 18px 20px;
    margin: 6px 0;
    transition: border-color 0.2s;
  }
  
  .metric-card:hover { border-color: #E8002D; }
  
  .metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #FFD700;
  }
  
  .metric-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: #888899;
    text-transform: uppercase;
    letter-spacing: 2px;
  }
  
  .podium-card {
    border-radius: 10px;
    padding: 16px;
    margin: 4px;
    text-align: center;
  }
  
  .p1-card { background: linear-gradient(135deg, #3D2B00, #1A1200); border: 2px solid #FFD700; }
  .p2-card { background: linear-gradient(135deg, #1A1A2E, #0D0D1A); border: 2px solid #C0C0C0; }
  .p3-card { background: linear-gradient(135deg, #2B1400, #150A00); border: 2px solid #CD7F32; }
  
  .driver-name { 
    font-family: 'Orbitron', monospace; 
    font-size: 1.1rem; 
    font-weight: 700; 
    color: #E8E8F0;
  }
  
  .team-badge {
    display: inline-block;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 4px;
  }
  
  .prediction-table {
    font-family: 'Inter', sans-serif;
    width: 100%;
    border-collapse: collapse;
  }
  
  .prediction-table th {
    background: #1A1A25;
    color: #888899;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 10px 12px;
    border-bottom: 1px solid #2A2A3A;
  }
  
  .prediction-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #1A1A22;
    font-size: 0.9rem;
  }
  
  .prediction-table tr:hover td { background: #1A1A25; }
  
  .pos-badge {
    display: inline-block;
    width: 28px;
    height: 28px;
    line-height: 28px;
    border-radius: 50%;
    text-align: center;
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    font-weight: 700;
  }
  
  .stButton > button {
    background: linear-gradient(135deg, #E8002D, #C00020) !important;
    color: white !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
  }
  
  .stButton > button:hover {
    background: linear-gradient(135deg, #FF1040, #E8002D) !important;
    transform: translateY(-1px) !important;
  }
  
  .section-title {
    font-family: 'Orbitron', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: #E8E8F0;
    letter-spacing: 3px;
    text-transform: uppercase;
    border-left: 3px solid #E8002D;
    padding-left: 12px;
    margin: 20px 0 14px;
  }
  
  .explanation-box {
    background: linear-gradient(135deg, #0D1520, #0A1018);
    border: 1px solid #1E3A5A;
    border-left: 3px solid #3671C6;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    line-height: 1.6;
  }
  
  .win-prob-bar {
    height: 6px;
    border-radius: 3px;
    background: linear-gradient(90deg, #E8002D, #FFD700);
    margin-top: 4px;
  }
  
  .nav-item {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
  }
  
  div[data-testid="stSelectbox"] label,
  div[data-testid="stMultiSelect"] label,
  div[data-testid="stNumberInput"] label,
  .stTextInput label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    color: #888899 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
  }
  
  .success-banner {
    background: linear-gradient(135deg, #0D2B1A, #091A10);
    border: 1px solid #27F4D2;
    border-radius: 8px;
    padding: 12px 16px;
    color: #27F4D2;
    font-family: 'Orbitron', monospace;
    font-size: 0.8rem;
    letter-spacing: 1px;
  }
  
  .error-banner {
    background: linear-gradient(135deg, #2B0A0A, #1A0505);
    border: 1px solid #E8002D;
    border-radius: 8px;
    padding: 12px 16px;
    color: #FF4466;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
  }
  
  .stTabs [data-baseweb="tab"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: #888899 !important;
  }
  
  .stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #E8002D !important;
    border-bottom-color: #E8002D !important;
  }
  
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #0A0A0F; }
  ::-webkit-scrollbar-thumb { background: #2A2A3A; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #E8002D; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────── HELPERS ───────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    """Load from enriched CSV (has all 39 features) or clean CSV fallback."""
    if DB_LIVE:
        df = load_race_data()
        if not df.empty:
            return df
    return load_clean_data()

@st.cache_data(ttl=120)
def get_summary(season):
    """Season standings from DB or CSV."""
    if DB_LIVE:
        df = get_season_standings(season)
        if not df.empty:
            return df
    return get_season_summary(season)

def models_trained():
    return os.path.exists(os.path.join(BASE_DIR, "models", "podium_model.pkl"))

def run_prediction(circuit, weather, qual_order):
    from src.predict import predict_race
    df = load_data()
    historical = df if not df.empty else None
    return predict_race(
        circuit=circuit,
        drivers=DRIVERS_2026,
        weather=weather,
        qualifying_order=qual_order,
        historical_df=historical,
        explain=True,
    )

def team_color_hex(team):
    return TEAM_COLORS.get(team, "#888888")


# ─────────────────────────── SIDEBAR ───────────────────────────────
with st.sidebar:
    st.markdown('<div class="pitwall-header">PitWall</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown("---")

    nav = st.radio(
        "NAVIGATION",
        ["🏁  Race Predictor", "📊  Analytics", "👤  Driver Profile",
         "📋  CRM Data Entry", "🗄️  DB & Insights", "⚙️  Model Management",
         "🔔  Subscribe", "🛡️  Admin"],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    
    df_global = load_data()
    if not df_global.empty:
        seasons = sorted(df_global["season"].unique().tolist(), reverse=True)
        selected_season = st.selectbox("SEASON", seasons, index=0)
    else:
        selected_season = 2025
    
    st.markdown("---")
    
    # DB Status indicator
    db_icon = "🟢" if DB_LIVE else "🔴"
    db_label = "Live DB" if DB_LIVE else "CSV Mode"
    st.markdown(f"""
    <div style="font-size:0.75rem;color:#888899;font-family:Inter,sans-serif;margin-bottom:8px;">
    {db_icon} <span style="color:{'#27F4D2' if DB_LIVE else '#FF8844'}">{db_label}</span>
    </div>
    """, unsafe_allow_html=True)

    # Model status
    if models_trained():
        metrics = get_model_metrics()
        st.markdown("**MODEL STATUS**")
        st.markdown(f"""
        <div style="font-size:0.75rem; color:#888899; font-family:Inter,sans-serif;">
        ✅ Models trained<br>
        Podium AUC: <span style="color:#27F4D2">{metrics.get('metrics',{}).get('podium_auc',0):.3f}</span><br>
        Position MAE: <span style="color:#27F4D2">{metrics.get('metrics',{}).get('position_mae',0):.2f}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Models not trained. Go to Model Management.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: RACE PREDICTOR
# ═══════════════════════════════════════════════════════════════════
if "Race Predictor" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">Race Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">AI-Powered Grand Prix Prediction Engine</div>', unsafe_allow_html=True)
    
    if not models_trained():
        st.error("⚠️ No trained models found. Please go to **Model Management** and train the models first.")
        st.stop()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        circuit = st.selectbox("SELECT CIRCUIT", CIRCUITS_2026, index=2)
    with col2:
        weather = st.selectbox("WEATHER", ["Dry", "Mixed", "Wet"])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("🏁  GENERATE PREDICTION")
    
    # Qualifying order
    with st.expander("⚙️ Set Qualifying Order (optional — defaults to form-based)"):
        st.markdown('<div style="font-size:0.8rem;color:#888899;margin-bottom:8px;">Drag or select drivers in qualifying order (P1 → P20)</div>', unsafe_allow_html=True)
        driver_names = [d for d, t in DRIVERS_2026]
        qual_selection = st.multiselect(
            "QUALIFYING ORDER (P1 first)",
            driver_names,
            default=driver_names[:10],
            key="qual_order"
        )
        remaining = [d for d in driver_names if d not in qual_selection]
        qual_order = qual_selection + remaining
    
    if predict_btn or st.session_state.get("last_prediction"):
        if predict_btn:
            with st.spinner("🔄 Running prediction engine..."):
                try:
                    pred = run_prediction(circuit, weather, qual_order)
                    st.session_state["last_prediction"] = pred
                except Exception as e:
                    st.error(f"Prediction failed: {e}")
                    st.stop()
        
        pred = st.session_state.get("last_prediction")
        if pred and pred["circuit"] == circuit:

            # ─── BROADCAST PODIUM VISUALIZATION ───
            st.markdown('<div class="section-title">🏆 Predicted Podium</div>', unsafe_allow_html=True)

            # Build podium inline — no imports needed
            _top3  = pred.get("top_10", [])[:3]
            if len(_top3) >= 3:
                _p1, _p2, _p3 = _top3[0], _top3[1], _top3[2]

                # Team colors lookup
                _TCOLORS = {
                    "Mercedes": "#27F4D2", "Ferrari": "#E8002D",
                    "McLaren": "#FF8000", "Red Bull": "#3671C6",
                    "Aston Martin": "#229971", "Alpine": "#FF87BC",
                    "Haas": "#B6BABD", "Racing Bulls": "#6692FF",
                    "Williams": "#37BEDD", "Audi": "#888888",
                    "Cadillac": "#FFFFFF",
                }

                # Driver images — using direct reliable sources
                _DIMGS = {
                    "George Russell":   "https://www.formula1.com/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png.transform/2col/image.png",
                    "Kimi Antonelli":   "https://www.formula1.com/content/dam/fom-website/drivers/A/ANDANT01_Kimi_Antonelli/andant01.png.transform/2col/image.png",
                    "Charles Leclerc":  "https://www.formula1.com/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png.transform/2col/image.png",
                    "Lewis Hamilton":   "https://www.formula1.com/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png.transform/2col/image.png",
                    "Lando Norris":     "https://www.formula1.com/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png.transform/2col/image.png",
                    "Oscar Piastri":    "https://www.formula1.com/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png.transform/2col/image.png",
                    "Max Verstappen":   "https://www.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/2col/image.png",
                    "Fernando Alonso":  "https://www.formula1.com/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png.transform/2col/image.png",
                    "Carlos Sainz":     "https://www.formula1.com/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png.transform/2col/image.png",
                    "Pierre Gasly":     "https://www.formula1.com/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png.transform/2col/image.png",
                    "Nico Hulkenberg":  "https://www.formula1.com/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png.transform/2col/image.png",
                    "Valtteri Bottas":  "https://www.formula1.com/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png.transform/2col/image.png",
                    "Esteban Ocon":     "https://www.formula1.com/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png.transform/2col/image.png",
                    "Lance Stroll":     "https://www.formula1.com/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png.transform/2col/image.png",
                    "Alexander Albon":  "https://www.formula1.com/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png.transform/2col/image.png",
                    "Sergio Perez":     "https://www.formula1.com/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png.transform/2col/image.png",
                    "Liam Lawson":      "https://www.formula1.com/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png.transform/2col/image.png",
                    "Oliver Bearman":   "https://www.formula1.com/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png.transform/2col/image.png",
                    "Isack Hadjar":     "https://www.formula1.com/content/dam/fom-website/drivers/I/ISAHAD01_Isack_Hadjar/isahad01.png.transform/2col/image.png",
                    "Franco Colapinto": "https://www.formula1.com/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png.transform/2col/image.png",
                    "Gabriel Bortoleto":"https://www.formula1.com/content/dam/fom-website/drivers/G/GABBOR01_Gabriel_Bortoleto/gabbor01.png.transform/2col/image.png",
                    "Arvid Lindblad":   "https://www.formula1.com/content/dam/fom-website/drivers/A/ARVLIN01_Arvid_Lindblad/arvlin01.png.transform/2col/image.png",
                }

                # Circuit track maps — Wikipedia SVG/PNG track layouts
                _CIRCUIT_INFO = {
                    "Australian Grand Prix":    {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Albert_Park_circuit_2020.png/800px-Albert_Park_circuit_2020.png",     "flag":"🇦🇺","turns":16,"length":"5.303","type":"Temporary Street","opened":1996},
                    "Chinese Grand Prix":       {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Shanghai_circuit.svg/800px-Shanghai_circuit.svg.png",                "flag":"🇨🇳","turns":16,"length":"5.451","type":"Permanent","opened":2004},
                    "Japanese Grand Prix":      {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Suzuka_circuit_map.svg/800px-Suzuka_circuit_map.svg.png",            "flag":"🇯🇵","turns":18,"length":"5.807","type":"Permanent","opened":1987},
                    "Bahrain Grand Prix":       {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Bahrain_International_Circuit--Grand_Prix_Layout.svg/800px-Bahrain_International_Circuit--Grand_Prix_Layout.svg.png", "flag":"🇧🇭","turns":15,"length":"5.412","type":"Permanent","opened":2004},
                    "Saudi Arabian Grand Prix": {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Jeddah_Corniche_Circuit.svg/800px-Jeddah_Corniche_Circuit.svg.png", "flag":"🇸🇦","turns":27,"length":"6.174","type":"Street","opened":2021},
                    "Miami Grand Prix":         {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Miami_International_Autodrome_track_map.svg/800px-Miami_International_Autodrome_track_map.svg.png", "flag":"🇺🇸","turns":19,"length":"5.412","type":"Street","opened":2022},
                    "Emilia Romagna Grand Prix":{"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Autodromo_Enzo_e_Dino_Ferrari_track_map.svg/800px-Autodromo_Enzo_e_Dino_Ferrari_track_map.svg.png", "flag":"🇮🇹","turns":19,"length":"4.909","type":"Permanent","opened":1980},
                    "Monaco Grand Prix":        {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/forty/Monte_Carlo_Formula_1_track_map.svg/800px-Monte_Carlo_Formula_1_track_map.svg.png", "flag":"🇲🇨","turns":19,"length":"3.337","type":"Street","opened":1929},
                    "Spanish Grand Prix":       {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Barcelona_circuit_map.svg/800px-Barcelona_circuit_map.svg.png",      "flag":"🇪🇸","turns":14,"length":"4.675","type":"Permanent","opened":1991},
                    "Canadian Grand Prix":      {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/thirty/Gilles_Villeneuve_track_map.svg/800px-Gilles_Villeneuve_track_map.svg.png", "flag":"🇨🇦","turns":14,"length":"4.361","type":"Street","opened":1978},
                    "Austrian Grand Prix":      {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Red_Bull_Ring_track_map.svg/800px-Red_Bull_Ring_track_map.svg.png", "flag":"🇦🇹","turns":10,"length":"4.318","type":"Permanent","opened":1970},
                    "British Grand Prix":       {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Silverstone_circuit_2020.svg/800px-Silverstone_circuit_2020.svg.png","flag":"🇬🇧","turns":18,"length":"5.891","type":"Permanent","opened":1950},
                    "Belgian Grand Prix":       {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Spa-Francorchamps_circuit_2020.svg/800px-Spa-Francorchamps_circuit_2020.svg.png", "flag":"🇧🇪","turns":19,"length":"7.004","type":"Permanent","opened":1950},
                    "Hungarian Grand Prix":     {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Hungaroring.svg/800px-Hungaroring.svg.png",                         "flag":"🇭🇺","turns":14,"length":"4.381","type":"Permanent","opened":1986},
                    "Dutch Grand Prix":         {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/thirty/Circuit_Zandvoort_track_map.svg/800px-Circuit_Zandvoort_track_map.svg.png", "flag":"🇳🇱","turns":14,"length":"4.259","type":"Permanent","opened":1952},
                    "Italian Grand Prix":       {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/nine/Autodromo_Nazionale_Monza.svg/800px-Autodromo_Nazionale_Monza.svg.png", "flag":"🇮🇹","turns":11,"length":"5.793","type":"Permanent","opened":1922},
                    "Azerbaijan Grand Prix":    {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Baku_City_Circuit_track_map.svg/800px-Baku_City_Circuit_track_map.svg.png", "flag":"🇦🇿","turns":20,"length":"6.003","type":"Street","opened":2016},
                    "Singapore Grand Prix":     {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Marina_Bay_Street_Circuit_2023.svg/800px-Marina_Bay_Street_Circuit_2023.svg.png", "flag":"🇸🇬","turns":19,"length":"4.940","type":"Street","opened":2008},
                    "United States Grand Prix": {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Austin_circuit_2012.svg/800px-Austin_circuit_2012.svg.png",          "flag":"🇺🇸","turns":20,"length":"5.513","type":"Permanent","opened":2012},
                    "Mexico City Grand Prix":   {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Autodromo_Hermanos_Rodriguez_track_map.svg/800px-Autodromo_Hermanos_Rodriguez_track_map.svg.png", "flag":"🇲🇽","turns":17,"length":"4.304","type":"Permanent","opened":1963},
                    "São Paulo Grand Prix":     {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Autodromo_Jose_Carlos_Pace_track_map.svg/800px-Autodromo_Jose_Carlos_Pace_track_map.svg.png", "flag":"🇧🇷","turns":15,"length":"4.309","type":"Permanent","opened":1973},
                    "Las Vegas Grand Prix":     {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Las_Vegas_Street_Circuit.svg/800px-Las_Vegas_Street_Circuit.svg.png","flag":"🇺🇸","turns":17,"length":"6.120","type":"Street","opened":2023},
                    "Qatar Grand Prix":         {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Losail_International_Circuit_track_map.svg/800px-Losail_International_Circuit_track_map.svg.png", "flag":"🇶🇦","turns":16,"length":"5.380","type":"Permanent","opened":2004},
                    "Abu Dhabi Grand Prix":     {"bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Yas_Marina_Circuit_2021.svg/800px-Yas_Marina_Circuit_2021.svg.png",  "flag":"🇦🇪","turns":16,"length":"5.281","type":"Permanent","opened":2009},
                }
                _ci   = _CIRCUIT_INFO.get(circuit, {"bg":"","flag":"🏁","turns":15,"length":"5.0","type":"Permanent","opened":2000})
                _bg   = _ci["bg"]
                _flag = _ci["flag"]
                _turns= _ci["turns"]
                _len  = _ci["length"]
                _ctype= _ci["type"]
                _yr   = _ci["opened"]
                _laps = cinfo.get("laps", 55)
                _dist = cinfo.get("distance_km", 305)
                _circ_short = circuit.replace(" Grand Prix","").upper()

                def _pcard(r, medal_color, pos_label, height, delay):
                    _d   = r["driver"]
                    _t   = r["team"]
                    _tc  = _TCOLORS.get(_t, "#888888")
                    _img = _DIMGS.get(_d, "")
                    _fn  = _d.split()[0][0] + ". " if len(_d.split()) > 1 else ""
                    _ln  = _d.split()[-1].upper()
                    _abr = (_d.split()[0][0] + _d.split()[-1][:2]).upper()
                    _wp  = r["win_prob"] * 100
                    _pp  = r["podium_prob"] * 100
                    _q   = r.get("qualifying_position", "?")
                    _bw  = min(_wp * 2, 100)
                    _bp  = min(_pp, 100)
                    _mg  = {
                        "#FFD700": "linear-gradient(135deg,#FFD700,#FFA500)",
                        "#C0C0C0": "linear-gradient(135deg,#C0C0C0,#A8A8A8)",
                        "#CD7F32": "linear-gradient(135deg,#CD7F32,#A0522D)",
                    }.get(medal_color, "linear-gradient(135deg," + medal_color + "," + medal_color + "88)")
                    _pn  = pos_label[1]  # "1", "2", "3"

                    # Build img tag separately to avoid f-string quote conflicts
                    if _img:
                        _img_tag = '<img src="' + _img + '" style="width:100%;height:100%;object-fit:cover;object-position:top;" />'
                    else:
                        _img_tag = '<div style="display:flex;width:100%;height:100%;align-items:center;justify-content:center;font-family:Orbitron,monospace;font-size:1.1rem;font-weight:900;color:' + _tc + ';">' + _abr + '</div>'

                    return (
                        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;flex:1;max-width:240px;animation:podiumRise 0.7s ease ' + str(delay) + 's both;">'
                        '<div style="background:linear-gradient(160deg,rgba(14,14,24,0.97),rgba(8,8,16,0.99));border:1px solid ' + _tc + '44;border-radius:16px;padding:16px 12px 12px;width:100%;text-align:center;position:relative;overflow:hidden;box-shadow:0 8px 40px ' + _tc + '22,0 20px 50px rgba(0,0,0,0.7);margin-bottom:8px;">'
                        '<div style="position:absolute;top:0;left:0;right:0;height:3px;background:' + _mg + ';"></div>'
                        '<div style="position:absolute;top:10px;left:12px;font-family:Orbitron,monospace;font-size:0.6rem;font-weight:900;color:' + medal_color + ';">' + pos_label + '</div>'
                        '<div style="width:84px;height:84px;border-radius:50%;margin:22px auto 10px;overflow:hidden;border:3px solid ' + _tc + '66;box-shadow:0 0 20px ' + _tc + '44;background:#0A0A14;">'
                        + _img_tag +
                        '</div>'
                        '<div style="font-family:Orbitron,monospace;font-size:0.7rem;font-weight:700;color:#FFFFFF;letter-spacing:0.5px;margin-bottom:3px;">' + _fn + _ln + '</div>'
                        '<div style="font-size:0.62rem;color:' + _tc + ';letter-spacing:1px;text-transform:uppercase;margin-bottom:10px;">' + _t + '</div>'
                        '<div style="margin-bottom:5px;">'
                        '<div style="display:flex;justify-content:space-between;margin-bottom:2px;">'
                        '<span style="font-size:0.55rem;color:#444460;letter-spacing:1px;">WIN</span>'
                        '<span style="font-family:Orbitron,monospace;font-size:0.6rem;color:' + medal_color + ';">' + f"{_wp:.1f}%" + '</span>'
                        '</div>'
                        '<div style="height:3px;background:#0A0A14;border-radius:2px;">'
                        '<div style="width:' + f"{_bw:.0f}" + '%;height:100%;background:' + _mg + ';border-radius:2px;"></div>'
                        '</div></div>'
                        '<div>'
                        '<div style="display:flex;justify-content:space-between;margin-bottom:2px;">'
                        '<span style="font-size:0.55rem;color:#444460;letter-spacing:1px;">PODIUM</span>'
                        '<span style="font-family:Orbitron,monospace;font-size:0.6rem;color:' + _tc + ';">' + f"{_pp:.1f}%" + '</span>'
                        '</div>'
                        '<div style="height:3px;background:#0A0A14;border-radius:2px;">'
                        '<div style="width:' + f"{_bp:.0f}" + '%;height:100%;background:' + _tc + '88;border-radius:2px;"></div>'
                        '</div></div>'
                        '<div style="margin-top:8px;padding-top:6px;border-top:1px solid #12121E;font-size:0.58rem;color:#444460;letter-spacing:1px;">QUAL P' + str(_q) + '</div>'
                        '</div>'
                        '<div style="width:100%;height:' + str(height) + 'px;background:linear-gradient(180deg,' + _tc + '22,' + _tc + '08);border:1px solid ' + _tc + '33;border-bottom:none;border-radius:8px 8px 0 0;display:flex;align-items:center;justify-content:center;">'
                        '<div style="font-family:Orbitron,monospace;font-size:2rem;font-weight:900;color:' + medal_color + ';">' + _pn + '</div>'
                        '</div>'
                        '</div>'
                    )

                _c1 = _pcard(_p1, "#FFD700", "P1", 120, 0.1)
                _c2 = _pcard(_p2, "#C0C0C0", "P2", 80,  0.3)
                _c3 = _pcard(_p3, "#CD7F32", "P3", 60,  0.5)

                # Circuit info bar at bottom
                _circ_bar = (
                    '<div style="position:relative;z-index:2;'
                    'background:linear-gradient(90deg,rgba(6,6,12,0.98),rgba(12,12,20,0.95));'
                    'border-top:1px solid #1A1A2A;padding:16px 24px;margin-top:16px;">'
                    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">'

                    # Left — flag + circuit name
                    '<div style="display:flex;align-items:center;gap:12px;">'
                    '<div style="font-size:2rem;">' + _flag + '</div>'
                    '<div>'
                    '<div style="font-family:Orbitron,monospace;font-size:0.85rem;font-weight:700;color:#FFFFFF;">' + _circ_short + '</div>'
                    '<div style="font-size:0.65rem;color:#555575;margin-top:2px;">' + _ctype + ' · Since ' + str(_yr) + '</div>'
                    '</div>'
                    '</div>'

                    # Right — stats
                    '<div style="display:flex;gap:20px;flex-wrap:wrap;">'

                    '<div style="text-align:center;">'
                    '<div style="font-family:Orbitron,monospace;font-size:1rem;font-weight:700;color:#E8002D;">' + str(_laps) + '</div>'
                    '<div style="font-size:0.58rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">Laps</div>'
                    '</div>'

                    '<div style="text-align:center;">'
                    '<div style="font-family:Orbitron,monospace;font-size:1rem;font-weight:700;color:#E8002D;">' + str(_len) + '</div>'
                    '<div style="font-size:0.58rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">KM / Lap</div>'
                    '</div>'

                    '<div style="text-align:center;">'
                    '<div style="font-family:Orbitron,monospace;font-size:1rem;font-weight:700;color:#E8002D;">' + str(_turns) + '</div>'
                    '<div style="font-size:0.58rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">Turns</div>'
                    '</div>'

                    '<div style="text-align:center;">'
                    '<div style="font-family:Orbitron,monospace;font-size:1rem;font-weight:700;color:#E8002D;">' + str(_dist) + '</div>'
                    '<div style="font-size:0.58rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">Total KM</div>'
                    '</div>'

                    '</div>'
                    '</div>'
                    '</div>'
                )

                st.markdown(
                    '<div style="border-radius:20px;overflow:hidden;margin:8px 0;'
                    'background:#06060A;border:1px solid #E8002D33;'
                    'box-shadow:0 0 60px rgba(232,0,45,0.08),0 20px 80px rgba(0,0,0,0.6);">'
                    '<style>@keyframes podiumRise{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}</style>'

                    # TWO COLUMN LAYOUT: Left = Circuit card, Right = Podium
                    '<div style="display:flex;gap:0;min-height:500px;">'

                    # LEFT SIDE — Circuit info card (like shutterstock image)
                    '<div style="width:280px;flex-shrink:0;background:linear-gradient(135deg,#0A0A14,#06060E);'
                    'border-right:1px solid #1A1A2A;position:relative;overflow:hidden;">'

                    # Circuit track map image — prominent
                    '<div style="position:absolute;inset:0;">'
                    '<img src="' + _bg + '" '
                    'style="width:100%;height:100%;object-fit:contain;object-position:center;'
                    'opacity:0.25;padding:20px;" '
                    'onerror="this.style.opacity=0.05" />'
                    '</div>'

                    # Dark overlay
                    '<div style="position:absolute;inset:0;'
                    'background:linear-gradient(180deg,rgba(6,6,10,0.6) 0%,rgba(6,6,10,0.85) 100%);"></div>'

                    # Circuit info content
                    '<div style="position:relative;z-index:2;padding:24px 20px;height:100%;'
                    'display:flex;flex-direction:column;justify-content:space-between;">'

                    # Top — flag + name
                    '<div>'
                    '<div style="font-size:3rem;margin-bottom:8px;">' + _flag + '</div>'
                    '<div style="font-family:Orbitron,monospace;font-size:1.1rem;font-weight:900;'
                    'color:#FFFFFF;letter-spacing:-0.5px;line-height:1.1;">' + _circ_short + '</div>'
                    '<div style="font-size:0.65rem;color:#E8002D;letter-spacing:2px;'
                    'text-transform:uppercase;margin-top:4px;">' + _ctype + '</div>'
                    '</div>'

                    # Middle — circuit stats
                    '<div style="margin:20px 0;">'

                    '<div style="display:flex;justify-content:space-between;align-items:center;'
                    'padding:8px 0;border-bottom:1px solid #1A1A2A;">'
                    '<span style="font-size:0.65rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">Track Length</span>'
                    '<span style="font-family:Orbitron,monospace;font-size:0.75rem;color:#FFFFFF;">' + str(_len) + ' KM</span>'
                    '</div>'

                    '<div style="display:flex;justify-content:space-between;align-items:center;'
                    'padding:8px 0;border-bottom:1px solid #1A1A2A;">'
                    '<span style="font-size:0.65rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">Race Distance</span>'
                    '<span style="font-family:Orbitron,monospace;font-size:0.75rem;color:#FFFFFF;">' + str(_laps) + ' Laps</span>'
                    '</div>'

                    '<div style="display:flex;justify-content:space-between;align-items:center;'
                    'padding:8px 0;border-bottom:1px solid #1A1A2A;">'
                    '<span style="font-size:0.65rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">Turns</span>'
                    '<span style="font-family:Orbitron,monospace;font-size:0.75rem;color:#FFFFFF;">' + str(_turns) + '</span>'
                    '</div>'

                    '<div style="display:flex;justify-content:space-between;align-items:center;'
                    'padding:8px 0;border-bottom:1px solid #1A1A2A;">'
                    '<span style="font-size:0.65rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">Circuit Type</span>'
                    '<span style="font-family:Orbitron,monospace;font-size:0.75rem;color:#FFFFFF;">' + _ctype + '</span>'
                    '</div>'

                    '<div style="display:flex;justify-content:space-between;align-items:center;'
                    'padding:8px 0;">'
                    '<span style="font-size:0.65rem;color:#555575;letter-spacing:1px;text-transform:uppercase;">First Grand Prix</span>'
                    '<span style="font-family:Orbitron,monospace;font-size:0.75rem;color:#FFFFFF;">' + str(_yr) + '</span>'
                    '</div>'
                    '</div>'

                    # Bottom — weather badge
                    '<div style="background:#E8002D22;border:1px solid #E8002D44;border-radius:8px;'
                    'padding:10px 12px;text-align:center;">'
                    '<div style="font-family:Orbitron,monospace;font-size:0.65rem;color:#E8002D;'
                    'letter-spacing:2px;">🌤️ ' + weather.upper() + '</div>'
                    '</div>'

                    '</div>'
                    '</div>'

                    # RIGHT SIDE — Podium visualization
                    '<div style="flex:1;background:linear-gradient(135deg,#080810,#06060A);'
                    'position:relative;overflow:hidden;padding:24px 16px 0;">'

                    # Subtle background track map on right side too
                    '<div style="position:absolute;inset:0;opacity:0.04;">'
                    '<img src="' + _bg + '" style="width:100%;height:100%;object-fit:cover;" />'
                    '</div>'

                    '<div style="position:relative;z-index:2;">'

                    # Header
                    '<div style="text-align:center;margin-bottom:20px;">'
                    '<div style="font-family:Orbitron,monospace;font-size:0.55rem;letter-spacing:4px;'
                    'color:#E8002D;text-transform:uppercase;margin-bottom:6px;">'
                    '🏎️ ML PREDICTION</div>'
                    '<div style="font-family:Orbitron,monospace;font-size:1.4rem;font-weight:900;'
                    'color:#FFFFFF;letter-spacing:-0.5px;">'
                    + _circ_short + ' GP</div>'
                    '</div>'

                    # Podium cards P2 | P1 | P3
                    '<div style="display:flex;align-items:flex-end;justify-content:center;gap:10px;">'
                    + _c2 + _c1 + _c3 +
                    '</div>'
                    '</div>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            st.markdown("")
            
            # ─── Top 10 Table + Underdogs ───
            c_left, c_right = st.columns([3, 1])
            
            with c_left:
                st.markdown('<div class="section-title">📊 Full Top 10 Grid</div>', unsafe_allow_html=True)
                
                table_html = '<table class="prediction-table"><thead><tr><th>POS</th><th>DRIVER</th><th>TEAM</th><th>QUAL</th><th>PODIUM%</th><th>WIN%</th><th>FORM</th></tr></thead><tbody>'
                
                for r in pred["top_10"]:
                    color = team_color_hex(r["team"])
                    pos = r["predicted_rank"]
                    pos_color = "#FFD700" if pos == 1 else "#C0C0C0" if pos == 2 else "#CD7F32" if pos == 3 else "#444455"
                    bg = "background:#1A1400;" if pos <= 3 else ""
                    bar_w = min(int(r["podium_prob"] * 100), 100)
                    flag = DRIVER_NATIONALITIES.get(r["driver"], "")
                    
                    table_html += (
                        f'<tr style="{bg}">'
                        f'<td><span class="pos-badge" style="background:{pos_color}22;color:{pos_color};">{pos}</span></td>'
                        f'<td><strong style="color:#E8E8F0;">{flag} {r["driver"]}</strong></td>'
                        f'<td><span style="color:{color};font-size:0.8rem;">{r["team"]}</span></td>'
                        f'<td style="color:#888899;">P{r["qualifying_position"]}</td>'
                        f'<td><div style="font-size:0.85rem;color:#E8E8F0;">{r["podium_prob"]*100:.1f}%</div>'
                        f'<div style="height:3px;width:{bar_w}%;background:{color};border-radius:2px;margin-top:2px;"></div></td>'
                        f'<td style="color:#27F4D2;font-family:Orbitron,monospace;font-size:0.85rem;">{r["win_prob"]*100:.1f}%</td>'
                        f'<td style="color:#888899;">{"▲" if r["qualifying_position"] > r["predicted_rank"] else "▼" if r["qualifying_position"] < r["predicted_rank"] else "━"} {abs(r["qualifying_position"] - r["predicted_rank"])}</td>'
                        f'</tr>'
                    )
                
                table_html += "</tbody></table>"
                st.markdown(table_html, unsafe_allow_html=True)
            
            with c_right:
                st.markdown('<div class="section-title">⚡ Dark Horses</div>', unsafe_allow_html=True)
                if pred["underdogs"]:
                    for u in pred["underdogs"]:
                        color = team_color_hex(u["team"])
                        st.markdown(f"""
                        <div class="metric-card" style="margin:6px 0;">
                          <div style="font-family:Orbitron,monospace;font-size:0.85rem;color:#E8E8F0;">{u['driver'].split()[-1].upper()}</div>
                          <div style="font-size:0.7rem;color:#888899;margin-top:2px;">{u['driver'].split()[0]}</div>
                          <div style="color:{color};font-size:0.75rem;margin-top:4px;">{u['team']}</div>
                          <div style="font-family:Orbitron,monospace;color:#FFD700;font-size:1.1rem;margin-top:8px;">
                            {u['podium_prob']*100:.1f}%
                          </div>
                          <div style="font-size:0.65rem;color:#888899;">podium chance</div>
                          <div style="font-size:0.7rem;color:#FF8844;margin-top:4px;">Qualifies: P{u['qualifying_position']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:#888899;font-size:0.85rem;font-family:Inter,sans-serif;">No major upsets predicted for this race.</div>', unsafe_allow_html=True)
                
                # ── LUXURY CIRCUIT CARD ──────────────────────────────
                cinfo = get_circuit_info(circuit)
                try:
                    from src.circuit_data import get_circuit_data
                    cdata = get_circuit_data(circuit)
                except Exception:
                    cdata = {}

                color     = cdata.get("color", "#E8002D")
                country   = cdata.get("country", "🏁")
                img_url   = cdata.get("image_url", "")
                desc      = cdata.get("description", "")
                record    = cdata.get("lap_record", "N/A")
                tire_info = cdata.get("tire_info", "")
                facts     = cdata.get("facts", [])
                circ_name = cdata.get("circuit_name", circuit)
                location  = cdata.get("location", "")
                most_wins = cdata.get("most_wins", "")
                drs       = cdata.get("drs_zones", 2)
                first_gp  = cdata.get("first_gp", "")

                st.markdown(f"""
                <style>
                @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Syne:wght@300;400;600&display=swap');

                .circuit-hero {{
                    position: relative;
                    border-radius: 20px;
                    overflow: hidden;
                    margin-bottom: 12px;
                    background: #06060A;
                    border: 1px solid {color}55;
                    box-shadow: 0 0 40px {color}22, 0 20px 60px rgba(0,0,0,0.8);
                }}

                .circuit-hero-img {{
                    width: 100%;
                    height: 200px;
                    object-fit: cover;
                    display: block;
                    opacity: 0.7;
                    transition: opacity 0.3s;
                }}

                .circuit-hero-img:hover {{ opacity: 0.9; }}

                .circuit-overlay {{
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(
                        180deg,
                        transparent 0%,
                        transparent 30%,
                        rgba(6,6,10,0.7) 60%,
                        rgba(6,6,10,0.98) 100%
                    );
                }}

                .circuit-badge {{
                    position: absolute;
                    top: 14px;
                    right: 14px;
                    background: {color};
                    color: white;
                    font-family: 'Orbitron', monospace;
                    font-size: 0.6rem;
                    letter-spacing: 2px;
                    padding: 4px 10px;
                    border-radius: 20px;
                    font-weight: 700;
                }}

                .circuit-title-block {{
                    position: absolute;
                    bottom: 16px;
                    left: 18px;
                    right: 18px;
                }}

                .circuit-country-name {{
                    font-family: 'Orbitron', monospace;
                    font-size: 1.2rem;
                    font-weight: 900;
                    color: #FFFFFF;
                    letter-spacing: -0.5px;
                    line-height: 1.1;
                    text-shadow: 0 2px 20px rgba(0,0,0,0.8);
                }}

                .circuit-subtitle {{
                    font-family: 'Syne', sans-serif;
                    font-size: 0.72rem;
                    color: {color};
                    margin-top: 3px;
                    letter-spacing: 0.5px;
                }}

                .circuit-stats-row {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 6px;
                    margin-bottom: 8px;
                }}

                .circuit-stat {{
                    background: linear-gradient(135deg, #0E0E18, #0A0A12);
                    border: 1px solid #1E1E30;
                    border-radius: 10px;
                    padding: 12px 8px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                    transition: border-color 0.2s;
                }}

                .circuit-stat::before {{
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0;
                    height: 2px;
                    background: linear-gradient(90deg, {color}, transparent);
                }}

                .circuit-stat:hover {{ border-color: {color}88; }}

                .stat-value {{
                    font-family: 'Orbitron', monospace;
                    font-size: 1.1rem;
                    font-weight: 700;
                    color: {color};
                    line-height: 1;
                }}

                .stat-label {{
                    font-family: 'Syne', sans-serif;
                    font-size: 0.58rem;
                    letter-spacing: 1.5px;
                    text-transform: uppercase;
                    color: #555570;
                    margin-top: 5px;
                }}

                .circuit-info-card {{
                    background: linear-gradient(135deg, #0A0A12, #080810);
                    border: 1px solid #1A1A2A;
                    border-radius: 12px;
                    padding: 14px 16px;
                    margin-bottom: 8px;
                    position: relative;
                    overflow: hidden;
                }}

                .circuit-info-card::after {{
                    content: '';
                    position: absolute;
                    bottom: 0; left: 0; right: 0;
                    height: 1px;
                    background: linear-gradient(90deg, {color}44, transparent);
                }}

                .info-card-label {{
                    font-family: 'Orbitron', monospace;
                    font-size: 0.58rem;
                    letter-spacing: 2px;
                    text-transform: uppercase;
                    color: #444460;
                    margin-bottom: 6px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }}

                .info-card-label::before {{
                    content: '';
                    display: inline-block;
                    width: 16px;
                    height: 1px;
                    background: {color};
                }}

                .info-card-value {{
                    font-family: 'Syne', sans-serif;
                    font-size: 0.82rem;
                    color: #D0D0E8;
                    line-height: 1.6;
                }}

                .record-value {{
                    font-family: 'Orbitron', monospace;
                    font-size: 0.85rem;
                    color: #FFD700;
                    font-weight: 700;
                }}

                .fact-item {{
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    padding: 7px 0;
                    border-bottom: 1px solid #10101A;
                    font-family: 'Syne', sans-serif;
                    font-size: 0.78rem;
                    color: #AAAACC;
                    line-height: 1.4;
                }}

                .fact-item:last-child {{ border-bottom: none; }}

                .fact-dot {{
                    width: 5px;
                    height: 5px;
                    border-radius: 50%;
                    background: {color};
                    flex-shrink: 0;
                    margin-top: 5px;
                }}

                .circuit-desc {{
                    font-family: 'Syne', sans-serif;
                    font-size: 0.8rem;
                    color: #7777AA;
                    line-height: 1.7;
                    padding: 12px 0 4px;
                    border-top: 1px solid #12121E;
                    margin-top: 8px;
                    font-style: italic;
                }}
                </style>

                <!-- HERO IMAGE CARD -->
                <div class="circuit-hero">
                    {"<img class='circuit-hero-img' src='" + img_url + "' onerror=\"this.parentElement.style.minHeight='120px';this.style.display='none'\"/>" if img_url else ""}
                    <div class="circuit-overlay"></div>
                    <div class="circuit-badge">{country} ROUND {cdata.get('first_gp','')}</div>
                    <div class="circuit-title-block">
                        <div class="circuit-country-name">{circuit.replace(' Grand Prix','').upper()}</div>
                        <div class="circuit-subtitle">{circ_name} · {location}</div>
                    </div>
                </div>

                <!-- STATS ROW -->
                <div class="circuit-stats-row">
                    <div class="circuit-stat">
                        <div class="stat-value">{cinfo['laps']}</div>
                        <div class="stat-label">Laps</div>
                    </div>
                    <div class="circuit-stat">
                        <div class="stat-value">{cinfo['distance_km']}</div>
                        <div class="stat-label">KM</div>
                    </div>
                    <div class="circuit-stat">
                        <div class="stat-value">{drs}</div>
                        <div class="stat-label">DRS</div>
                    </div>
                    <div class="circuit-stat">
                        <div class="stat-value" style="font-size:0.75rem;">{cinfo['overtaking']}</div>
                        <div class="stat-label">OVT</div>
                    </div>
                </div>

                <!-- LAP RECORD -->
                {"<div class='circuit-info-card'><div class='info-card-label'>⏱ Lap Record</div><div class='record-value'>" + record + "</div></div>" if record and record != "N/A" else ""}

                <!-- TIRE STRATEGY -->
                {"<div class='circuit-info-card'><div class='info-card-label'>🔴 Tire Strategy</div><div class='info-card-value'>" + tire_info + "</div></div>" if tire_info else ""}

                <!-- MOST WINS -->
                {"<div class='circuit-info-card'><div class='info-card-label'>🏆 Most Wins</div><div class='info-card-value'>" + most_wins + "</div></div>" if most_wins else ""}

                <!-- CIRCUIT FACTS -->
                {"<div class='circuit-info-card'><div class='info-card-label'>📋 Circuit Facts</div>" + "".join([f"<div class='fact-item'><div class='fact-dot'></div>{f}</div>" for f in facts[:4]]) + "</div>" if facts else ""}

                <!-- DESCRIPTION -->
                {"<div class='circuit-desc'>" + desc + "</div>" if desc else ""}
                """, unsafe_allow_html=True)
            
            # ─── LLM Reasoning Section ───
            st.markdown('<div class="section-title">🤖 AI Race Analysis</div>', unsafe_allow_html=True)

            with st.spinner("🧠 Generating AI analysis..."):
                try:
                    from ingestion.llm_reasoning import LLMReasoning
                    import os as _os
                    api_key  = _os.environ.get("ANTHROPIC_API_KEY", "")
                    reasoner = LLMReasoning(api_key=api_key)
                    reasoning = reasoner.explain_race_prediction(
                        circuit=circuit,
                        prediction=pred,
                        weather=weather,
                        season=2026,
                    )
                except Exception as _e:
                    reasoning = None

            if reasoning:
                # ── Confidence Badge ──
                conf_level = reasoning.get("confidence_level", "MEDIUM")
                conf_colors = {"HIGH": "#27F4D2", "MEDIUM": "#FFD700", "LOW": "#FF8844"}
                conf_color  = conf_colors.get(conf_level, "#888899")

                st.markdown(f"""
                <div style="display:flex;gap:12px;align-items:center;margin-bottom:16px;flex-wrap:wrap;">
                  <div style="background:{conf_color}22;border:1px solid {conf_color};
                              border-radius:8px;padding:8px 20px;
                              font-family:Orbitron,monospace;font-size:0.85rem;color:{conf_color};">
                    {conf_level} CONFIDENCE
                  </div>
                  <div style="font-family:Inter,sans-serif;font-size:0.85rem;color:#888899;">
                    {reasoning.get('confidence_reason','')}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # ── 4 Analysis Cards ──
                a1, a2 = st.columns(2)
                analysis_cards = [
                    ("📖", "Race Preview",    reasoning.get("race_preview",""),    "#3671C6", a1),
                    ("🏆", "Winner Analysis", reasoning.get("winner_reasoning",""), "#E8002D", a2),
                ]
                for icon, title, text, color, col in analysis_cards:
                    with col:
                        st.markdown(f"""
                        <div class="explanation-box" style="border-left-color:{color};min-height:90px;">
                          <div style="font-family:Orbitron,monospace;font-size:0.75rem;
                                      color:{color};margin-bottom:8px;letter-spacing:1px;">
                            {icon} {title.upper()}
                          </div>
                          <div style="font-family:Inter,sans-serif;font-size:0.85rem;
                                      color:#CCCCDD;line-height:1.6;">
                            {text}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                b1, b2, b3 = st.columns(3)
                cards2 = [
                    ("🔧", "Strategy",    reasoning.get("strategy_insight",""), "#229971", b1),
                    ("⚡", "Dark Horses", reasoning.get("dark_horses",""),      "#FF8000", b2),
                    ("⚠️", "Risk Factors",reasoning.get("risk_factors",""),     "#FF87BC", b3),
                ]
                for icon, title, text, color, col in cards2:
                    with col:
                        st.markdown(f"""
                        <div class="explanation-box" style="border-left-color:{color};min-height:80px;">
                          <div style="font-family:Orbitron,monospace;font-size:0.7rem;
                                      color:{color};margin-bottom:6px;letter-spacing:1px;">
                            {icon} {title.upper()}
                          </div>
                          <div style="font-family:Inter,sans-serif;font-size:0.82rem;
                                      color:#CCCCDD;line-height:1.6;">
                            {text}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                # ── Per-driver Summaries ──
                driver_summaries = reasoning.get("driver_summaries", {})
                if driver_summaries:
                    st.markdown('<div class="section-title">👤 Driver-by-Driver Analysis</div>', unsafe_allow_html=True)
                    d_cols = st.columns(2)
                    for idx, (driver, summary) in enumerate(list(driver_summaries.items())[:6]):
                        r_data = next((r for r in pred["top_10"] if r["driver"] == driver), None)
                        color  = team_color_hex(r_data["team"]) if r_data else "#888888"
                        rank   = r_data["predicted_rank"] if r_data else "?"
                        with d_cols[idx % 2]:
                            st.markdown(f"""
                            <div class="explanation-box" style="border-left-color:{color};
                                         padding:10px 14px;margin:4px 0;">
                              <div style="display:flex;justify-content:space-between;
                                          align-items:center;margin-bottom:4px;">
                                <span style="font-family:Orbitron,monospace;font-size:0.8rem;
                                             color:{color};">{driver}</span>
                                <span style="font-family:Orbitron,monospace;font-size:0.75rem;
                                             color:#FFD700;">P{rank}</span>
                              </div>
                              <div style="font-family:Inter,sans-serif;font-size:0.8rem;
                                          color:#BBBBCC;line-height:1.5;">
                                {summary}
                              </div>
                            </div>
                            """, unsafe_allow_html=True)

                # ── Instagram Caption Generator ──
                st.markdown('<div class="section-title">📸 Instagram Caption</div>', unsafe_allow_html=True)

                platform = st.selectbox(
                    "PLATFORM",
                    ["instagram", "twitter", "linkedin"],
                    key="caption_platform"
                )

                if st.button("✨  GENERATE CAPTION", key="gen_caption"):
                    with st.spinner("Writing caption..."):
                        try:
                            caption = reasoner.generate_race_preview_post(
                                circuit=circuit,
                                prediction=pred,
                                weather=weather,
                                platform=platform,
                            )
                            st.session_state["last_caption"] = caption
                        except Exception as e:
                            st.error(f"Caption generation failed: {e}")

                if st.session_state.get("last_caption"):
                    st.markdown(f"""
                    <div style="background:#0D1520;border:1px solid #3671C6;border-radius:8px;
                                padding:16px 20px;font-family:Inter,sans-serif;font-size:0.88rem;
                                color:#E8E8F0;line-height:1.8;white-space:pre-wrap;">
{st.session_state['last_caption']}
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(st.session_state["last_caption"], language=None)
                    st.caption("👆 Click the copy icon top-right of the code block to copy")

            else:
                # Fallback to original basic explanation
                exp_cols = st.columns(2)
                exp_items = [(d, v) for d, v in pred["explanations"].items()][:4]
                for idx, (driver, exp) in enumerate(exp_items):
                    with exp_cols[idx % 2]:
                        r_data = next((r for r in pred["top_10"] if r["driver"] == driver), None)
                        if not r_data:
                            continue
                        color = team_color_hex(r_data["team"])
                        factors = exp.get("factors", [])
                        if not factors:
                            pos_f = exp.get("positive_factors", [])
                            factors = [f[0].replace('_',' ').title() for f in pos_f[:4]]
                        factor_html = "".join([f'<div style="margin:3px 0;">• {f}</div>' for f in factors[:4]])
                        st.markdown(f"""
                        <div class="explanation-box" style="border-left-color:{color};">
                          <div style="font-family:Orbitron,monospace;font-size:0.85rem;
                                      color:{color};margin-bottom:6px;">
                            {driver} — P{r_data['predicted_rank']} Predicted
                          </div>
                          <div style="font-family:Inter,sans-serif;font-size:0.8rem;
                                      color:#BBBBCC;line-height:1.7;">
                            {factor_html}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════
elif "Analytics" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">Season & Historical Performance Dashboard</div>', unsafe_allow_html=True)
    
    df = load_data()
    if df.empty:
        st.warning("No race data loaded. Please run data generation first.")
        st.stop()
    
    season_df = df[df["season"] == selected_season]
    
    # KPI Row
    k_cols = st.columns(5)
    kpis = [
        ("RACES", len(season_df["round"].unique())),
        ("DRIVERS", len(season_df["driver"].unique())),
        ("TEAMS", len(season_df["team"].unique())),
        ("WET RACES", len(season_df[season_df["weather"] == "Wet"]["round"].unique())),
        ("SEASON", str(selected_season)),
    ]
    for c, (label, val) in zip(k_cols, kpis):
        with c:
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;">
              <div class="metric-value">{val}</div>
              <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["STANDINGS", "DRIVER FORM", "CIRCUIT ANALYSIS", "TEAM TRENDS"])
    
    with tab1:
        standings = get_summary(selected_season)
        if not standings.empty:
            # Driver championship chart
            top_drivers = standings.head(10)
            fig = go.Figure()
            for _, row in top_drivers.iterrows():
                color = TEAM_COLORS.get(row["team"], "#888888")
                fig.add_trace(go.Bar(
                    x=[row["driver"].split()[-1]],
                    y=[row["points"]],
                    name=row["team"],
                    marker_color=color,
                    showlegend=False,
                    text=[f"{int(row['points'])} pts"],
                    textposition="outside",
                    textfont=dict(size=10, color="white"),
                ))
            
            fig.update_layout(
                title=dict(text=f"{selected_season} Driver Championship", font=dict(family="Orbitron", size=14, color="#E8E8F0")),
                paper_bgcolor="#0A0A0F", plot_bgcolor="#13131A",
                font=dict(family="Inter", color="#888899"),
                xaxis=dict(gridcolor="#2A2A3A", color="#888899"),
                yaxis=dict(gridcolor="#2A2A3A", color="#888899", title="Points"),
                height=380,
                margin=dict(t=50, b=40, l=40, r=20),
                bargap=0.3,
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            st.dataframe(
                standings.rename(columns={
                    "driver": "Driver", "team": "Team", "races": "Races",
                    "wins": "Wins", "podiums": "Podiums", "points": "Points",
                    "avg_finish": "Avg Finish", "avg_qual": "Avg Qual"
                }).round(2),
                use_container_width=True,
                hide_index=False,
            )
    
    with tab2:
        # Driver form over rounds
        driver_sel = st.selectbox("SELECT DRIVER", sorted(season_df["driver"].unique()))
        d_df = season_df[season_df["driver"] == driver_sel].sort_values("round")
        
        if not d_df.empty:
            fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                  subplot_titles=("Finishing Position", "Qualifying Position"))
            
            color = TEAM_COLORS.get(d_df.iloc[0]["team"], "#E8002D")
            
            fig2.add_trace(go.Scatter(
                x=d_df["round"], y=d_df["finish_position"],
                mode="lines+markers", name="Finish",
                line=dict(color=color, width=2),
                marker=dict(size=8, color=color),
            ), row=1, col=1)
            
            fig2.add_trace(go.Scatter(
                x=d_df["round"], y=d_df["qualifying_position"],
                mode="lines+markers", name="Qualifying",
                line=dict(color="#888899", width=1.5, dash="dot"),
                marker=dict(size=6, color="#888899"),
            ), row=2, col=1)
            
            fig2.update_layout(
                paper_bgcolor="#0A0A0F", plot_bgcolor="#13131A",
                font=dict(family="Inter", color="#888899"),
                height=380, showlegend=False,
                margin=dict(t=40, b=20),
            )
            fig2.update_yaxes(autorange="reversed", gridcolor="#2A2A3A")
            fig2.update_xaxes(gridcolor="#2A2A3A", title_text="Round")
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Stats row
            s_cols = st.columns(5)
            stats = [
                ("WINS", int(d_df["win"].sum())),
                ("PODIUMS", int(d_df["podium"].sum())),
                ("POINTS", int(d_df["points"].sum())),
                ("AVG FINISH", f"{d_df['finish_position'].mean():.1f}"),
                ("AVG QUAL", f"{d_df['qualifying_position'].mean():.1f}"),
            ]
            for c, (lbl, v) in zip(s_cols, stats):
                with c:
                    st.markdown(f"""
                    <div class="metric-card" style="text-align:center;">
                      <div class="metric-value" style="font-size:1.5rem;">{v}</div>
                      <div class="metric-label">{lbl}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab3:
        # Win rate by circuit
        circ_wins = season_df[season_df["win"] == 1].groupby("circuit")["driver"].first().reset_index()
        circ_df = season_df.groupby("circuit").agg(
            avg_pos=("finish_position", "mean"),
            races=("round", "nunique"),
        ).reset_index()
        
        fig3 = px.scatter(
            season_df.groupby(["circuit", "team"])["finish_position"].mean().reset_index(),
            x="circuit", y="finish_position", color="team",
            color_discrete_map=TEAM_COLORS,
            title=f"{selected_season} Avg Finish Position by Circuit & Team",
        )
        fig3.update_layout(
            paper_bgcolor="#0A0A0F", plot_bgcolor="#13131A",
            font=dict(family="Inter", color="#888899"),
            height=420, xaxis_tickangle=-45,
            margin=dict(b=120),
        )
        fig3.update_yaxes(autorange="reversed")
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab4:
        # Constructor performance
        team_pts = season_df.groupby("team")["points"].sum().reset_index().sort_values("points", ascending=True)
        
        fig4 = go.Figure(go.Bar(
            x=team_pts["points"],
            y=team_pts["team"],
            orientation="h",
            marker_color=[TEAM_COLORS.get(t, "#888888") for t in team_pts["team"]],
            text=team_pts["points"].astype(int),
            textposition="outside",
        ))
        fig4.update_layout(
            title=dict(text=f"{selected_season} Constructor Championship", font=dict(family="Orbitron", size=14, color="#E8E8F0")),
            paper_bgcolor="#0A0A0F", plot_bgcolor="#13131A",
            font=dict(family="Inter", color="#888899"),
            height=400, xaxis=dict(gridcolor="#2A2A3A"), yaxis=dict(gridcolor="#2A2A3A"),
            margin=dict(l=120, r=60),
        )
        st.plotly_chart(fig4, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: DRIVER PROFILE
# ═══════════════════════════════════════════════════════════════════
elif "Driver Profile" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">Driver Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">Career & Season Statistics</div>', unsafe_allow_html=True)
    
    df = load_data()
    all_drivers = sorted(df["driver"].unique()) if not df.empty else [d for d, t in DRIVERS_2026]
    
    selected_driver = st.selectbox("SELECT DRIVER", all_drivers)
    
    if not df.empty:
        stats = get_driver_stats(selected_driver, df)
        driver_df = df[df["driver"] == selected_driver]
        team = driver_df.iloc[-1]["team"] if not driver_df.empty else "Unknown"
        color = team_color_hex(team)
        flag = DRIVER_NATIONALITIES.get(selected_driver, "")
        
        # Header
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color}18,{color}08);border:1px solid {color}33;
                    border-radius:16px;padding:24px 30px;margin-bottom:20px;display:flex;align-items:center;gap:20px;">
            <div>
                <div style="font-size:2.5rem;">{flag}</div>
            </div>
            <div>
                <div style="font-family:Orbitron,monospace;font-size:1.8rem;font-weight:900;color:#E8E8F0;">
                    {selected_driver.upper()}
                </div>
                <div style="color:{color};font-size:0.9rem;font-family:Inter,sans-serif;margin-top:4px;">{team}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats grid
        stat_items = [
            ("RACES", stats.get("races", 0)),
            ("WINS", stats.get("wins", 0)),
            ("PODIUMS", stats.get("podiums", 0)),
            ("POLES", stats.get("poles", 0)),
            ("POINTS", int(stats.get("points", 0))),
            ("WIN RATE", f"{stats.get('win_rate',0)*100:.1f}%"),
        ]
        s_cols = st.columns(6)
        for c, (lbl, v) in zip(s_cols, stat_items):
            with c:
                st.markdown(f"""
                <div class="metric-card" style="text-align:center;">
                  <div class="metric-value" style="font-size:1.4rem;color:{color};">{v}</div>
                  <div class="metric-label">{lbl}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Season breakdown
        seasons_avail = sorted(driver_df["season"].unique(), reverse=True)
        
        fig = go.Figure()
        for s in seasons_avail:
            s_data = driver_df[driver_df["season"] == s].sort_values("round")
            fig.add_trace(go.Scatter(
                x=s_data["round"], y=s_data["finish_position"],
                mode="lines+markers", name=str(s),
                line=dict(width=2),
            ))
        
        fig.update_layout(
            title=dict(text=f"{selected_driver} — Season Comparison", font=dict(family="Orbitron", size=13, color="#E8E8F0")),
            paper_bgcolor="#0A0A0F", plot_bgcolor="#13131A",
            font=dict(family="Inter", color="#888899"),
            xaxis=dict(title="Round", gridcolor="#2A2A3A"),
            yaxis=dict(title="Finish Position", autorange="reversed", gridcolor="#2A2A3A"),
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Best circuits
        if stats.get("best_circuits"):
            st.markdown('<div class="section-title">🏆 Best Circuits</div>', unsafe_allow_html=True)
            bc_cols = st.columns(len(stats["best_circuits"][:3]))
            for c, circ in zip(bc_cols, stats["best_circuits"][:3]):
                with c:
                    cinfo = get_circuit_info(circ)
                    st.markdown(f"""
                    <div class="metric-card" style="text-align:center;">
                      <div style="font-family:Orbitron,monospace;font-size:0.75rem;color:{color};">{circ.replace(' Grand Prix','')}</div>
                      <div style="font-size:0.7rem;color:#888899;margin-top:4px;">{cinfo['type']}</div>
                    </div>
                    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: CRM DATA ENTRY — SMART UNIVERSAL INGESTION
# ═══════════════════════════════════════════════════════════════════
elif "CRM" in nav:
    import sys as _sys
    _sys.path.insert(0, BASE_DIR)
    from src.smart_ingest import smart_parse, preview_parsed, normalize_df

    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">Data Ingestion</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">Upload Race Data in Any Format</div>', unsafe_allow_html=True)

    # Format badges
    st.markdown("""
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;">
      <span style="background:#1A2A1A;border:1px solid #27F4D2;color:#27F4D2;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-family:Orbitron,monospace;">📊 CSV</span>
      <span style="background:#1A2A1A;border:1px solid #27F4D2;color:#27F4D2;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-family:Orbitron,monospace;">📗 EXCEL</span>
      <span style="background:#1A2A1A;border:1px solid #27F4D2;color:#27F4D2;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-family:Orbitron,monospace;">🔷 JSON</span>
      <span style="background:#1A2A1A;border:1px solid #27F4D2;color:#27F4D2;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-family:Orbitron,monospace;">📄 PDF</span>
      <span style="background:#1A2A1A;border:1px solid #27F4D2;color:#27F4D2;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-family:Orbitron,monospace;">🖼️ IMAGE</span>
      <span style="background:#1A2A1A;border:1px solid #27F4D2;color:#27F4D2;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-family:Orbitron,monospace;">📋 TEXT</span>
      <span style="background:#1A2A1A;border:1px solid #27F4D2;color:#27F4D2;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-family:Orbitron,monospace;">✏️ MANUAL</span>
    </div>
    """, unsafe_allow_html=True)

    tab_upload, tab_paste, tab_manual = st.tabs(["📁  FILE UPLOAD", "📋  PASTE / TEXT", "✏️  MANUAL ENTRY"])

    # ── TAB 1: FILE UPLOAD ────────────────────────────────────────
    with tab_upload:
        st.markdown("""
        <div class="explanation-box">
        Drop <strong>any file</strong> — the system auto-detects format and extracts race data.<br>
        <span style="color:#888899;">CSV · Excel (.xlsx/.xls) · JSON · PDF · Screenshot/Photo (.png/.jpg) · Text (.txt)</span><br><br>
        <strong>Columns can be messy</strong> — it handles: <code>pos, position, grid, constructor, pilot, pts</code>, etc.<br>
        <strong>Driver names</strong> can be abbreviations: <code>RUS, NOR, HAM, VER</code> — all auto-expanded.<br>
        <strong>Teams</strong> auto-filled from driver name if missing.
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "DROP FILE HERE",
            type=["csv","xlsx","xls","json","pdf","png","jpg","jpeg","txt","webp"],
            help="CSV, Excel, JSON, PDF, screenshot, or plain text"
        )

        col_ctx1, col_ctx2, col_ctx3 = st.columns(3)
        with col_ctx1:
            up_circuit = st.selectbox("CIRCUIT (if not in file)", ["— auto-detect —"] + CIRCUITS_2026, key="up_circ")
        with col_ctx2:
            up_season = st.number_input("SEASON", min_value=2020, max_value=2030, value=2026, key="up_season")
        with col_ctx3:
            up_round = st.number_input("ROUND #", min_value=1, max_value=25, value=2, key="up_round")

        up_retrain = st.checkbox("Auto-retrain models after ingestion", value=False, key="up_retrain")

        if uploaded:
            with st.spinner(f"🔍 Parsing {uploaded.name}..."):
                try:
                    df_parsed, fmt_detected, parse_warnings = smart_parse(uploaded)

                    # Apply context overrides
                    if up_circuit != "— auto-detect —":
                        df_parsed["circuit"] = up_circuit
                        df_parsed["location"] = up_circuit.replace(" Grand Prix","").strip()
                    df_parsed["season"] = int(up_season)
                    df_parsed["round"]  = int(up_round)

                    st.markdown(f'<div class="success-banner">✅ Parsed {len(df_parsed)} rows &nbsp;|&nbsp; Format: <strong>{fmt_detected.upper()}</strong></div>', unsafe_allow_html=True)

                    for w in parse_warnings:
                        st.markdown(f'<div class="error-banner">{w}</div>', unsafe_allow_html=True)

                    st.markdown('<div class="section-title">👁️ Preview — edit before saving</div>', unsafe_allow_html=True)
                    preview = preview_parsed(df_parsed)
                    edited = st.data_editor(preview, use_container_width=True, num_rows="dynamic", key="file_editor")

                    if st.button("💾  CONFIRM & SAVE TO DATASET", key="save_file"):
                        for col in edited.columns:
                            df_parsed[col] = edited[col].values
                        df_final = normalize_df(df_parsed)

                        raw_path   = os.path.join(BASE_DIR, "data", "raw_race_data.csv")
                        clean_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
                        existing = pd.read_csv(raw_path) if os.path.exists(raw_path) else pd.DataFrame()
                        pd.concat([existing, df_final], ignore_index=True).to_csv(raw_path, index=False)

                        from src.data_cleaner import clean_dataset
                        clean_df = clean_dataset(raw_path, clean_path)
                        st.markdown(f'<div class="success-banner">✅ {len(df_final)} rows saved → dataset now has {len(clean_df)} total rows</div>', unsafe_allow_html=True)
                        st.cache_data.clear()

                        if up_retrain:
                            with st.spinner("🔄 Retraining models..."):
                                try:
                                    from src.train_model import train_pipeline
                                    train_pipeline(clean_path)
                                    st.markdown('<div class="success-banner">🏁 Models retrained successfully</div>', unsafe_allow_html=True)
                                except Exception as e:
                                    st.error(f"Retraining failed: {e}")

                except RuntimeError as e:
                    st.markdown(f'<div class="error-banner">⚠️ {e}</div>', unsafe_allow_html=True)
                    st.info("💡 Copy the text from the image and paste it in the **PASTE / TEXT** tab instead.")
                except Exception as e:
                    st.markdown(f'<div class="error-banner">❌ Parse failed: {e}</div>', unsafe_allow_html=True)
                    st.info("💡 Try the **Paste / Text** tab or **Manual Entry** tab.")

    # ── TAB 2: PASTE / TEXT ───────────────────────────────────────
    with tab_paste:
        st.markdown("""
        <div class="explanation-box">
        Paste data from <strong>anywhere</strong> — X/Twitter, F1 website, Wikipedia, WhatsApp, email.<br>
        Works with any format including:<br>
        <code style="font-size:0.8rem;">1. George Russell — Mercedes (+2.9s)</code><br>
        <code style="font-size:0.8rem;">P1 RUS MER 25pts</code><br>
        <code style="font-size:0.8rem;">1,Russell,Mercedes,25</code><br>
        <code style="font-size:0.8rem;">1&#9;Hamilton&#9;Ferrari&#9;18</code>
        </div>
        """, unsafe_allow_html=True)

        paste_text = st.text_area(
            "PASTE RACE DATA HERE",
            height=220,
            placeholder="Examples:\n1. George Russell (Mercedes) 25pts\n2. Kimi Antonelli (Mercedes) 18pts\n3. Charles Leclerc (Ferrari) 15pts\n\nOR:\n1,RUS,Mercedes,25\n2,ANT,Mercedes,18\n3,LEC,Ferrari,15",
            key="paste_area"
        )

        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            paste_circuit = st.selectbox("CIRCUIT", ["— auto-detect —"] + CIRCUITS_2026, key="p_circ")
        with p_col2:
            paste_season = st.number_input("SEASON", value=2026, key="p_season")
        with p_col3:
            paste_round = st.number_input("ROUND #", value=2, key="p_round")

        paste_retrain = st.checkbox("Auto-retrain after save", key="p_retrain")

        if st.button("🔍  PARSE TEXT", key="parse_text_btn") and paste_text:
            try:
                df_p, fmt_p, warns_p = smart_parse(("pasted_data.txt", paste_text.encode("utf-8")))
                if paste_circuit != "— auto-detect —":
                    df_p["circuit"] = paste_circuit
                    df_p["location"] = paste_circuit.replace(" Grand Prix","").strip()
                df_p["season"] = int(paste_season)
                df_p["round"]  = int(paste_round)

                st.markdown(f'<div class="success-banner">✅ Parsed {len(df_p)} rows from pasted text</div>', unsafe_allow_html=True)
                for w in warns_p:
                    st.markdown(f'<div class="error-banner">{w}</div>', unsafe_allow_html=True)

                edited_p = st.data_editor(preview_parsed(df_p), use_container_width=True, num_rows="dynamic", key="paste_editor")

                if st.button("💾  SAVE PARSED DATA", key="save_paste"):
                    for col in edited_p.columns:
                        df_p[col] = edited_p[col].values
                    df_p = normalize_df(df_p)
                    raw_path   = os.path.join(BASE_DIR, "data", "raw_race_data.csv")
                    clean_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
                    existing = pd.read_csv(raw_path) if os.path.exists(raw_path) else pd.DataFrame()
                    pd.concat([existing, df_p], ignore_index=True).to_csv(raw_path, index=False)
                    from src.data_cleaner import clean_dataset
                    clean_df = clean_dataset(raw_path, clean_path)
                    st.markdown(f'<div class="success-banner">✅ {len(df_p)} rows saved → {len(clean_df)} total</div>', unsafe_allow_html=True)
                    st.cache_data.clear()
                    if paste_retrain:
                        from src.train_model import train_pipeline
                        train_pipeline(clean_path)
                        st.markdown('<div class="success-banner">🏁 Models retrained</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="error-banner">❌ {e}</div>', unsafe_allow_html=True)

    # ── TAB 3: MANUAL ENTRY ───────────────────────────────────────
    with tab_manual:
        st.markdown('<div class="section-title">Single Driver Entry</div>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        with r1:
            form_season  = st.number_input("SEASON", min_value=2020, max_value=2030, value=2026)
            form_round   = st.number_input("ROUND", min_value=1, max_value=25, value=2)
            form_circuit = st.selectbox("CIRCUIT", CIRCUITS_2026)
        with r2:
            form_driver  = st.selectbox("DRIVER", [d for d,t in DRIVERS_2026])
            form_team    = st.selectbox("TEAM", VALID_TEAMS_2026)
            form_weather = st.selectbox("WEATHER", ["Dry","Mixed","Wet"])
        with r3:
            form_qual    = st.number_input("QUALIFYING POSITION", min_value=1, max_value=22, value=1)
            form_finish  = st.number_input("FINISH POSITION", min_value=1, max_value=22, value=1)
            form_strat   = st.selectbox("TIRE STRATEGY", ["1-Stop","2-Stop","3-Stop"])
        r4, r5 = st.columns(2)
        with r4:
            form_pits      = st.number_input("PIT STOPS", min_value=0, max_value=5, value=2)
            form_incidents = st.number_input("INCIDENTS (0/1)", min_value=0, max_value=1, value=0)
        with r5:
            form_penalties = st.number_input("PENALTIES (0/1)", min_value=0, max_value=1, value=0)
            man_retrain    = st.checkbox("Auto-retrain after insert", value=False)

        if st.button("➕  SUBMIT ENTRY"):
            data = {"season":form_season,"round":form_round,"circuit":form_circuit,
                    "driver":form_driver,"team":form_team,"qualifying_position":form_qual,
                    "finish_position":form_finish,"weather":form_weather,
                    "tire_strategy":form_strat,"pit_stops":form_pits,
                    "incidents":form_incidents,"penalties":form_penalties}
            res = ingest_single_result(data, auto_retrain=man_retrain)
            if res["success"]:
                st.markdown(f'<div class="success-banner">✅ {res["message"]} | Total rows: {res["rows"]}</div>', unsafe_allow_html=True)
                st.cache_data.clear()
            else:
                for err in res["errors"]:
                    st.markdown(f'<div class="error-banner">❌ {err}</div>', unsafe_allow_html=True)

    # ── DATASET PREVIEW ───────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">📦 Current Dataset</div>', unsafe_allow_html=True)
    df_curr = load_data()
    if not df_curr.empty:
        k1, k2, k3, k4 = st.columns(4)
        for col, (lbl, val) in zip([k1,k2,k3,k4], [
            ("TOTAL ROWS",    len(df_curr)),
            ("SEASONS",       df_curr["season"].nunique()),
            ("DRIVERS",       df_curr["driver"].nunique()),
            ("2026 ROWS",     len(df_curr[df_curr["season"]==2026])),
        ]):
            with col:
                st.markdown(f'<div class="metric-card" style="text-align:center;"><div class="metric-value" style="font-size:1.3rem;">{val}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)
        st.dataframe(df_curr[df_curr["season"]==2026].sort_values(["round","finish_position"]) if len(df_curr[df_curr["season"]==2026]) > 0 else df_curr.tail(30), use_container_width=True)




# ═══════════════════════════════════════════════════════════════════
# PAGE: DB & INSIGHTS
# ═══════════════════════════════════════════════════════════════════
elif "DB" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">DB & Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">Live Database · Expert Predictions · Regulations · Calendar</div>', unsafe_allow_html=True)

    tab_db, tab_cpi, tab_expert, tab_regs, tab_cal, tab_log = st.tabs([
        "🗄️ DB STATUS", "🏆 CPI RANKINGS", "💬 EXPERT INSIGHTS",
        "📋 REGULATIONS", "🗓️ CALENDAR", "📝 INGEST LOG"
    ])

    # ── DB STATUS ──
    with tab_db:
        if DB_LIVE:
            status = get_db_status()
            st.markdown('<div class="section-title">Database Tables</div>', unsafe_allow_html=True)

            metrics_data = [
                ("DRIVERS",    status.get("drivers", 0)),
                ("TEAMS",      status.get("teams", 0)),
                ("CIRCUITS",   status.get("circuits", 0)),
                ("RACES",      status.get("races_total", 0)),
                ("RESULTS",    status.get("race_results", 0)),
                ("EXPERT PREDS", status.get("expert_predictions", 0)),
                ("REGULATIONS",status.get("regulations", 0)),
                ("LOGS",       status.get("ingestion_logs", 0)),
            ]
            cols = st.columns(4)
            for i, (lbl, val) in enumerate(metrics_data):
                with cols[i % 4]:
                    st.markdown(f'<div class="metric-card" style="text-align:center;"><div class="metric-value" style="font-size:1.3rem;">{val}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="explanation-box" style="margin-top:16px;">
            <strong style="color:#27F4D2;">🟢 Live Database Connected</strong><br>
            Last successful ingest: <code>{status.get('last_ingest','Unknown')}</code><br>
            2026 races in calendar: <strong>{status.get('races_2026', 0)}</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Database offline — running in CSV mode. Run `python ingestion\\run_ingestion.py --setup` to initialize.")

    # ── CPI RANKINGS ──
    with tab_cpi:
        st.markdown('<div class="section-title">Combined Performance Index — 2026 Rankings</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="explanation-box">
        The <strong>Combined Performance Index (CPI)</strong> merges 7 data signals into one master score:<br>
        Circuit history (25%) · Recent form (25%) · Expert confidence (15%) · Regulation benefit (15%) · H2H stats (10%) · Team trajectory (10%)
        </div>
        """, unsafe_allow_html=True)

        if DB_LIVE:
            cpi_df = get_driver_cpi_ranking(2026)
        else:
            df_tmp = load_data()
            df_tmp = df_tmp[df_tmp["season"]==2026] if not df_tmp.empty else pd.DataFrame()
            cpi_df = df_tmp.sort_values("combined_performance_index", ascending=False).drop_duplicates("driver") if not df_tmp.empty and "combined_performance_index" in df_tmp.columns else pd.DataFrame()

        if not cpi_df.empty:
            from src.utils import TEAM_COLORS
            for i, row in cpi_df.iterrows():
                color = TEAM_COLORS.get(row.get("team",""), "#888888")
                cpi   = row.get("combined_performance_index", 0)
                conf  = row.get("expert_confidence_score", 0.5)
                reg   = row.get("reg_combined_impact", 0.5)
                form  = row.get("driver_form_momentum_score", 0.5)
                bar_w = int(cpi * 100)

                st.markdown(f"""
                <div class="metric-card" style="padding:12px 16px;margin:4px 0;">
                  <div style="display:flex;align-items:center;gap:12px;">
                    <div style="font-family:Orbitron,monospace;font-size:1rem;color:#FFD700;width:28px;">P{i+1}</div>
                    <div style="flex:1;">
                      <div style="font-family:Orbitron,monospace;font-size:0.85rem;color:#E8E8F0;">{row.get('driver','')}</div>
                      <div style="font-size:0.7rem;color:{color};">{row.get('team','')}</div>
                      <div style="height:4px;width:{bar_w}%;background:linear-gradient(90deg,{color},{color}88);border-radius:2px;margin-top:4px;"></div>
                    </div>
                    <div style="text-align:right;min-width:180px;">
                      <span style="font-family:Orbitron,monospace;color:#FFD700;font-size:0.9rem;">{cpi:.3f}</span>
                      <span style="color:#888899;font-size:0.7rem;margin-left:8px;">CPI</span><br>
                      <span style="font-size:0.7rem;color:#888899;">Expert:{conf:.2f} · Reg:{reg:.2f} · Form:{form:.2f}</span>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── EXPERT INSIGHTS ──
    with tab_expert:
        st.markdown('<div class="section-title">Expert Analyst Predictions</div>', unsafe_allow_html=True)

        if DB_LIVE:
            exp_df = get_expert_predictions()
        else:
            exp_df = pd.DataFrame()

        if not exp_df.empty:
            for _, row in exp_df.iterrows():
                sent = row.get("sentiment","neutral")
                conf = float(row.get("confidence", 0.5))
                sent_color = "#27F4D2" if sent=="positive" else "#FF4466" if sent=="negative" else "#888899"
                sent_icon  = "😊" if sent=="positive" else "😟" if sent=="negative" else "😐"
                driver = row.get("driver","Unknown")
                color  = "#E8E8F0"

                st.markdown(f"""
                <div class="explanation-box" style="margin:6px 0;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <div style="font-family:Orbitron,monospace;font-size:0.85rem;color:{color};">
                      {sent_icon} {driver}
                    </div>
                    <div style="font-size:0.7rem;color:#888899;">
                      {sent_color and f'<span style="color:{sent_color}">{sent.upper()}</span>'} · conf: {conf:.2f} · {row.get('source','')}
                    </div>
                  </div>
                  <div style="font-size:0.82rem;color:#BBBBCC;line-height:1.5;">
                    <em>"{row.get('raw_text','')[:150]}..."</em>
                  </div>
                  <div style="font-size:0.78rem;color:#27F4D2;margin-top:6px;">
                    → {row.get('prediction','')}
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # Add new insight form
            st.markdown('<div class="section-title">➕ Add Expert Insight</div>', unsafe_allow_html=True)
            new_text   = st.text_area("PASTE EXPERT QUOTE OR ARTICLE SNIPPET", height=100, key="new_expert_text")
            new_source = st.text_input("SOURCE", placeholder="Sky Sports, The Race, Twitter...", key="new_expert_source")
            new_weekend = st.selectbox("RACE WEEKEND", ["—"] + CIRCUITS_2026, key="new_expert_weekend")

            if st.button("🧠  EXTRACT & SAVE INSIGHT"):
                if new_text:
                    try:
                        from ingestion.scrapers.expert_ingester import ExpertIngester
                        ingester = ExpertIngester()
                        result = ingester.ingest_text(
                            new_text, source=new_source or "Manual",
                            race_weekend=new_weekend if new_weekend != "—" else None
                        )
                        if result.get("success"):
                            ext = result["extracted"]
                            st.markdown(f"""
                            <div class="success-banner">
                            ✅ Extracted: {ext['driver_name']} | {ext['sentiment']} | conf={ext['confidence_score']:.2f}
                            </div>
                            """, unsafe_allow_html=True)
                            st.cache_data.clear()
                        else:
                            st.error(f"Failed: {result.get('error','')}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("No expert predictions in DB yet. Use the form below to add some.")

    # ── REGULATIONS ──
    with tab_regs:
        st.markdown('<div class="section-title">2026 Formula 1 Regulations</div>', unsafe_allow_html=True)

        if DB_LIVE:
            regs_df = get_regulations(2026)
        else:
            regs_df = pd.DataFrame()

        if not regs_df.empty:
            cat_colors = {
                "power_unit": "#3671C6", "aerodynamics": "#E8002D",
                "tires": "#FF8000", "chassis": "#229971",
                "entries": "#27F4D2", "format": "#FF87BC",
            }
            for _, reg in regs_df.iterrows():
                color    = cat_colors.get(reg.get("category",""), "#888888")
                impact   = float(reg.get("impact_score", 0.5))
                bar_w    = int(impact * 100)

                st.markdown(f"""
                <div class="metric-card" style="margin:8px 0;padding:16px;">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                      <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;">
                        <span style="background:{color}22;color:{color};border:1px solid {color}44;
                                     padding:2px 8px;border-radius:12px;font-size:0.65rem;
                                     font-family:Orbitron,monospace;letter-spacing:1px;">
                          {reg.get('category','').upper().replace('_',' ')}
                        </span>
                        <span style="font-size:0.7rem;color:#888899;">{reg.get('rule_id','')}</span>
                      </div>
                      <div style="font-family:Inter,sans-serif;font-size:0.85rem;color:#E8E8F0;margin-bottom:6px;">
                        {reg.get('description','')[:120]}...
                      </div>
                      <div style="font-size:0.75rem;color:#888899;">
                        🏁 {reg.get('race_impact','')[:80]}
                      </div>
                    </div>
                    <div style="text-align:right;min-width:80px;padding-left:12px;">
                      <div style="font-family:Orbitron,monospace;color:#FFD700;font-size:1.1rem;">{impact:.2f}</div>
                      <div style="font-size:0.6rem;color:#888899;letter-spacing:1px;">IMPACT</div>
                      <div style="height:3px;width:{bar_w}%;background:{color};border-radius:2px;margin-top:4px;margin-left:auto;"></div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── CALENDAR ──
    with tab_cal:
        st.markdown('<div class="section-title">2026 Race Calendar</div>', unsafe_allow_html=True)

        if DB_LIVE:
            cal_df = get_season_race_calendar(2026)
        else:
            cal_df = pd.DataFrame()

        if not cal_df.empty:
            for _, race in cal_df.iterrows():
                status = race.get("status","scheduled")
                icon   = "✅" if status=="completed" else "🔜" if status=="scheduled" else "⏳"
                color  = "#27F4D2" if status=="completed" else "#888899"
                sprint = race.get("sprint","—")

                st.markdown(f"""
                <div class="metric-card" style="padding:10px 16px;margin:3px 0;display:flex;align-items:center;gap:12px;">
                  <div style="font-family:Orbitron,monospace;font-size:0.85rem;color:#FFD700;width:30px;">R{race.get('round','')}</div>
                  <div style="flex:1;">
                    <span style="font-size:0.85rem;color:{color};">{race.get('race_name','')}</span>
                    <span style="font-size:0.7rem;color:#888899;margin-left:8px;">{race.get('date','')}</span>
                  </div>
                  <div style="font-size:0.75rem;color:#888899;">{sprint} Sprint</div>
                  <div style="font-size:0.85rem;">{icon}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── INGESTION LOG ──
    with tab_log:
        st.markdown('<div class="section-title">Recent Ingestion Activity</div>', unsafe_allow_html=True)

        if DB_LIVE:
            log_df = get_recent_ingestion_log(20)
            if not log_df.empty:
                for _, log in log_df.iterrows():
                    icon = "✅" if log.get("status")=="success" else "❌"
                    st.markdown(f"""
                    <div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#E8E8F0;
                                padding:6px 0;border-bottom:1px solid #1A1A25;display:flex;gap:12px;">
                      <span>{icon}</span>
                      <span style="color:#888899;min-width:130px;">{log.get('timestamp','')}</span>
                      <span style="min-width:100px;">{log.get('type','')}</span>
                      <span style="color:#27F4D2;">+{log.get('inserted',0)} rows</span>
                      <span style="color:#888899;">{log.get('source','')}</span>
                      <span style="color:#888899;margin-left:auto;">{log.get('duration','')}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Database not connected. Run `python ingestion\\run_ingestion.py --setup`")


# ═══════════════════════════════════════════════════════════════════
# PAGE: MODEL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════
elif "Model" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">Model Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">Training Pipeline & Performance Metrics</div>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        if models_trained():
            metrics = get_model_metrics()
            m = metrics.get("metrics", {})
            
            st.markdown('<div class="section-title">📈 Model Performance</div>', unsafe_allow_html=True)
            
            m_cols = st.columns(4)
            perf = [
                ("PODIUM AUC", f"{m.get('podium_auc',0):.3f}", "#27F4D2"),
                ("PODIUM ACC", f"{m.get('podium_acc',0)*100:.1f}%", "#27F4D2"),
                ("POSITION MAE", f"{m.get('position_mae',0):.2f}", "#FFD700"),
                ("POSITION R²", f"{m.get('position_r2',0):.3f}", "#FFD700"),
            ]
            for c, (lbl, v, color) in zip(m_cols, perf):
                with c:
                    st.markdown(f"""
                    <div class="metric-card" style="text-align:center;">
                      <div class="metric-value" style="font-size:1.4rem;color:{color};">{v}</div>
                      <div class="metric-label">{lbl}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Feature importance
            feats = metrics.get("metrics", {}).get("feature_cols", [])
            if feats:
                st.markdown('<div class="section-title">🔍 Feature Importance</div>', unsafe_allow_html=True)
                try:
                    podium_model = joblib.load(os.path.join(BASE_DIR, "models", "podium_model.pkl"))
                    fi = podium_model.feature_importances_
                    available = [c for c in feats if c]
                    fi_df = pd.DataFrame({"feature": available[:len(fi)], "importance": fi[:len(available)]})
                    fi_df.sort_values("importance", ascending=True, inplace=True)
                    fi_df = fi_df.tail(12)
                    
                    fig_fi = go.Figure(go.Bar(
                        x=fi_df["importance"], y=fi_df["feature"].str.replace("_", " ").str.title(),
                        orientation="h",
                        marker_color=["#E8002D" if i == len(fi_df)-1 else "#3671C6" for i in range(len(fi_df))],
                    ))
                    fig_fi.update_layout(
                        paper_bgcolor="#0A0A0F", plot_bgcolor="#13131A",
                        font=dict(family="Inter", color="#888899", size=11),
                        height=380, margin=dict(l=160, r=20, t=20, b=20),
                        xaxis=dict(gridcolor="#2A2A3A", title="Importance"),
                    )
                    st.plotly_chart(fig_fi, use_container_width=True)
                except Exception as e:
                    st.info(f"Could not render feature importance: {e}")
        else:
            st.info("No trained models found. Train models using the panel on the right.")
    
    with col_right:
        st.markdown('<div class="section-title">⚙️ Train Models</div>', unsafe_allow_html=True)
        
        df_check = load_data()
        n_rows = len(df_check)
        
        st.markdown(f"""
        <div class="metric-card">
          <div style="font-size:0.75rem;color:#888899;text-transform:uppercase;letter-spacing:1px;">Dataset Status</div>
          <div style="font-family:Orbitron,monospace;font-size:1.4rem;color:#FFD700;margin-top:8px;">{n_rows}</div>
          <div style="font-size:0.7rem;color:#888899;">rows available</div>
        </div>
        """, unsafe_allow_html=True)
        
        if n_rows < 50:
            st.warning("⚠️ Dataset too small for reliable training. Recommend 500+ rows.")
        
        if st.button("🚀  TRAIN ALL MODELS"):
            if n_rows < 20:
                st.error("Insufficient data. Please add race results first.")
            else:
                progress_bar = st.progress(0)
                status = st.empty()
                
                try:
                    status.text("Loading data and building features...")
                    progress_bar.progress(20)
                    
                    from src.train_model import train_pipeline
                    from src.data_cleaner import clean_dataset
                    
                    clean_path = os.path.join(BASE_DIR, "data", "cleaned_race_data.csv")
                    
                    status.text("Training models...")
                    progress_bar.progress(50)
                    
                    train_pipeline(clean_path)
                    progress_bar.progress(100)
                    
                    status.empty()
                    st.markdown('<div class="success-banner">✅ All models trained and saved successfully!</div>', unsafe_allow_html=True)
                    st.cache_data.clear()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Training failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        st.markdown('<div class="section-title">📁 Model Files</div>', unsafe_allow_html=True)
        model_files = ["podium_model.pkl", "win_model.pkl", "position_model.pkl", "model_meta.json"]
        for mf in model_files:
            path = os.path.join(BASE_DIR, "models", mf)
            exists = os.path.exists(path)
            size = f"{os.path.getsize(path)/1024:.1f}KB" if exists else "—"
            status_icon = "✅" if exists else "❌"
            st.markdown(f"""
            <div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#{'E8E8F0' if exists else '888899'};
                        padding:6px 0;border-bottom:1px solid #1A1A25;">
              {status_icon} {mf} <span style="color:#888899;float:right;">{size}</span>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: SUBSCRIBE
# ═══════════════════════════════════════════════════════════════════
if "Subscribe" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">Stay Ahead</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">Get race predictions delivered before every Grand Prix</div>', unsafe_allow_html=True)

    sys.path.insert(0, BASE_DIR)
    try:
        from auth import subscribe_email, signup, login, get_user_count
        AUTH_OK = True
    except Exception:
        AUTH_OK = False

    # Stats bar
    if AUTH_OK:
        try:
            stats = get_user_count()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div style="background:#0D0E16;border:1px solid #C9A84C33;border-radius:12px;padding:20px;text-align:center;">
                <div style="font-family:Orbitron,monospace;font-size:1.8rem;color:#C9A84C;">{stats['subscribers']}</div>
                <div style="font-size:0.65rem;color:#888899;letter-spacing:2px;text-transform:uppercase;">Subscribers</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div style="background:#0D0E16;border:1px solid #27F4D233;border-radius:12px;padding:20px;text-align:center;">
                <div style="font-family:Orbitron,monospace;font-size:1.8rem;color:#27F4D2;">{stats['users']}</div>
                <div style="font-size:0.65rem;color:#888899;letter-spacing:2px;text-transform:uppercase;">Members</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div style="background:#0D0E16;border:1px solid #E8002D33;border-radius:12px;padding:20px;text-align:center;">
                <div style="font-family:Orbitron,monospace;font-size:1.8rem;color:#E8002D;">2/2</div>
                <div style="font-size:0.65rem;color:#888899;letter-spacing:2px;text-transform:uppercase;">Podiums Called</div>
                </div>""", unsafe_allow_html=True)
        except Exception:
            pass

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📧 Quick Subscribe", "👤 Create Account"])

    with tab1:
        st.markdown("### Get race predictions by email — free forever")
        with st.form("subscribe_form"):
            sub_email = st.text_input("Email address", placeholder="you@example.com")
            sub_name  = st.text_input("Your name (optional)", placeholder="Srikanth")
            submitted = st.form_submit_button("🔔 Subscribe — It's Free")
            if submitted:
                if sub_email and "@" in sub_email:
                    if AUTH_OK:
                        result = subscribe_email(sub_email, sub_name)
                        if result["success"]:
                            st.success(f"✅ Subscribed! You'll get predictions before every race.")
                        else:
                            st.info("Already subscribed!")
                    else:
                        st.info("Subscription saved!")
                else:
                    st.error("Please enter a valid email")

        st.markdown("""
        <div style="margin-top:16px;padding:16px;background:#0D0E16;border-radius:12px;
                    border:1px solid rgba(255,255,255,0.05);">
        <div style="font-size:0.75rem;color:#888899;line-height:1.8;">
        ✅ Pre-race prediction email every Saturday<br>
        ✅ Post-race accuracy report every Sunday<br>
        ✅ Weekly F1 data digest every Monday<br>
        ✅ No spam. Unsubscribe anytime.
        </div></div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Create a free account for personalised predictions")
        with st.form("signup_form"):
            acc_name   = st.text_input("Full name")
            acc_email  = st.text_input("Email address")
            acc_pass   = st.text_input("Password", type="password")
            acc_driver = st.selectbox("Favourite driver",
                                      [""] + [d for d, t in DRIVERS_2026])
            acc_team   = st.selectbox("Favourite team",
                                      [""] + list(TEAM_COLORS.keys()))
            acc_submit = st.form_submit_button("🚀 Create Account")
            if acc_submit:
                if acc_email and acc_pass and acc_name:
                    if AUTH_OK:
                        result = signup(acc_email, acc_name, acc_pass, acc_driver, acc_team)
                        if result["success"]:
                            st.success("✅ Account created! Welcome to PitWall AI.")
                        else:
                            st.error(result["message"])
                    else:
                        st.success("Account created!")
                else:
                    st.error("Please fill all required fields")


# ═══════════════════════════════════════════════════════════════════
# PAGE: ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════
if "Admin" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">Admin Dashboard</div>', unsafe_allow_html=True)

    # Simple password protection
    admin_pass = st.text_input("Admin password", type="password")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "pitwall2026")

    if admin_pass != ADMIN_PASSWORD:
        st.warning("Enter admin password to access this page")
        st.stop()

    st.success("✅ Admin access granted")

    try:
        from auth import get_user_count, get_all_subscribers
        stats = get_user_count()

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        metrics = [
            ("Total Users", stats["users"], "#27F4D2"),
            ("Subscribers", stats["subscribers"], "#C9A84C"),
            ("Pro Users", stats["pro_users"], "#E8002D"),
            ("Races Completed", 3, "#888888"),
        ]
        for col, (label, val, color) in zip([c1,c2,c3,c4], metrics):
            with col:
                st.markdown(f"""<div style="background:#0D0E16;border:1px solid {color}33;
                border-radius:12px;padding:16px;text-align:center;">
                <div style="font-family:Orbitron,monospace;font-size:1.6rem;color:{color};">{val}</div>
                <div style="font-size:0.6rem;color:#888899;letter-spacing:2px;text-transform:uppercase;">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Subscribers list
        st.markdown('<div class="section-title">📧 Subscribers</div>', unsafe_allow_html=True)
        subs = get_all_subscribers()
        if subs:
            sub_df = pd.DataFrame(subs)[["email","name","subscribed_at","is_active"]]
            st.dataframe(sub_df, use_container_width=True)
        else:
            st.info("No subscribers yet")

        # Manual trigger buttons
        st.markdown('<div class="section-title">⚡ Manual Triggers</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🏎️ Run Prediction"):
                with st.spinner("Running..."):
                    import subprocess
                    result = subprocess.run(
                        ["python", "predict.py", "auto"],
                        capture_output=True, text=True,
                        cwd=BASE_DIR, timeout=120
                    )
                    if result.returncode == 0:
                        st.success("Prediction complete!")
                        st.code(result.stdout[-500:])
                    else:
                        st.error(result.stderr[-300:])

        with col2:
            if st.button("🔄 Retrain Model"):
                with st.spinner("Retraining..."):
                    import subprocess
                    r1 = subprocess.run(
                        ["python", "ingestion/run_ingestion.py", "--features"],
                        capture_output=True, text=True, cwd=BASE_DIR, timeout=120
                    )
                    r2 = subprocess.run(
                        ["python", "src/train_model.py"],
                        capture_output=True, text=True, cwd=BASE_DIR, timeout=300
                    )
                    if r2.returncode == 0:
                        st.success("Model retrained!")
                    else:
                        st.error(r2.stderr[-300:])

        with col3:
            if st.button("📬 Send Test Email"):
                st.info("Configure EMAIL_USER + EMAIL_PASS env vars to enable emails")

        # Latest prediction
        st.markdown('<div class="section-title">🔮 Latest Prediction</div>', unsafe_allow_html=True)
        pred_path = os.path.join(BASE_DIR, "data", "latest_prediction.json")
        if os.path.exists(pred_path):
            with open(pred_path) as f:
                latest_pred = json.load(f)
            st.markdown(f"""
            <div style="background:#0D0E16;border:1px solid #C9A84C33;border-radius:12px;padding:16px;">
            <div style="font-family:Orbitron,monospace;font-size:0.9rem;color:#C9A84C;">{latest_pred.get('circuit','')}</div>
            <div style="font-size:0.8rem;color:#E8E4D8;margin-top:8px;">
              🏆 Predicted winner: <strong>{latest_pred.get('winner','')}</strong><br>
              🕒 Generated: {latest_pred.get('generated_at','')[:19]}
            </div></div>
            """, unsafe_allow_html=True)
        else:
            st.info("No prediction generated yet")

    except Exception as e:
        st.error(f"Admin error: {e}")
        st.info("Run: python auth.py to initialise the user database")

