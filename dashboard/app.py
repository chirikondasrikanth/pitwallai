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
    if DB_LIVE:
        df = load_race_data()
        if not df.empty:
            return df
    return load_clean_data()

@st.cache_data(ttl=120)
def get_summary(season):
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
         "📋  CRM Data Entry", "🗄️  DB & Insights", "⚙️  Model Management"],
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
            
            # ─── Podium Cards ───
            st.markdown('<div class="section-title">🏆 Predicted Podium</div>', unsafe_allow_html=True)
            p_cols = st.columns(3)
            medals = [("🥇", "p1-card", "P1"), ("🥈", "p2-card", "P2"), ("🥉", "p3-card", "P3")]
            
            for i, (medal, card_cls, label) in enumerate(medals):
                r = pred["top_10"][i]
                color = team_color_hex(r["team"])
                with p_cols[i]:
                    st.markdown(f"""
                    <div class="podium-card {card_cls}">
                        <div style="font-size:1.8rem;">{medal}</div>
                        <div class="driver-name">{r['driver'].split()[-1].upper()}</div>
                        <div style="font-size:0.75rem;color:#888899;margin-top:2px;">{r['driver'].split()[0]}</div>
                        <div style="margin-top:6px;">
                            <span class="team-badge" style="background:{color}22;color:{color};border:1px solid {color}44;">
                                {r['team']}
                            </span>
                        </div>
                        <div style="margin-top:10px;font-family:Orbitron,monospace;font-size:1.4rem;color:#FFD700;">
                            {r['win_prob']*100:.1f}<span style="font-size:0.6rem;color:#888899;">%</span>
                        </div>
                        <div style="font-size:0.65rem;color:#888899;letter-spacing:1px;">WIN PROBABILITY</div>
                        <div class="win-prob-bar" style="width:{min(r['win_prob']*500,100):.0f}%;"></div>
                    </div>
                    """, unsafe_allow_html=True)
            
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
                
                # Circuit info
                cinfo = get_circuit_info(circuit)
                st.markdown('<div class="section-title">🗺️ Circuit</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="metric-card">
                  <div style="font-size:0.75rem;color:#888899;text-transform:uppercase;letter-spacing:1px;">{circuit.replace(' Grand Prix','')}</div>
                  <div style="font-size:0.8rem;color:#E8E8F0;margin-top:8px;">🔄 {cinfo['laps']} laps</div>
                  <div style="font-size:0.8rem;color:#E8E8F0;">📏 {cinfo['distance_km']} km</div>
                  <div style="font-size:0.8rem;color:#E8E8F0;">🏟️ {cinfo['type']}</div>
                  <div style="font-size:0.8rem;color:#E8E8F0;">⚡ Overtaking: {cinfo['overtaking']}</div>
                </div>
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
                conf_level  = reasoning.get("confidence_level", "MEDIUM")
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

                a1, a2 = st.columns(2)
                for (icon, title, text, color, col) in [
                    ("📖", "Race Preview",    reasoning.get("race_preview",""),    "#3671C6", a1),
                    ("🏆", "Winner Analysis", reasoning.get("winner_reasoning",""),"#E8002D", a2),
                ]:
                    with col:
                        st.markdown(f"""
                        <div class="explanation-box" style="border-left-color:{color};min-height:90px;">
                          <div style="font-family:Orbitron,monospace;font-size:0.75rem;
                                      color:{color};margin-bottom:8px;letter-spacing:1px;">
                            {icon} {title.upper()}
                          </div>
                          <div style="font-family:Inter,sans-serif;font-size:0.85rem;
                                      color:#CCCCDD;line-height:1.6;">{text}</div>
                        </div>
                        """, unsafe_allow_html=True)

                b1, b2, b3 = st.columns(3)
                for (icon, title, text, color, col) in [
                    ("🔧", "Strategy",    reasoning.get("strategy_insight",""), "#229971", b1),
                    ("⚡", "Dark Horses", reasoning.get("dark_horses",""),      "#FF8000", b2),
                    ("⚠️", "Risk Factors",reasoning.get("risk_factors",""),     "#FF87BC", b3),
                ]:
                    with col:
                        st.markdown(f"""
                        <div class="explanation-box" style="border-left-color:{color};min-height:80px;">
                          <div style="font-family:Orbitron,monospace;font-size:0.7rem;
                                      color:{color};margin-bottom:6px;letter-spacing:1px;">
                            {icon} {title.upper()}
                          </div>
                          <div style="font-family:Inter,sans-serif;font-size:0.82rem;
                                      color:#CCCCDD;line-height:1.6;">{text}</div>
                        </div>
                        """, unsafe_allow_html=True)

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
                            <div class="explanation-box" style="border-left-color:{color};padding:10px 14px;margin:4px 0;">
                              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                                <span style="font-family:Orbitron,monospace;font-size:0.8rem;color:{color};">{driver}</span>
                                <span style="font-family:Orbitron,monospace;font-size:0.75rem;color:#FFD700;">P{rank}</span>
                              </div>
                              <div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#BBBBCC;line-height:1.5;">{summary}</div>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown('<div class="section-title">📸 Caption Generator</div>', unsafe_allow_html=True)
                platform = st.selectbox("PLATFORM", ["instagram", "twitter", "linkedin"], key="caption_platform")
                if st.button("✨  GENERATE CAPTION", key="gen_caption"):
                    with st.spinner("Writing caption..."):
                        try:
                            caption = reasoner.generate_race_preview_post(circuit=circuit, prediction=pred, weather=weather, platform=platform)
                            st.session_state["last_caption"] = caption
                        except Exception as e:
                            st.error(f"Caption failed: {e}")

                if st.session_state.get("last_caption"):
                    st.code(st.session_state["last_caption"], language=None)
                    st.caption("👆 Click copy icon top-right to copy")


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
# PAGE: CRM DATA ENTRY
# ═══════════════════════════════════════════════════════════════════
elif "CRM" in nav:
    st.markdown('<div class="pitwall-header" style="font-size:1.8rem;">CRM Data Entry</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header" style="margin-bottom:24px;">Insert Race Results & Update Dataset</div>', unsafe_allow_html=True)
    
    tab_manual, tab_csv = st.tabs(["MANUAL ENTRY", "CSV UPLOAD"])
    
    with tab_manual:
        st.markdown('<div class="section-title">Enter Race Result</div>', unsafe_allow_html=True)
        
        r1, r2, r3 = st.columns(3)
        with r1:
            form_season = st.number_input("SEASON", min_value=2020, max_value=2030, value=2026)
            form_round = st.number_input("ROUND", min_value=1, max_value=25, value=1)
            form_circuit = st.selectbox("CIRCUIT", CIRCUITS_2026)
        with r2:
            form_driver = st.selectbox("DRIVER", [d for d, t in DRIVERS_2026])
            form_team = st.selectbox("TEAM", VALID_TEAMS_2026)
            form_weather = st.selectbox("WEATHER", ["Dry", "Mixed", "Wet"])
        with r3:
            form_qual = st.number_input("QUALIFYING POSITION", min_value=1, max_value=20, value=1)
            form_finish = st.number_input("FINISH POSITION", min_value=1, max_value=20, value=1)
            form_strategy = st.selectbox("TIRE STRATEGY", ["1-Stop", "2-Stop", "3-Stop"])
        
        r4, r5 = st.columns(2)
        with r4:
            form_pits = st.number_input("PIT STOPS", min_value=0, max_value=5, value=2)
            form_incidents = st.number_input("INCIDENTS (0/1)", min_value=0, max_value=1, value=0)
        with r5:
            form_penalties = st.number_input("PENALTIES (0/1)", min_value=0, max_value=1, value=0)
            auto_retrain = st.checkbox("Auto-retrain models after insert", value=False)
        
        if st.button("➕  SUBMIT RACE RESULT"):
            data = {
                "season": form_season, "round": form_round,
                "circuit": form_circuit, "driver": form_driver, "team": form_team,
                "qualifying_position": form_qual, "finish_position": form_finish,
                "weather": form_weather, "tire_strategy": form_strategy,
                "pit_stops": form_pits, "incidents": form_incidents, "penalties": form_penalties,
            }
            result = ingest_single_result(data, auto_retrain=auto_retrain)
            if result["success"]:
                st.markdown(f'<div class="success-banner">✅ {result["message"]} | Dataset now has {result["rows"]} rows</div>', unsafe_allow_html=True)
                if auto_retrain:
                    st.markdown('<div class="success-banner">🔄 Models retrained successfully</div>', unsafe_allow_html=True)
                st.cache_data.clear()
            else:
                for err in result["errors"]:
                    st.markdown(f'<div class="error-banner">❌ {err}</div>', unsafe_allow_html=True)
    
    with tab_csv:
        st.markdown('<div class="section-title">Bulk CSV Upload</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="explanation-box">
        <strong>Expected columns:</strong> season, circuit, driver, team, qualifying_position, finish_position<br>
        <strong>Optional:</strong> round, weather, tire_strategy, pit_stops, incidents, penalties, points<br>
        The system auto-cleans messy data, normalizes column names, and handles missing values.
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("UPLOAD CSV FILE", type=["csv"])
        csv_retrain = st.checkbox("Auto-retrain models after upload", value=False)
        
        if uploaded_file and st.button("📤  INGEST CSV"):
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            result = ingest_race_csv(tmp_path, auto_retrain=csv_retrain)
            if result["success"]:
                st.markdown(f'<div class="success-banner">✅ {result["message"]} | Total rows: {result["total_rows"]}</div>', unsafe_allow_html=True)
                st.cache_data.clear()
            else:
                for err in result.get("errors", []):
                    st.markdown(f'<div class="error-banner">❌ {err}</div>', unsafe_allow_html=True)
        
        # Current dataset preview
        df_curr = load_data()
        if not df_curr.empty:
            st.markdown('<div class="section-title">Current Dataset</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:#888899;font-size:0.8rem;margin-bottom:8px;">{len(df_curr)} rows | {df_curr["season"].nunique()} seasons | {df_curr["driver"].nunique()} drivers</div>', unsafe_allow_html=True)
            st.dataframe(df_curr.tail(20), use_container_width=True)


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

    with tab_db:
        if DB_LIVE:
            status = get_db_status()
            st.markdown('<div class="section-title">Database Tables</div>', unsafe_allow_html=True)
            metrics_data = [
                ("DRIVERS",      status.get("drivers", 0)),
                ("TEAMS",        status.get("teams", 0)),
                ("CIRCUITS",     status.get("circuits", 0)),
                ("RACES",        status.get("races_total", 0)),
                ("RESULTS",      status.get("race_results", 0)),
                ("EXPERT PREDS", status.get("expert_predictions", 0)),
                ("REGULATIONS",  status.get("regulations", 0)),
                ("LOGS",         status.get("ingestion_logs", 0)),
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
            st.warning("⚠️ Database offline. Run: python ingestion\\run_ingestion.py --setup")

    with tab_cpi:
        st.markdown('<div class="section-title">Combined Performance Index — 2026 Rankings</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="explanation-box">
        The <strong>Combined Performance Index (CPI)</strong> merges 7 signals into one master score:<br>
        Circuit history (25%) · Recent form (25%) · Expert confidence (15%) · Regulation benefit (15%) · H2H stats (10%) · Team trajectory (10%)
        </div>
        """, unsafe_allow_html=True)

        if DB_LIVE:
            cpi_df = get_driver_cpi_ranking(2026)
        else:
            df_tmp = load_data()
            cpi_df = df_tmp[df_tmp["season"]==2026].sort_values("combined_performance_index", ascending=False).drop_duplicates("driver") if not df_tmp.empty and "combined_performance_index" in df_tmp.columns else pd.DataFrame()

        if not cpi_df.empty:
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

    with tab_expert:
        st.markdown('<div class="section-title">Expert Analyst Predictions</div>', unsafe_allow_html=True)
        exp_df = get_expert_predictions() if DB_LIVE else pd.DataFrame()

        if not exp_df.empty:
            for _, row in exp_df.iterrows():
                sent = row.get("sentiment","neutral")
                conf = float(row.get("confidence", 0.5))
                sent_color = "#27F4D2" if sent=="positive" else "#FF4466" if sent=="negative" else "#888899"
                sent_icon  = "😊" if sent=="positive" else "😟" if sent=="negative" else "😐"
                st.markdown(f"""
                <div class="explanation-box" style="margin:6px 0;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <div style="font-family:Orbitron,monospace;font-size:0.85rem;color:#E8E8F0;">{sent_icon} {row.get('driver','')}</div>
                    <div style="font-size:0.7rem;color:#888899;"><span style="color:{sent_color}">{sent.upper()}</span> · conf:{conf:.2f} · {row.get('source','')}</div>
                  </div>
                  <div style="font-size:0.82rem;color:#BBBBCC;"><em>"{row.get('raw_text','')[:150]}..."</em></div>
                  <div style="font-size:0.78rem;color:#27F4D2;margin-top:6px;">→ {row.get('prediction','')}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">➕ Add Expert Insight</div>', unsafe_allow_html=True)
        new_text    = st.text_area("PASTE EXPERT QUOTE", height=100, key="new_expert_text")
        new_source  = st.text_input("SOURCE", placeholder="Sky Sports, The Race...", key="new_expert_source")
        new_weekend = st.selectbox("RACE WEEKEND", ["—"] + CIRCUITS_2026, key="new_expert_weekend")
        if st.button("🧠  EXTRACT & SAVE"):
            if new_text:
                try:
                    from ingestion.scrapers.expert_ingester import ExpertIngester
                    ingester = ExpertIngester()
                    result = ingester.ingest_text(new_text, source=new_source or "Manual",
                                                   race_weekend=new_weekend if new_weekend != "—" else None)
                    if result.get("success"):
                        ext = result["extracted"]
                        st.markdown(f'<div class="success-banner">✅ Extracted: {ext["driver_name"]} | {ext["sentiment"]} | conf={ext["confidence_score"]:.2f}</div>', unsafe_allow_html=True)
                        st.cache_data.clear()
                    else:
                        st.error(f"Failed: {result.get('error','')}")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_regs:
        st.markdown('<div class="section-title">2026 Formula 1 Regulations</div>', unsafe_allow_html=True)
        regs_df = get_regulations(2026) if DB_LIVE else pd.DataFrame()
        if not regs_df.empty:
            cat_colors = {"power_unit":"#3671C6","aerodynamics":"#E8002D","tires":"#FF8000","chassis":"#229971","entries":"#27F4D2","format":"#FF87BC"}
            for _, reg in regs_df.iterrows():
                color  = cat_colors.get(reg.get("category",""), "#888888")
                impact = float(reg.get("impact_score", 0.5))
                bar_w  = int(impact * 100)
                st.markdown(f"""
                <div class="metric-card" style="margin:8px 0;padding:16px;">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                      <div style="margin-bottom:6px;">
                        <span style="background:{color}22;color:{color};border:1px solid {color}44;padding:2px 8px;border-radius:12px;font-size:0.65rem;font-family:Orbitron,monospace;">{reg.get('category','').upper().replace('_',' ')}</span>
                        <span style="font-size:0.7rem;color:#888899;margin-left:8px;">{reg.get('rule_id','')}</span>
                      </div>
                      <div style="font-size:0.85rem;color:#E8E8F0;margin-bottom:6px;">{reg.get('description','')[:120]}...</div>
                      <div style="font-size:0.75rem;color:#888899;">🏁 {reg.get('race_impact','')[:80]}</div>
                    </div>
                    <div style="text-align:right;min-width:80px;padding-left:12px;">
                      <div style="font-family:Orbitron,monospace;color:#FFD700;font-size:1.1rem;">{impact:.2f}</div>
                      <div style="font-size:0.6rem;color:#888899;">IMPACT</div>
                      <div style="height:3px;width:{bar_w}%;background:{color};border-radius:2px;margin-top:4px;margin-left:auto;"></div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    with tab_cal:
        st.markdown('<div class="section-title">2026 Race Calendar</div>', unsafe_allow_html=True)
        cal_df = get_season_race_calendar(2026) if DB_LIVE else pd.DataFrame()
        if not cal_df.empty:
            for _, race in cal_df.iterrows():
                status = race.get("status","scheduled")
                icon   = "✅" if status=="completed" else "🔜"
                color  = "#27F4D2" if status=="completed" else "#888899"
                st.markdown(f"""
                <div class="metric-card" style="padding:10px 16px;margin:3px 0;display:flex;align-items:center;gap:12px;">
                  <div style="font-family:Orbitron,monospace;font-size:0.85rem;color:#FFD700;width:30px;">R{race.get('round','')}</div>
                  <div style="flex:1;"><span style="font-size:0.85rem;color:{color};">{race.get('race_name','')}</span>
                  <span style="font-size:0.7rem;color:#888899;margin-left:8px;">{race.get('date','')}</span></div>
                  <div style="font-size:0.75rem;color:#888899;">{race.get('sprint','—')} Sprint</div>
                  <div>{icon}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab_log:
        st.markdown('<div class="section-title">Recent Ingestion Activity</div>', unsafe_allow_html=True)
        if DB_LIVE:
            log_df = get_recent_ingestion_log(20)
            if not log_df.empty:
                for _, log in log_df.iterrows():
                    icon = "✅" if log.get("status")=="success" else "❌"
                    st.markdown(f"""
                    <div style="font-size:0.8rem;color:#E8E8F0;padding:6px 0;border-bottom:1px solid #1A1A25;display:flex;gap:12px;">
                      <span>{icon}</span>
                      <span style="color:#888899;min-width:130px;">{log.get('timestamp','')}</span>
                      <span style="min-width:100px;">{log.get('type','')}</span>
                      <span style="color:#27F4D2;">+{log.get('inserted',0)}</span>
                      <span style="color:#888899;">{log.get('source','')}</span>
                      <span style="color:#888899;margin-left:auto;">{log.get('duration','')}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Database not connected.")

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
