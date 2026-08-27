import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.data_loader import load_session_basic

def render(year, selected_race, session_type, session_options):
    st.title(f"Monte Carlo Oracle: {selected_race} {year}")
    
    try:
        with st.status("Initializing predictive engine...", expanded=True) as status:
            session = load_session_basic(year, selected_race, session_options[session_type])
            laps = session.laps
            status.update(label="Engine ready", state="complete", expanded=False)
            
        available_drivers = laps['Driver'].dropna().unique()
        total_race_laps = int(laps['LapNumber'].max())
        
        col1, col2 = st.columns(2)
        with col1:
            target_driver = st.selectbox("Target Driver (Defending)", available_drivers, index=0)
        with col2:
            chaser_driver = st.selectbox("Chaser Driver (Attacking)", available_drivers, index=1 if len(available_drivers) > 1 else 0)
            
        if target_driver and chaser_driver and target_driver != chaser_driver:
            target_laps = laps.pick_drivers(target_driver).dropna(subset=['LapTime'])
            chaser_laps = laps.pick_drivers(chaser_driver).dropna(subset=['LapTime'])
            
            max_lap = int(min(target_laps['LapNumber'].max(), chaser_laps['LapNumber'].max()))
            
            if max_lap > 10:
                st.markdown("### Simulation Parameters")
                reference_lap = st.slider("Select Current Lap to Begin Simulation", min_value=10, max_value=max_lap, value=max_lap)
                
                # Extract historical pace up to the reference lap
                t_past = target_laps[target_laps['LapNumber'] <= reference_lap]
                c_past = chaser_laps[chaser_laps['LapNumber'] <= reference_lap]
                
                t_time = t_past['Time'].iloc[-1].total_seconds()
                c_time = c_past['Time'].iloc[-1].total_seconds()
                current_gap = c_time - t_time
                
                if current_gap < 0:
                    st.warning("The Chaser is already ahead! Swap the drivers to simulate.")
                elif reference_lap >= total_race_laps:
                    st.warning("The race is already over at this lap.")
                else:
                    # Calculate mean and standard deviation of pace (using last 10 laps for recent form)
                    t_recent = t_past.tail(10)['LapTime'].dt.total_seconds()
                    c_recent = c_past.tail(10)['LapTime'].dt.total_seconds()
                    
                    t_mu, t_sigma = t_recent.mean(), t_recent.std()
                    c_mu, c_sigma = c_recent.mean(), c_recent.std()
                    
                    laps_remaining = total_race_laps - reference_lap
                    num_simulations = 1000
                    
                    # Run Monte Carlo Simulation
                    target_simulated_times = np.random.normal(t_mu, t_sigma, (num_simulations, laps_remaining)).sum(axis=1)
                    chaser_simulated_times = np.random.normal(c_mu, c_sigma, (num_simulations, laps_remaining)).sum(axis=1)
                    
                    # Add current gap to the chaser's required time
                    final_gaps = (chaser_simulated_times + current_gap) - target_simulated_times
                    
                    chaser_wins = np.sum(final_gaps < 0)
                    win_probability = (chaser_wins / num_simulations) * 100
                    
                    st.markdown("### Oracle Prediction Results")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Simulations Run", f"{num_simulations:,}")
                    c2.metric("Laps Simulated per Run", laps_remaining)
                    c3.metric(f"{chaser_driver} Overtake Probability", f"{win_probability:.1f}%")
                    
                    if win_probability > 50:
                        st.markdown(f"<div style='padding:15px;background-color:#003311;color:#00FF7F;border-radius:5px;'><b>High Probability:</b> The math favors {chaser_driver} to catch and pass {target_driver} by the checkered flag.</div>", unsafe_allow_html=True)
                    elif win_probability > 15:
                        st.markdown(f"<div style='padding:15px;background-color:#332200;color:#FFCC00;border-radius:5px;'><b>Toss Up:</b> {chaser_driver} has a fighting chance, but {target_driver} is favored to defend successfully.</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px;'><b>Low Probability:</b> It is highly unlikely {chaser_driver} possesses the pace to close the gap before the race ends.</div>", unsafe_allow_html=True)
                    
                    # Plot the distribution of simulated final gaps
                    gap_df = pd.DataFrame({'Final Net Gap (Seconds)': final_gaps})
                    
                    fig = px.histogram(gap_df, x='Final Net Gap (Seconds)', nbins=50,
                                       title="Distribution of Simulated Race Outcomes",
                                       color_discrete_sequence=['#00AEEF'])
                    
                    fig.add_vline(x=0, line_dash="dash", line_color="#FF3333", annotation_text="Overtake Threshold")
                    
                    fig.update_layout(
                        plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
                        xaxis=dict(showgrid=True, gridcolor='#333333'),
                        yaxis=dict(title="Number of Simulations", showgrid=True, gridcolor='#333333')
                    )
                    
                    st.plotly_chart(fig, width="stretch")
            else:
                st.warning("Not enough laps completed to build a reliable statistical model. Please select a later lap.")
        else:
             st.markdown("<div style='padding:15px;background-color:#333333;color:#FFFFFF;border-radius:5px;'>Please select two different drivers.</div>", unsafe_allow_html=True)
             
    except Exception as e:
        st.error(f"Oracle simulation failed. (Error: {e})")