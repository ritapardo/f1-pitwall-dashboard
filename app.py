import importlib
import streamlit as st
import pandas as pd
from utils.data_loader import get_calendar

# 1. BASE CONFIGURATION
st.set_page_config(page_title="F1 Pit Wall", layout="wide")

st.markdown("""
    <style>
        /* Import F1-style font */
        @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap');
        
        /* Apply font to the whole app */
        html, body, [class*="css"]  {
            font-family: 'Titillium Web', sans-serif !important;
        }
        
        /* Hide the Streamlit footer */
        footer {visibility: hidden;}
        
        /* Hide the Deploy button and top menu, but KEEP the sidebar toggle visible */
        .stDeployButton {display: none;}
        #MainMenu {visibility: hidden;}
        header {background-color: transparent !important;}
        
        /* Tighten up the top padding so the dashboard fills the screen */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Style the Sidebar to look more like a dark-mode F1 terminal */
        [data-testid="stSidebar"] {
            background-color: #0e0e0e;
            border-right: 1px solid #333333;
        }
        
        /* Style the metric boxes (like the pit loss and pace boxes) */
        [data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #ffffff !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 14px !important;
            color: #aaaaaa !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
    </style>
""", unsafe_allow_html=True)

# 2. SIDEBAR: GLOBAL SETTINGS & MEMORY (DEMO MODE)
st.sidebar.title("Settings")
qp = st.query_params

# Year Selection (Demo Mode: Only 2026)
year = st.sidebar.selectbox("Select Year", [2024], index=0)
st.query_params["year"] = str(year)

# Race Selection (Demo Mode: Only cached races)
demo_races = ['Spanish Grand Prix', 'Dutch Grand Prix']
default_race = qp.get("race", demo_races[0])
race_index = demo_races.index(default_race) if default_race in demo_races else 0

selected_race = st.sidebar.selectbox("Grand Prix", demo_races, index=race_index)
st.query_params["race"] = selected_race

# Session Selection (Demo Mode: Forced to 'Race')
session_options = {'Race': 'Race'}
session_type = st.sidebar.selectbox("Session", ['Race'], index=0)
st.query_params["session"] = session_type


# 3. SIDEBAR: NAVIGATION ROUTER (Removed Season Evolution)
st.sidebar.markdown("---")
st.sidebar.title("Strategy Modules")

module_list = [
    "1. Tire Degradation Monitor",
    "2. Official Classification",
    "3. Undercut Radar",
    "4. Catch-Up Projection",
    "5. Micro-Sector Battles",
    "6. DRS Train Radar",
    "7. Crossover Point Alert",
    "8. Monte Carlo Oracle",
    "10. Strategy Optimizer",
    "11. Telemetry Overlays",
    "12. Tactical Alert Matrix" 
]

default_module = qp.get("module", module_list[0])
module_index = module_list.index(default_module) if default_module in module_list else 0

module = st.sidebar.radio("Navigation:", module_list, index=module_index)
st.query_params["module"] = module


# 4. MODULE EXECUTION (SPA ROUTING)
if module == "1. Tire Degradation Monitor":
    from modules import mod1_tire_deg
    importlib.reload(mod1_tire_deg)
    mod1_tire_deg.render(year, selected_race, session_type, session_options)

elif module == "2. Official Classification":
    from modules import mod2_classification
    importlib.reload(mod2_classification)
    mod2_classification.render(year, selected_race, session_type, session_options)

elif module == "3. Undercut Radar":
    from modules import mod3_undercut
    importlib.reload(mod3_undercut)
    mod3_undercut.render(year, selected_race, session_type, session_options)

elif module == "4. Catch-Up Projection":
    from modules import mod4_catchup
    importlib.reload(mod4_catchup)
    mod4_catchup.render(year, selected_race, session_type, session_options)

elif module == "5. Micro-Sector Battles":
    from modules import mod5_microsector
    importlib.reload(mod5_microsector)
    mod5_microsector.render(year, selected_race, session_type, session_options)

elif module == "6. DRS Train Radar":
    from modules import mod6_drs_radar
    importlib.reload(mod6_drs_radar)
    mod6_drs_radar.render(year, selected_race, session_type, session_options)

elif module == "7. Crossover Point Alert":
    from modules import mod7_crossover
    importlib.reload(mod7_crossover)
    mod7_crossover.render(year, selected_race, session_type, session_options)

elif module == "8. Monte Carlo Oracle":
    from modules import mod8_monte_carlo
    importlib.reload(mod8_monte_carlo)
    mod8_monte_carlo.render(year, selected_race, session_type, session_options)

elif module == "10. Strategy Optimizer":
    from modules import mod10_strategy_optimizer
    importlib.reload(mod10_strategy_optimizer)
    mod10_strategy_optimizer.render(year, selected_race, session_type, session_options)
    
elif module == "11. Telemetry Overlays":
    from modules import mod11_telemetry_map
    importlib.reload(mod11_telemetry_map)
    mod11_telemetry_map.render(year, selected_race, session_type, session_options)
    
elif module == "12. Tactical Alert Matrix":
    from modules import mod12_tactical_alert
    importlib.reload(mod12_tactical_alert)
    mod12_tactical_alert.render(year, selected_race, session_type, session_options)