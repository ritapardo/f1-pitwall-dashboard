import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_session_telemetry

def render(year, selected_race, session_type, session_options):
    st.title(f"Micro-Sector Battles: {selected_race} {year}")
    
    try:
        with st.spinner("Downloading high-resolution GPS telemetry...") as status:
            session = load_session_telemetry(year, selected_race, session_options[session_type])
            laps = session.laps
            
        available_drivers = laps['Driver'].dropna().unique()
        
        col1, col2 = st.columns(2)
        with col1:
            driver_1 = st.selectbox("Driver 1 (Reference)", available_drivers, index=0)
        with col2:
            driver_2 = st.selectbox("Driver 2 (Comparator)", available_drivers, index=1 if len(available_drivers) > 1 else 0)
            
        if driver_1 and driver_2 and driver_1 != driver_2:
            d1_lap = laps.pick_drivers(driver_1).pick_fastest()
            d2_lap = laps.pick_drivers(driver_2).pick_fastest()
            
            if pd.isnull(d1_lap['LapTime']) or pd.isnull(d2_lap['LapTime']):
                st.warning("One or both drivers do not have a valid fastest lap recorded in this session.")
            else:
                d1_tel = d1_lap.get_telemetry()
                d2_tel = d2_lap.get_telemetry()
                
                num_minisectors = 250
                track_length = max(d1_tel['Distance'].max(), d2_tel['Distance'].max())
                sector_length = track_length / num_minisectors
                
                d1_tel['Minisector'] = (d1_tel['Distance'] // sector_length).astype(int)
                d2_tel['Minisector'] = (d2_tel['Distance'] // sector_length).astype(int)
                
                d1_speed = d1_tel.groupby('Minisector')['Speed'].mean().reset_index()
                d2_speed = d2_tel.groupby('Minisector')['Speed'].mean().reset_index()
                
                battle_df = pd.merge(d1_speed, d2_speed, on='Minisector', suffixes=(f'_{driver_1}', f'_{driver_2}'))
                
                def determine_faster_driver(row):
                    if row[f'Speed_{driver_1}'] > row[f'Speed_{driver_2}']:
                        return driver_1
                    return driver_2
                    
                battle_df['Faster_Driver'] = battle_df.apply(determine_faster_driver, axis=1)
                plot_data = pd.merge(d1_tel[['X', 'Y', 'Minisector']], battle_df[['Minisector', 'Faster_Driver']], on='Minisector')
                
                color_1 = f"#{session.get_driver(driver_1)['TeamColor']}"
                color_2 = f"#{session.get_driver(driver_2)['TeamColor']}"
                color_map = {driver_1: color_1, driver_2: color_2}
                
                fig = px.scatter(plot_data, x="X", y="Y", color="Faster_Driver",
                                 title=f"Track Dominance Map: {driver_1} vs {driver_2} (Fastest Laps)",
                                 color_discrete_map=color_map)
                
                fig.update_layout(
                    plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
                    xaxis=dict(showgrid=False, zeroline=False, visible=False),
                    yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
                    legend_title_text="Faster Driver"
                )
                
                fig.update_traces(marker=dict(size=12, opacity=1.0))
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("### Pace Matrix")
                d1_time = d1_lap['LapTime'].total_seconds()
                d2_time = d2_lap['LapTime'].total_seconds()
                delta = d2_time - d1_time
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric(label=f"{driver_1} Fastest Lap", value=f"{d1_time:.3f}s")
                col_b.metric(label=f"{driver_2} Fastest Lap", value=f"{d2_time:.3f}s")
                
                if delta > 0:
                    col_c.metric(label="Advantage", value=f"{driver_1} (-{delta:.3f}s)")
                else:
                    col_c.metric(label="Advantage", value=f"{driver_2} (-{abs(delta):.3f}s)")
                    
        else:
            st.markdown("<div style='padding:15px;background-color:#333333;color:#FFFFFF;border-radius:5px;'>Please select two different drivers to compare.</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px;'>Failed to load telemetry data. (Error: {e})</div>", unsafe_allow_html=True)