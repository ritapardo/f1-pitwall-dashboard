import streamlit as st
import plotly.express as px
from utils.data_loader import load_session_laps

def render(year, selected_race, session_type, session_options):
    st.title(f"Tire Degradation Monitor: {selected_race} {year}")
    
    try:
        with st.spinner("Connecting to FIA Servers...", expanded=True) as status:
            st.write("Downloading raw telemetry... (This may take a minute on the first run)")
            # Pull data using the clean utility function
            laps = load_session_laps(year, selected_race, session_options[session_type])
        
        # Clean data: drop in-laps and missing compounds
        clean_laps = laps.pick_quicklaps().dropna(subset=['LapTime', 'Compound'])
        clean_laps['Time_Seconds'] = clean_laps['LapTime'].dt.total_seconds()
        
        available_drivers = clean_laps['Driver'].unique()
        selected_drivers = st.multiselect("Select drivers to compare:", 
                                          available_drivers, 
                                          default=list(available_drivers)[:2] if len(available_drivers) > 1 else [])
        
        if selected_drivers:
            if len(selected_drivers) > 4:
                st.warning("For optimal visualization, we recommend comparing a maximum of 4 drivers at once.")
            
            # Data Science Controls
            st.markdown("### Telemetry Filtering")
            col1, col2 = st.columns(2)
            with col1:
                smoothing_window = st.slider("Pace Smoothing (Rolling Average)", min_value=1, max_value=5, value=1, help="Applies a rolling average to flatten sudden lap time spikes.")
            with col2:
                filter_outliers = st.toggle("Enable Outlier Filtering", value=True, help="Removes abnormal laps (e.g., traffic, minor lock-ups) using a 107% threshold rule.")
                
            filtered_data = clean_laps[clean_laps['Driver'].isin(selected_drivers)].copy()
            
            # Apply Outlier Filtering
            if filter_outliers and not filtered_data.empty:
                threshold = filtered_data['Time_Seconds'].min() * 1.07
                filtered_data = filtered_data[filtered_data['Time_Seconds'] <= threshold]
            
            # Create Stint IDs
            filtered_data['Driver_Stint'] = filtered_data['Driver'] + "-" + filtered_data['Stint'].astype(str)
            
            # Apply Pace Smoothing (Rolling Average)
            if smoothing_window > 1:
                # Sort chronologically to ensure accurate rolling calculations
                filtered_data = filtered_data.sort_values(by=['Driver', 'Stint', 'LapNumber'])
                filtered_data['Time_Seconds'] = filtered_data.groupby('Driver_Stint')['Time_Seconds'].transform(lambda x: x.rolling(window=smoothing_window, min_periods=1).mean())
            
            tire_colors = {'SOFT': '#FF3333', 'MEDIUM': '#FFFF00', 'HARD': '#FFFFFF', 'INTERMEDIATE': '#39B54A', 'WET': '#00AEEF'}
            
            fig = px.line(filtered_data, x="LapNumber", y="Time_Seconds", 
                          color="Compound", symbol="Driver", line_group="Driver_Stint",
                          color_discrete_map=tire_colors, markers=True,
                          hover_data=["Driver", "Compound", "TyreLife", "Stint"],
                          title="Lap Times and Tire Life")
            
            fig.update_traces(marker=dict(size=8, opacity=0.9, line=dict(width=2, color='DarkSlateGrey')))
            fig.update_layout(
                plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
                xaxis=dict(title="Lap Number", showgrid=False), 
                yaxis=dict(title="Lap Time (Seconds)", showgrid=True, gridcolor='#333333', autorange="reversed")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Failed to load race data. (Error: {e})")