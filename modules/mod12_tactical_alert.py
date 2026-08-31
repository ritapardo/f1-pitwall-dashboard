import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data_loader import load_session_laps, load_session_results, render_driver_tag

def render(year, selected_race, session_type, session_options):
    st.title(f"Flash Tactical Alert Engine: {selected_race} {year}")
    
    try:
        with st.spinner("Analyzing live pit windows, gaps & field compression...") as status:
            laps = load_session_laps(year, selected_race, session_options[session_type])
            results = load_session_results(year, selected_race, session_options[session_type])

        clean_laps = laps.dropna(subset=['LapTime', 'Compound', 'TyreLife']).copy()
        clean_laps['Time_Sec'] = clean_laps['LapTime'].dt.total_seconds()
        
        flying_laps = clean_laps[(clean_laps['PitInTime'].isnull()) & (clean_laps['PitOutTime'].isnull())]
        median_pace = flying_laps['Time_Sec'].median()
        
        in_laps = clean_laps[clean_laps['PitInTime'].notnull()]
        out_laps = clean_laps[clean_laps['PitOutTime'].notnull()]
        
        if not in_laps.empty and not out_laps.empty and pd.notna(median_pace):
            green_pit_loss = (in_laps['Time_Sec'].median() + out_laps['Time_Sec'].median()) - (2 * median_pace)
        else:
            green_pit_loss = 22.0
            
        if pd.isna(green_pit_loss) or green_pit_loss < 14.0 or green_pit_loss > 40.0:
            green_pit_loss = 22.0

        available_drivers = sorted(results['Abbreviation'].dropna().unique())
        if not available_drivers:
            st.warning("No classification data available to simulate live tactical scenarios.")
            return

        total_race_laps = int(clean_laps['LapNumber'].max()) if not clean_laps.empty else 50

        # TACTICAL INCIDENT CONTROL DESK
        st.markdown("### Incident Command Desk")
        c1, c2, c3 = st.columns(3)
        with c1:
            target_driver = st.selectbox("Target Driver", available_drivers, index=0)
            driver_info = results[results['Abbreviation'] == target_driver]
            driver_color = str(driver_info['TeamColor'].iloc[0]) if not driver_info.empty else "FFFFFF"
            st.markdown(render_driver_tag(target_driver, driver_color), unsafe_allow_html=True)
            
        with c2:
            incident_type = st.selectbox("Track Status Trigger", ["Full Safety Car (SC)", "Virtual Safety Car (VSC)", "Red Flag (RF)", "Local Yellow / Green Flag"])
            current_lap = st.slider("Incident Lap:", 1, total_race_laps, int(total_race_laps * 0.5))

        with c3:
            current_compound = st.selectbox("Current Tyre Compound", ["HARD", "MEDIUM", "SOFT"], index=1)
            tyre_age = st.slider("Current Stint Age (Laps):", 1, total_race_laps, 18)

        delta_multiplier = {
            "Full Safety Car (SC)": 0.50,
            "Virtual Safety Car (VSC)": 0.60,
            "Red Flag (RF)": 0.0,
            "Local Yellow / Green Flag": 1.0
        }[incident_type]

        effective_pit_loss = green_pit_loss * delta_multiplier
        laps_remaining = max(1, total_race_laps - current_lap)

        st.markdown("---")
        st.markdown("### Live Gap & Re-Entry Simulation")
        
        g1, g2 = st.columns(2)
        with g1:
            gap_behind = st.slider("Gap to Car Behind (Seconds):", 0.0, 35.0, 16.5, 0.5)
        with g2:
            target_new_compound = st.selectbox("Target New Compound for Pit:", ["SOFT", "MEDIUM", "HARD"], index=0)

        # ==========================================
        # NEW PERFECTED TACTICAL MATH LOGIC
        # ==========================================
        has_free_stop = gap_behind > effective_pit_loss
        position_deficit = effective_pit_loss - gap_behind
        
        # 1. Base Pace differences between compounds
        compound_base_adv = {"SOFT": 1.2, "MEDIUM": 0.5, "HARD": 0.0}[target_new_compound]
        current_base_adv = {"SOFT": 1.2, "MEDIUM": 0.5, "HARD": 0.0}[current_compound]
        compound_delta = compound_base_adv - current_base_adv
        
        # 2. Pace lost due to tire age (Degradation)
        tyre_deg_penalty = 0.06 if current_compound == "HARD" else (0.10 if current_compound == "MEDIUM" else 0.16)
        deg_recovery = tyre_age * tyre_deg_penalty
        
        # 3. Total pace advantage per lap on the new tire
        total_pace_advantage = deg_recovery + compound_delta
        net_gain_from_box = (total_pace_advantage * laps_remaining) - effective_pit_loss

        # VERDICT GENERATION
        if incident_type == "Red Flag (RF)":
            box_decision = "FREE TIRE CHANGE UNDER RED FLAG"
            verdict_color = "#00FF7F"
            box_reason = "FIA regulations allow free tyre changes during Red Flag stoppages in the pit lane without any time loss."
        elif has_free_stop:
            box_decision = "BOX, BOX — FREE PIT WINDOW"
            verdict_color = "#00FF7F"
            box_reason = f"Your gap to the car behind (+{gap_behind:.1f}s) is greater than the discounted pit delta (+{effective_pit_loss:.1f}s). You will retain track position on fresh tyres."
        elif net_gain_from_box > 0 and position_deficit > 0:
            recovery_laps = int(position_deficit / max(0.05, total_pace_advantage))
            if recovery_laps < laps_remaining:
                box_decision = "BOX, BOX — TIRE OFFSET ADVANTAGE"
                verdict_color = "#00FF7F"
                box_reason = f"You will concede track position (-{position_deficit:.1f}s), but your total fresh tyre pace advantage (+{total_pace_advantage:.1f}s/lap) will recover the position in approximately {recovery_laps} laps."
            else:
                box_decision = "STAY OUT — NOT ENOUGH LAPS TO RECOVER"
                verdict_color = "#FF3333"
                box_reason = f"Fresh tyres give you +{total_pace_advantage:.1f}s/lap, but you will lose {position_deficit:.1f}s in the pit lane. It would take {recovery_laps} laps to catch up, and only {laps_remaining} laps remain."
        else:
            box_decision = "STAY OUT — DEFEND POSITION"
            verdict_color = "#FF8800"
            box_reason = f"Your current tyres have enough life. Pitting costs {effective_pit_loss:.1f}s, and the new tyres will not generate enough pace to recover the time lost."

        # VERDICT BANNER
        st.markdown(
            f"""
            <div style="background-color: #1a1a1a; padding: 22px; border-radius: 8px; border-left: 8px solid {verdict_color}; margin-bottom: 20px;">
                <span style="font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1.5px; font-weight: bold;">Pit Wall Strategic Command</span>
                <div style="font-size: 28px; font-weight: bold; color: {verdict_color}; margin-top: 4px; margin-bottom: 8px;">{box_decision}</div>
                <div style="color: #e0e0e0; font-size: 15px; line-height: 1.5;">{box_reason}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        st.markdown("### Pit Delta Breakdown")
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Nominal Green Pit Delta", f"{green_pit_loss:.1f}s")
        col_b.metric(f"{incident_type} Effective Pit Loss", f"{effective_pit_loss:.1f}s", delta=f"-{green_pit_loss - effective_pit_loss:.1f}s Saved", delta_color="normal")
        col_c.metric("Buffer to Car Behind", f"{gap_behind - effective_pit_loss:+.1f}s")
        col_d.metric("Actual Fresh Tyre Delta", f"+{total_pace_advantage:.2f}s / lap")

        # POSITION RE-ENTRY WINDOW BAR
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=['Tactical Window'],
            x=[gap_behind],
            name='Gap to Chaser',
            orientation='h',
            marker=dict(color='#00AEEF')
        ))
        fig.add_trace(go.Bar(
            y=['Tactical Window'],
            x=[effective_pit_loss],
            name='Effective Pit Stop Loss',
            orientation='h',
            marker=dict(color='#FF3333' if not has_free_stop else '#00FF7F')
        ))
        
        fig.update_layout(
            barmode='group',
            plot_bgcolor='#111111',
            paper_bgcolor='#111111',
            font=dict(color='white'),
            title="Pit Stop Loss vs Defend Gap",
            xaxis=dict(title="Time (Seconds)", showgrid=True, gridcolor='#333333'),
            yaxis=dict(showgrid=False),
            height=240,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Tactical alert simulation failed. (Error: {e})")