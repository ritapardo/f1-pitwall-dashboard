import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_session_basic

def render(year, selected_race, session_type, session_options):
    st.title(f"Undercut Radar: {selected_race} {year}")
    
    try:
        with st.spinner("Calculating net time deltas...") as status:
            # We use load_session_basic here because we need TeamColors for the plot
            session = load_session_basic(year, selected_race, session_options[session_type])
            laps = session.laps
            
        available_drivers = laps['Driver'].dropna().unique()
        
        col1, col2 = st.columns(2)
        with col1:
            target_driver = st.selectbox("Select Target Driver (Defending)", available_drivers, index=0)
        with col2:
            chaser_driver = st.selectbox("Select Chaser Driver (Attacking)", available_drivers, index=1 if len(available_drivers) > 1 else 0)
            
        if target_driver and chaser_driver and target_driver != chaser_driver:
            
            target_laps = laps.pick_drivers(target_driver)[['LapNumber', 'Time', 'Stint', 'PitInTime', 'PitOutTime', 'LapTime']].dropna(subset=['Time'])
            chaser_laps = laps.pick_drivers(chaser_driver)[['LapNumber', 'Time', 'Stint', 'PitInTime', 'PitOutTime', 'LapTime']].dropna(subset=['Time'])
            
            battle_data = pd.merge(target_laps, chaser_laps, on='LapNumber', suffixes=('_Target', '_Chaser'))
            battle_data['Raw_Gap'] = (battle_data['Time_Chaser'] - battle_data['Time_Target']).dt.total_seconds()
            
            # Dynamic pit loss calculation
            normal_laps = laps[(laps['PitInTime'].isnull()) & (laps['PitOutTime'].isnull())]
            median_normal_pace = normal_laps['LapTime'].dt.total_seconds().median()
            
            in_lap_time = laps[laps['PitInTime'].notnull()]['LapTime'].dt.total_seconds().median()
            out_lap_time = laps[laps['PitOutTime'].notnull()]['LapTime'].dt.total_seconds().median()
            
            dynamic_pit_loss = (in_lap_time - median_normal_pace) + (out_lap_time - median_normal_pace)
            
            if pd.isna(dynamic_pit_loss) or dynamic_pit_loss < 10 or dynamic_pit_loss > 45:
                dynamic_pit_loss = 22.5
                
            battle_data['Pit_Diff'] = battle_data['Stint_Target'] - battle_data['Stint_Chaser']
            battle_data['Net_Gap'] = battle_data['Raw_Gap'] + (battle_data['Pit_Diff'] * dynamic_pit_loss)
            
            # Smooth out the 1-lap math distortions exactly on pit entry/exit laps
            battle_data['Smoothed_Net_Gap'] = battle_data['Net_Gap'].rolling(window=2, min_periods=1).mean()
            
            chaser_color = f"#{session.get_driver(chaser_driver)['TeamColor']}"
            
            fig = px.area(battle_data, x="LapNumber", y="Smoothed_Net_Gap",
                          title=f"Net Pace Advantage: {chaser_driver} chasing {target_driver}",
                          labels={"Smoothed_Net_Gap": "Net Gap (Seconds)", "LapNumber": "Lap Number"},
                          hover_data={"Raw_Gap": True, "Pit_Diff": True},
                          color_discrete_sequence=[chaser_color])
            
            fig.add_hline(y=0, line_dash="dash", line_color="white", annotation_text="Overtake Threshold")
            
            max_visual_gap = min(battle_data['Smoothed_Net_Gap'].max(), 25.0)
            min_visual_gap = max(battle_data['Smoothed_Net_Gap'].min(), -5.0)
            
            fig.update_layout(
                plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#333333', range=[max_visual_gap, min_visual_gap])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # STRATEGY INTELLIGENCE ENGINE
            target_stops = target_laps['Stint'].max() - 1
            chaser_stops = chaser_laps['Stint'].max() - 1
            min_gap = battle_data['Smoothed_Net_Gap'].min()
            
            if target_stops != chaser_stops:
                st.markdown(f"<div style='padding:15px;background-color:#332200;color:#FFCC00;border-radius:5px; border-left: 5px solid #FFCC00;'><b>Split Strategy Detected:</b> {target_driver} executed a {target_stops}-stop strategy, while {chaser_driver} executed a {chaser_stops}-stop strategy. Because they are on offset stints, the Net Gap fluctuates wildly based on tire age, meaning a traditional direct undercut metric does not apply here.</div>", unsafe_allow_html=True)
            elif min_gap < 0:
                st.markdown(f"<div style='padding:15px;background-color:#003311;color:#00FF7F;border-radius:5px; border-left: 5px solid #00FF7F;'><b>Undercut/Overtake Successful:</b> {chaser_driver} achieved a negative net gap against {target_driver} on the same strategy.</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px; border-left: 5px solid #FF6666;'><b>Defense Successful:</b> {chaser_driver} never overcame the net gap. Closest net distance: {min_gap:.2f}s.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='padding:15px;background-color:#333333;color:#FFFFFF;border-radius:5px;'>Please select two different drivers to compare.</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px;'>Failed to calculate undercut data. (Error: {e})</div>", unsafe_allow_html=True)