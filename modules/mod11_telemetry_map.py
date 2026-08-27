import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.data_loader import load_session_telemetry, render_driver_tag

def render(year, selected_race, session_type, session_options):
    st.title(f"Telemetry Overlays: {selected_race} {year}")
    
    try:
        with st.status("Downloading heavy telemetry (GPS & Car Inputs)...", expanded=True) as status:
            session = load_session_telemetry(year, selected_race, session_options[session_type])
            laps = session.laps
            status.update(label="Telemetry engine ready", state="complete", expanded=False)
            
        available_drivers = laps['Driver'].dropna().unique()
        if len(available_drivers) == 0:
            st.warning("No telemetry available for this session.")
            return
            
        st.markdown("### Telemetry Configuration")
        # THIS IS THE NEW 3-COLUMN LAYOUT WITH THE ROTATION SLIDER
        col1, col2, col3 = st.columns(3)
        with col1:
            driver = st.selectbox("Select Driver", available_drivers)
        with col2:
            metric = st.selectbox("Select Telemetry Channel", ["Throttle (%)", "Brake (%)", "Speed (km/h)", "Gear"])
        with col3:
            rotation = st.slider("Rotate Map (Degrees)", 0, 360, 90, 90, help="Align the track with the official TV broadcast.")
            
        driver_laps = laps.pick_drivers(driver)
        fastest_lap = driver_laps.pick_fastest()
        
        if fastest_lap.empty or pd.isna(fastest_lap['LapTime']):
            st.warning("Could not find a valid fast lap for this driver.")
            return
        
        driver_info = session.get_driver(driver)
        team_color = str(fastest_lap.get('TeamColor', 'FFFFFF'))
        lap_time_str = str(fastest_lap['LapTime']).split('.')[0][-5:] + "." + str(fastest_lap['LapTime']).split('.')[1][:3]
        
        st.markdown(render_driver_tag(driver, team_color), unsafe_allow_html=True)
        st.write(f"**Fastest Lap:** {lap_time_str} (Lap {int(fastest_lap['LapNumber'])})")
        
        with st.spinner("Extracting GPS and mapping traces..."):
            telemetry = fastest_lap.get_telemetry()
            
        # 1. APPLY ROTATION MATRIX
        theta = np.radians(rotation)
        c, s = np.cos(theta), np.sin(theta)
        telemetry['X_rot'] = telemetry['X'] * c - telemetry['Y'] * s
        telemetry['Y_rot'] = telemetry['X'] * s + telemetry['Y'] * c
            
        col_map = {
            "Throttle (%)": "Throttle",
            "Brake (%)": "Brake",
            "Speed (km/h)": "Speed",
            "Gear": "nGear"
        }
        y_col = col_map[metric]
        
        if metric == "Speed (km/h)":
            color_scale = "Turbo"
        elif metric == "Gear":
            color_scale = "Viridis"
        else:
            color_scale = "Inferno"
            
        # 2. RENDER THE THICK CONTINUOUS MAP
        fig = px.scatter(
            telemetry,
            x="X_rot", 
            y="Y_rot",
            color=y_col,
            color_continuous_scale=color_scale,
            title=f"{driver} - {metric} Trace",
            labels={y_col: metric}
        )
        
        fig.update_traces(marker=dict(size=8, symbol='circle', line=dict(width=0)))
        
        layout_args = dict(
            plot_bgcolor='#0e0e0e', 
            paper_bgcolor='#0e0e0e', 
            font=dict(color='white'),
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_colorbar=dict(title=metric, orientation="v")
        )
        
        if metric == "Gear":
            layout_args["coloraxis_colorbar"]["dtick"] = 1
            
        fig.update_layout(**layout_args)
        fig.update_yaxes(visible=False, showgrid=False, scaleanchor="x", scaleratio=1)
        fig.update_xaxes(visible=False, showgrid=False)
        
        st.plotly_chart(fig, width="stretch")
        
    except Exception as e:
        st.error(f"Failed to generate telemetry map. (Error: {e})")