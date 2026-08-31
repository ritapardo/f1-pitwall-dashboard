import importlib
import streamlit as st
import pandas as pd
import time
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

# 2. SIDEBAR: GLOBAL SETTINGS & MEMORY
st.sidebar.title("Settings")
qp = st.query_params

# Year Selection with Memory
default_year = int(qp.get("year", 2024))
# Genera automáticamente la lista desde 2026 bajando hasta 2018
year_list = list(range(2018, 2027))[::-1]
year_index = year_list.index(default_year) if default_year in year_list else 0

year = st.sidebar.selectbox("Select Year", year_list, index=year_index)
st.query_params["year"] = str(year)

# Fetch Calendar & Race Selection with Memory
calendar_df = get_calendar(year)
race_names = calendar_df['EventName'].tolist()

default_race = qp.get("race", race_names[0])
race_index = race_names.index(default_race) if default_race in race_names else 0

selected_race = st.sidebar.selectbox("Grand Prix", race_names, index=race_index)
st.query_params["race"] = selected_race

# Validate Event Date
race_info = calendar_df[calendar_df['EventName'] == selected_race].iloc[0]
event_date = race_info['EventDate']

if event_date > pd.Timestamp.now():
    st.sidebar.warning(f"This event is scheduled for {event_date.strftime('%Y-%m-%d')}.")
    st.sidebar.warning(f"Notice: The {selected_race} {year} hasn't happened yet. No telemetry data is available.")
    st.stop()

# DYNAMIC Session Selection (Includes all Free Practices, Sprints, etc.)
session_options = {}
for i in range(1, 6):
    sess_name = race_info.get(f'Session{i}')
    if pd.notna(sess_name) and sess_name != 'None' and sess_name != '':
        session_options[sess_name] = sess_name

session_list = list(session_options.keys())
# Default to the final session of the weekend (usually the Race)
default_session = qp.get("session", session_list[-1] if session_list else "")
session_index = session_list.index(default_session) if default_session in session_list else (len(session_list) - 1)

session_type = st.sidebar.selectbox("Session", session_list, index=session_index)
st.query_params["session"] = session_type


# 3. SIDEBAR: NAVIGATION ROUTER (Now with Memory!)
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
    "9. Season Evolution",
    "10. Strategy Optimizer",
    "11. Telemetry Overlays",
    "12. Tactical Alert Matrix" 
]

default_module = qp.get("module", module_list[0])
module_index = module_list.index(default_module) if default_module in module_list else 0

module = st.sidebar.radio("Navigation:", module_list, index=module_index)
st.query_params["module"] = module


# 4. SIDEBAR: LIVE REFRESH CONTROLS
st.sidebar.markdown("---")
st.sidebar.title("Live Race Controls")
live_mode = st.sidebar.toggle("Enable Live Auto-Refresh")

if live_mode:
    refresh_rate = st.sidebar.slider("Refresh Interval (Seconds)", min_value=30, max_value=120, value=30, step=10)
    st.sidebar.warning(f"Live mode active. The dashboard will automatically update every {refresh_rate} seconds.")


# 5. MODULE EXECUTION (SPA ROUTING)

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

elif module == "9. Season Evolution":
    from modules import mod9_season_evolution
    importlib.reload(mod9_season_evolution)
    mod9_season_evolution.render(year, selected_race, session_type, session_options)
    
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

# 6. HYBRID REFRESH ENGINE
if live_mode:
    time.sleep(refresh_rate)
    st.rerun()