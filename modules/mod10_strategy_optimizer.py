import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_session_laps

def render(year, selected_race, session_type, session_options):
    st.title(f"Dynamic Strategy Optimizer: {selected_race} {year}")
    
    try:
        with st.spinner("Analyzing track telemetry, degradation slopes & pit loss...") as status:
            laps = load_session_laps(year, selected_race, session_options[session_type])
            
        clean_laps = laps.dropna(subset=['LapTime', 'Compound', 'TyreLife']).copy()
        clean_laps['Time_Sec'] = clean_laps['LapTime'].dt.total_seconds()
        
        # 1. DYNAMIC CIRCUIT PIT LOSS CALCULATION
        flying_laps = clean_laps[(clean_laps['PitInTime'].isnull()) & (clean_laps['PitOutTime'].isnull())]
        median_flying_pace = flying_laps['Time_Sec'].median()
        
        in_laps = clean_laps[clean_laps['PitInTime'].notnull()]
        out_laps = clean_laps[clean_laps['PitOutTime'].notnull()]
        
        if not in_laps.empty and not out_laps.empty and pd.notna(median_flying_pace):
            calc_pit_loss = (in_laps['Time_Sec'].median() + out_laps['Time_Sec'].median()) - (2 * median_flying_pace)
        else:
            calc_pit_loss = 22.5
            
        if pd.isna(calc_pit_loss) or calc_pit_loss < 14.0 or calc_pit_loss > 42.0:
            calc_pit_loss = 22.5
            
        total_race_laps = int(clean_laps['LapNumber'].max())
        if total_race_laps < 20:
            st.warning("Insufficient completed laps in this session to build a multi-stint simulation.")
            return

        # 2. DYNAMIC COMPOUND PACE & DEGRADATION ESTIMATION
        compounds = ['SOFT', 'MEDIUM', 'HARD']
        base_pace = {}
        deg_rates = {}
        default_deg = {'SOFT': 0.110, 'MEDIUM': 0.075, 'HARD': 0.045}
        
        for comp in compounds:
            c_laps = flying_laps[flying_laps['Compound'] == comp]
            if len(c_laps) >= 8:
                base_pace[comp] = c_laps['Time_Sec'].quantile(0.20)
                slope, _ = np.polyfit(c_laps['TyreLife'], c_laps['Time_Sec'], 1)
                deg_rates[comp] = max(0.02, min(slope, 0.25))
            else:
                deg_rates[comp] = default_deg[comp]
                
        # Fill missing base paces relative to available data
        if 'MEDIUM' in base_pace:
            if 'SOFT' not in base_pace: base_pace['SOFT'] = base_pace['MEDIUM'] - 0.55
            if 'HARD' not in base_pace: base_pace['HARD'] = base_pace['MEDIUM'] + 0.65
        elif 'HARD' in base_pace:
            base_pace['MEDIUM'] = base_pace['HARD'] - 0.65
            base_pace['SOFT'] = base_pace['MEDIUM'] - 0.55
        elif 'SOFT' in base_pace:
            base_pace['MEDIUM'] = base_pace['SOFT'] + 0.55
            base_pace['HARD'] = base_pace['MEDIUM'] + 0.65
        else:
            base_pace = {'SOFT': median_flying_pace - 0.5, 'MEDIUM': median_flying_pace, 'HARD': median_flying_pace + 0.6}

        # 3. INTERACTIVE SIMULATION CONTROLS & SAFETY CAR TRIGGER
        st.markdown("### Circuit Parameters & Tactical Controls")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Green Flag Pit Delta", f"{calc_pit_loss:.2f}s")
        col2.metric("Soft Pace / Deg", f"{base_pace['SOFT']:.2f}s | +{deg_rates['SOFT']:.3f}s/l")
        col3.metric("Medium Pace / Deg", f"{base_pace['MEDIUM']:.2f}s | +{deg_rates['MEDIUM']:.3f}s/l")
        col4.metric("Hard Pace / Deg", f"{base_pace['HARD']:.2f}s | +{deg_rates['HARD']:.3f}s/l")

        with st.expander("Tactical Scenario & Safety Car Tuner", expanded=True):
            sc_col1, sc_col2 = st.columns(2)
            with sc_col1:
                enable_sc = st.toggle("Simulate Safety Car / VSC Window", value=False)
                sc_lap = st.slider("Safety Car Deployed on Lap:", min_value=5, max_value=total_race_laps - 5, value=int(total_race_laps * 0.45), disabled=not enable_sc)
            with sc_col2:
                deg_multiplier = st.slider("Track Degradation Multiplier", 0.5, 2.5, 1.0, 0.1, help="Higher values simulate hot track surface or high tyre wear.")
                adj_pit_loss = st.slider("Base Pit Loss (Seconds)", 14.0, 38.0, float(round(calc_pit_loss, 1)), 0.5)

        effective_deg = {k: v * deg_multiplier for k, v in deg_rates.items()}
        sc_pit_loss = adj_pit_loss * 0.55  # ~45% time savings under SC

        # 4. CANDIDATE STRATEGIES (1-Stop, 2-Stop, and 3-Stop)
        candidate_plans = [
            # 1-Stop
            ('1-Stop: M ➔ H', ['MEDIUM', 'HARD']),
            ('1-Stop: H ➔ M', ['HARD', 'MEDIUM']),
            ('1-Stop: S ➔ H', ['SOFT', 'HARD']),
            ('1-Stop: H ➔ S', ['HARD', 'SOFT']),
            ('1-Stop: S ➔ M', ['SOFT', 'MEDIUM']),
            ('1-Stop: M ➔ S', ['MEDIUM', 'SOFT']),
            # 2-Stop
            ('2-Stop: S ➔ M ➔ H', ['SOFT', 'MEDIUM', 'HARD']),
            ('2-Stop: M ➔ H ➔ M', ['MEDIUM', 'HARD', 'MEDIUM']),
            ('2-Stop: S ➔ H ➔ M', ['SOFT', 'HARD', 'MEDIUM']),
            ('2-Stop: M ➔ H ➔ H', ['MEDIUM', 'HARD', 'HARD']),
            ('2-Stop: S ➔ M ➔ M', ['SOFT', 'MEDIUM', 'MEDIUM']),
            ('2-Stop: S ➔ H ➔ H', ['SOFT', 'HARD', 'HARD']),
            ('2-Stop: M ➔ M ➔ H', ['MEDIUM', 'MEDIUM', 'HARD']),
            ('2-Stop: S ➔ M ➔ S', ['SOFT', 'MEDIUM', 'SOFT']),
            # 3-Stop (High Wear / Safety Car Chaos)
            ('3-Stop: S ➔ M ➔ M ➔ S', ['SOFT', 'MEDIUM', 'MEDIUM', 'SOFT']),
            ('3-Stop: S ➔ M ➔ H ➔ S', ['SOFT', 'MEDIUM', 'HARD', 'SOFT']),
            ('3-Stop: S ➔ H ➔ M ➔ S', ['SOFT', 'HARD', 'MEDIUM', 'SOFT']),
            ('3-Stop: M ➔ S ➔ M ➔ S', ['MEDIUM', 'SOFT', 'MEDIUM', 'SOFT']),
        ]

        max_life = {'SOFT': int(total_race_laps * 0.45), 'MEDIUM': int(total_race_laps * 0.60), 'HARD': int(total_race_laps * 0.80)}
        min_stint = 6
        evaluated_strategies = []

        def get_pit_cost(pit_lap):
            if enable_sc and abs(pit_lap - sc_lap) <= 2:
                return sc_pit_loss
            return adj_pit_loss

        for name, seq in candidate_plans:
            stops = len(seq) - 1
            
            if stops == 1:
                c1, c2 = seq
                best_time, best_split = float('inf'), None
                for l1 in range(min_stint, total_race_laps - min_stint + 1):
                    l2 = total_race_laps - l1
                    if l1 > max_life[c1] or l2 > max_life[c2]: continue
                    
                    p_loss = get_pit_cost(l1)
                    t1 = l1 * base_pace[c1] + effective_deg[c1] * (l1 * (l1 + 1) / 2)
                    t2 = l2 * base_pace[c2] + effective_deg[c2] * (l2 * (l2 + 1) / 2)
                    total_t = t1 + t2 + p_loss
                    
                    if total_t < best_time:
                        best_time = total_t
                        best_split = [l1, l2]
                        
                if best_split:
                    evaluated_strategies.append({'Name': name, 'Stops': '1-Stop', 'Sequence': seq, 'Stints': best_split, 'Total_Time': best_time, 'Pit_Laps': [best_split[0]]})
                    
            elif stops == 2:
                c1, c2, c3 = seq
                best_time, best_split = float('inf'), None
                for l1 in range(min_stint, total_race_laps - 2 * min_stint + 1):
                    if l1 > max_life[c1]: continue
                    for l2 in range(min_stint, total_race_laps - l1 - min_stint + 1):
                        l3 = total_race_laps - l1 - l2
                        if l2 > max_life[c2] or l3 > max_life[c3]: continue
                        
                        p_loss = get_pit_cost(l1) + get_pit_cost(l1 + l2)
                        t1 = l1 * base_pace[c1] + effective_deg[c1] * (l1 * (l1 + 1) / 2)
                        t2 = l2 * base_pace[c2] + effective_deg[c2] * (l2 * (l2 + 1) / 2)
                        t3 = l3 * base_pace[c3] + effective_deg[c3] * (l3 * (l3 + 1) / 2)
                        total_t = t1 + t2 + t3 + p_loss
                        
                        if total_t < best_time:
                            best_time = total_t
                            best_split = [l1, l2, l3]
                            
                if best_split:
                    evaluated_strategies.append({'Name': name, 'Stops': '2-Stop', 'Sequence': seq, 'Stints': best_split, 'Total_Time': best_time, 'Pit_Laps': [best_split[0], best_split[0] + best_split[1]]})
                    
            elif stops == 3:
                c1, c2, c3, c4 = seq
                best_time, best_split = float('inf'), None
                # Equal-ish stint approximation for 3-stops to maintain responsive execution
                target_l = total_race_laps // 4
                splits = [target_l, target_l, target_l, total_race_laps - (3 * target_l)]
                
                if all(s <= max_life[c] for s, c in zip(splits, seq)):
                    pit_laps = [splits[0], splits[0] + splits[1], splits[0] + splits[1] + splits[2]]
                    p_loss = sum(get_pit_cost(p) for p in pit_laps)
                    total_t = sum(l * base_pace[c] + effective_deg[c] * (l * (l + 1) / 2) for l, c in zip(splits, seq)) + p_loss
                    evaluated_strategies.append({'Name': name, 'Stops': '3-Stop', 'Sequence': seq, 'Stints': splits, 'Total_Time': total_t, 'Pit_Laps': pit_laps})

        if not evaluated_strategies:
            st.error("No valid strategy combinations met stint length criteria.")
            return

        # 5. SORT & RANK RESULTS
        strat_df = pd.DataFrame(evaluated_strategies).sort_values(by='Total_Time').reset_index(drop=True)
        optimal = strat_df.iloc[0]
        strat_df['Delta_To_Best'] = strat_df['Total_Time'] - optimal['Total_Time']

        # Banner with SC context
        sc_note = f" (Includes discounted pit stop during SC around Lap {sc_lap})" if enable_sc else ""
        pit_lap_desc = ", ".join([f"Lap {p}" for p in optimal['Pit_Laps']])
        st.markdown(
            f"<div style='padding:16px;background-color:#003311;color:#00FF7F;border-radius:6px;border-left:6px solid #00FF7F;margin-bottom:20px;'>"
            f"<b>Optimal Race Strategy:</b> <b>{optimal['Name']}</b>{sc_note}<br>"
            f"Planned Pit Stops at: <b>{pit_lap_desc}</b> (Stint lengths: {optimal['Stints']} laps). "
            f"Theoretical race duration: <b>{optimal['Total_Time']/60:.2f} minutes</b>."
            f"</div>", 
            unsafe_allow_html=True
        )

        # 6. STINT BREAKDOWN TIMELINE
        st.markdown("### Stint Breakdown & Pit Stop Windows")
        compound_colors = {'SOFT': '#FF3333', 'MEDIUM': '#FFE500', 'HARD': '#FFFFFF'}
        timeline_fig = go.Figure()

        display_strats = strat_df.head(7).iloc[::-1]

        for _, row in display_strats.iterrows():
            current_lap = 0
            for comp, length in zip(row['Sequence'], row['Stints']):
                timeline_fig.add_trace(go.Bar(
                    y=[row['Name']],
                    x=[length],
                    name=comp,
                    orientation='h',
                    marker=dict(color=compound_colors.get(comp, '#888888'), line=dict(color='#111111', width=2)),
                    customdata=[[comp, length, current_lap, current_lap + length]],
                    hovertemplate="<b>%{y}</b><br>Compound: %{customdata[0]}<br>Laps: %{customdata[1]} (Lap %{customdata[2]} ➔ %{customdata[3]})<extra></extra>",
                    showlegend=False
                ))
                current_lap += length

        if enable_sc:
            timeline_fig.add_vline(x=sc_lap, line_dash="dash", line_color="#FFE500", annotation_text=f"SC Lap {sc_lap}")

        timeline_fig.update_layout(
            barmode='stack', plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
            xaxis=dict(title="Race Lap Progress", range=[0, total_race_laps], showgrid=True, gridcolor='#333333'),
            yaxis=dict(showgrid=False), height=380, margin=dict(l=20, r=20, t=20, b=30)
        )
        st.plotly_chart(timeline_fig, use_container_width=True)

        # 7. STRATEGY COMPARISON DELTA CHART
        st.markdown("### Full Strategy Landscape Ranking")
        bar_fig = px.bar(
            strat_df, x="Delta_To_Best", y="Name", orientation='h', color="Stops",
            color_discrete_map={'1-Stop': '#00AEEF', '2-Stop': '#FF8800', '3-Stop': '#FF3333'},
            labels={"Delta_To_Best": "Delta to Optimal Strategy (Seconds)", "Name": "Strategy Permutation"},
            title=f"Theoretical Time Loss vs Optimal ({total_race_laps} Laps)"
        )
        bar_fig.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
            xaxis=dict(showgrid=True, gridcolor='#333333'), yaxis=dict(autorange="reversed", showgrid=False),
            legend=dict(title="Type", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(bar_fig, use_container_width=True)

    except Exception as e:
        st.error(f"Strategy optimization engine failed. (Error: {e})")