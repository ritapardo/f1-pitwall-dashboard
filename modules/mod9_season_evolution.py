import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import get_season_standings, render_driver_tag

def render(year, selected_race, session_type, session_options):
    st.title(f"Championship Season Evolution: {year}")
    
    try:
        with st.status("Compiling season and sprint data...", expanded=True) as status:
            df = get_season_standings(year)
            status.update(label="Season data loaded successfully", state="complete", expanded=False)
            
        if df.empty:
            st.warning("No completed race data found for this season.")
            return

        current_totals = df.groupby('Driver')['Cumulative_Points'].max().sort_values(ascending=False)
        top_5_drivers = current_totals.head(5).index.tolist()
        available_drivers = sorted(df['Driver'].unique())
        
        selected_drivers = st.multiselect(
            "Select Drivers to Track:", 
            available_drivers, 
            default=top_5_drivers if top_5_drivers else available_drivers[:5]
        )
        
        if selected_drivers:
            plot_df = df[df['Driver'].isin(selected_drivers)].copy()
            round_order = df[['Round', 'Race']].drop_duplicates().sort_values('Round')['Race'].tolist()
            
            color_map = {}
            for driver in selected_drivers:
                driver_rows = plot_df[plot_df['Driver'] == driver]
                if not driver_rows.empty:
                    hex_color = driver_rows['Color'].iloc[0]
                    color_map[driver] = f"#{hex_color}" if not hex_color.startswith('#') else hex_color
                else:
                    color_map[driver] = "#FFFFFF"

            st.markdown("### Drivers' Championship Trajectory")
            
            fig = px.line(
                plot_df, x="Race", y="Cumulative_Points", color="Driver", markers=True,
                color_discrete_map=color_map, category_orders={"Race": round_order},
                title=f"Cumulative Drivers' Championship Points — {year}",
                labels={"Cumulative_Points": "Total Points", "Race": "Grand Prix"}
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            fig.update_layout(
                plot_bgcolor='#111111', paper_bgcolor='#111111', font=dict(color='white'),
                xaxis=dict(showgrid=True, gridcolor='#333333', tickangle=45),
                yaxis=dict(showgrid=True, gridcolor='#333333', title="Cumulative Points"),
                legend=dict(title="Driver", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, width="stretch")
            
            # Driver Standings Summary Cards with Custom Tags
            st.markdown("### Current Standings (Selected Drivers)")
            latest_standings = plot_df.groupby('Driver').last().reset_index()
            latest_standings = latest_standings.sort_values(by='Cumulative_Points', ascending=False)
            
            cols = st.columns(min(len(selected_drivers), 5))
            for i, (_, row) in enumerate(latest_standings.iterrows()):
                col_idx = i % len(cols)
                driver_badge = render_driver_tag(row['Driver'], row['Color'])
                
                # Custom HTML replacing st.metric
                card_html = f"""
                <div style="margin-bottom: 15px;">
                    {driver_badge}
                    <div style="font-size: 32px; font-weight: bold; color: white; margin-top: -5px; padding-left: 5px;">
                        {int(row['Cumulative_Points'])} <span style="font-size: 16px; color: #888;">pts</span>
                    </div>
                </div>
                """
                cols[col_idx].markdown(card_html, unsafe_allow_html=True)
                
        else:
            st.info("Select at least one driver to view the trajectory.")

    except Exception as e:
        st.error(f"Failed to load season evolution data. (Error: {e})")