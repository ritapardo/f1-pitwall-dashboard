import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_session_basic

def render(year, selected_race, session_type, session_options):
    st.title(f"Catch-Up Projection: {selected_race} {year}")
    
    try:
        with st.spinner("Analyzing lap pace trends...", expanded=True) as status:
            session = load_session_basic(year, selected_race, session_options[session_type])
            laps = session.laps
            
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
            
            if max_lap > 5:
                st.markdown("### Simulation Parameters")
                reference_lap = st.slider("Select Current Lap for Projection", min_value=5, max_value=max_lap, value=max_lap)
                
                t_past = target_laps[target_laps['LapNumber'] <= reference_lap]
                c_past = chaser_laps[chaser_laps['LapNumber'] <= reference_lap]
                
                t_time = t_past['Time'].iloc[-1].total_seconds()
                c_time = c_past['Time'].iloc[-1].total_seconds()
                current_gap = c_time - t_time
                
                if current_gap < 0:
                    st.markdown("<div style='padding:15px;background-color:#333333;color:#FFFFFF;border-radius:5px;'>The Chaser is already ahead of the Target at this lap. Swap the driver order to calculate the catch-up time.</div>", unsafe_allow_html=True)
                else:
                    t_pace = t_past.tail(3)['LapTime'].dt.total_seconds().mean()
                    c_pace = c_past.tail(3)['LapTime'].dt.total_seconds().mean()
                    pace_delta = t_pace - c_pace
                    
                    st.markdown("### Pace Analysis")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric(label="Current Gap", value=f"{current_gap:.3f}s")
                    m2.metric(label=f"{target_driver} Pace", value=f"{t_pace:.3f}s")
                    m3.metric(label=f"{chaser_driver} Pace", value=f"{c_pace:.3f}s")
                    m4.metric(label="Pace Delta", value=f"{pace_delta:.3f}s", delta=f"{pace_delta:.3f}s per lap")
                    
                    # 1. Calculate the Historical Trend (Last 10 laps)
                    hist_start = max(5, reference_lap - 10)
                    hist_t = t_past[t_past['LapNumber'] >= hist_start]
                    hist_c = c_past[c_past['LapNumber'] >= hist_start]
                    hist_battle = pd.merge(hist_t, hist_c, on='LapNumber', suffixes=('_Target', '_Chaser'))
                    hist_battle['Gap'] = (hist_battle['Time_Chaser'] - hist_battle['Time_Target']).dt.total_seconds()
                    
                    hist_df = hist_battle[['LapNumber', 'Gap']].copy()
                    hist_df['Trace'] = 'Actual (Last 10 Laps)'
                    
                    chaser_color = f"#{session.get_driver(chaser_driver)['TeamColor']}"
                    
                    if pace_delta > 0:
                        laps_to_catch = current_gap / pace_delta
                        catch_lap = int(reference_lap + laps_to_catch)
                        
                        if catch_lap > total_race_laps:
                            st.markdown(f"<div style='padding:15px;background-color:#332200;color:#FFCC00;border-radius:5px; border-left: 5px solid #FFCC00;'><b>Out of Laps:</b> The Chaser is catching up, but needs {laps_to_catch:.1f} laps to close the gap. The race will end at Lap {total_race_laps} before they can overtake.</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='padding:15px;background-color:#003311;color:#00FF7F;border-radius:5px; border-left: 5px solid #00FF7F;'><b>Projection:</b> The Chaser is {pace_delta:.3f}s per lap faster. They will intercept the Target in <b>{laps_to_catch:.1f} laps</b> (Approx. Lap {catch_lap}).</div>", unsafe_allow_html=True)

                        # 2. Project the gap, capped strictly at the Checkered Flag or Overtake
                        max_proj_lap = min(catch_lap, total_race_laps)
                        proj_laps = list(range(reference_lap, max_proj_lap + 1))
                        proj_gaps = [current_gap - (pace_delta * (l - reference_lap)) for l in proj_laps]
                        
                        proj_df = pd.DataFrame({'LapNumber': proj_laps, 'Gap': proj_gaps})
                        proj_df['Trace'] = 'Projected'
                        
                        plot_df = pd.concat([hist_df, proj_df])
                        
                    else:
                        st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px; border-left: 5px solid #FF6666;'><b>Projection:</b> The Chaser is slower by {abs(pace_delta):.3f}s per lap. They are losing ground and will not intercept the Target.</div>", unsafe_allow_html=True)
                        plot_df = hist_df # Only show history if they are falling behind

                    # Combine into a rich visual narrative
                    fig = px.line(plot_df, x='LapNumber', y='Gap', color='Trace', line_dash='Trace',
                                  title="Gap Convergence Forecast",
                                  color_discrete_map={'Actual (Last 10 Laps)': 'white', 'Projected': chaser_color},
                                  line_dash_map={'Actual (Last 10 Laps)': 'solid', 'Projected': 'dot'})
                                  
                    fig.update_traces(line=dict(width=3))
                    fig.add_hline(y=0, line_dash="solid", line_color="white", annotation_text="Overtake Threshold")
                    fig.add_vline(x=total_race_laps, line_dash="dash", line_color="#FF3333", annotation_text="Checkered Flag")

                    fig.update_layout(
                        plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
                        xaxis=dict(title="Lap Number", showgrid=False),
                        yaxis=dict(title="Gap (Seconds)", showgrid=True, gridcolor='#333333'),
                        legend=dict(title="")
                    )
                    st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("Not enough laps completed to calculate accurate pace projections. Please wait for lap 6.")
                
        else:
            st.markdown("<div style='padding:15px;background-color:#333333;color:#FFFFFF;border-radius:5px;'>Please select two different drivers to compare.</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px;'>Failed to calculate projection data. (Error: {e})</div>", unsafe_allow_html=True)