import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_session_basic

def render(year, selected_race, session_type, session_options):
    st.title(f"Crossover Point Alert: {selected_race} {year}")
    
    try:
        with st.spinner("Scanning weather and tire compound data...", expanded=True) as status:
            session = load_session_basic(year, selected_race, session_options[session_type])
            laps = session.laps
            
        valid_laps = laps.dropna(subset=['LapTime', 'Compound']).copy()
        valid_laps = valid_laps[(valid_laps['PitInTime'].isnull()) & (valid_laps['PitOutTime'].isnull())]
        valid_laps['Time_Seconds'] = valid_laps['LapTime'].dt.total_seconds()
        
        slick_compounds = ['SOFT', 'MEDIUM', 'HARD']
        wet_compounds = ['INTERMEDIATE', 'WET']
        
        valid_laps['Tire_Type'] = valid_laps['Compound'].apply(
            lambda x: 'Slick (Dry)' if x in slick_compounds else ('Wet/Inter' if x in wet_compounds else 'Other')
        )
        valid_laps = valid_laps[valid_laps['Tire_Type'] != 'Other']

        if 'Slick (Dry)' in valid_laps['Tire_Type'].values and 'Wet/Inter' in valid_laps['Tire_Type'].values:
            
            pace_df = valid_laps.groupby(['LapNumber', 'Tire_Type'])['Time_Seconds'].median().reset_index()
            pivot_df = pace_df.pivot(index='LapNumber', columns='Tire_Type', values='Time_Seconds').reset_index()
            
            # Reduce interpolation limit to prevent long lines across missing data
            pivot_df['Slick (Dry)'] = pivot_df['Slick (Dry)'].interpolate(limit=1)
            pivot_df['Wet/Inter'] = pivot_df['Wet/Inter'].interpolate(limit=1)
            
            crossover_lap = None
            for i in range(1, len(pivot_df)):
                prev = pivot_df.iloc[i-1]
                curr = pivot_df.iloc[i]
                
                if pd.notnull(prev['Slick (Dry)']) and pd.notnull(prev['Wet/Inter']) and \
                   pd.notnull(curr['Slick (Dry)']) and pd.notnull(curr['Wet/Inter']):
                    
                    if (prev['Slick (Dry)'] > prev['Wet/Inter'] and curr['Slick (Dry)'] < curr['Wet/Inter']) or \
                       (prev['Slick (Dry)'] < prev['Wet/Inter'] and curr['Slick (Dry)'] > curr['Wet/Inter']):
                        crossover_lap = curr['LapNumber']
                        break
            
            if crossover_lap:
                st.markdown(f"<div style='padding:15px;background-color:#332200;color:#FFCC00;border-radius:5px; border-left: 5px solid #FFCC00; margin-bottom: 20px;'><b>Crossover Detected:</b> The pace intersection occurred at approximately <b>Lap {int(crossover_lap)}</b>. Pitting before this lap was a risk; pitting after this lap meant losing time.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='padding:15px;background-color:#333333;color:#FFFFFF;border-radius:5px; margin-bottom: 20px;'><b>Data Note:</b> Both tire types were used, but a clear mathematical intersection point was not established (likely due to a Safety Car or Red Flag during the transition).</div>", unsafe_allow_html=True)
                
            fig = px.line(pace_df, x="LapNumber", y="Time_Seconds", color="Tire_Type",
                          color_discrete_map={'Slick (Dry)': '#FF3333', 'Wet/Inter': '#00AEEF'},
                          markers=True, title="Grid Pace Analysis: Slicks vs. Wet/Inter Tires")
            
            if crossover_lap:
                fig.add_vline(x=crossover_lap, line_dash="dash", line_color="#FFCC00", annotation_text="Optimal Pit Window")
            
            # IMPROVEMENT: Calculate dynamic Y-axis bounds to crop out massive Safety Car anomalies
            fastest_time = pace_df['Time_Seconds'].min()
            slowest_visual_cutoff = fastest_time * 1.20  # Cap the view at 20% slower than the fastest lap
            
            fig.update_layout(
                plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
                xaxis=dict(title="Lap Number", showgrid=False),
                yaxis=dict(title="Median Lap Time (Seconds)", showgrid=True, gridcolor='#333333', range=[slowest_visual_cutoff, fastest_time]),
                legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.markdown("<div style='padding:15px;background-color:#003311;color:#00FF7F;border-radius:5px; border-left: 5px solid #00FF7F; margin-bottom: 20px;'><b>Stable Weather Session:</b> This session was run entirely on a single tire category. No wet/dry crossover occurred.</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px;'>Failed to process crossover data. (Error: {e})</div>", unsafe_allow_html=True)