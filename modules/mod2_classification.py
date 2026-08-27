import streamlit as st
import pandas as pd
from utils.data_loader import load_session_results, render_driver_tag

def render(year, selected_race, session_type, session_options):
    st.title(f"Official Classification: {selected_race} {year}")
    
    try:
        with st.status("Fetching official results...", expanded=True) as status:
            results = load_session_results(year, selected_race, session_options[session_type])
            status.update(label="Results loaded successfully", state="complete", expanded=False)
            
        html_content = """
        <div style="background-color: #111111; padding: 20px; border-radius: 10px; border: 1px solid #333;">
            <div style="display: flex; border-bottom: 2px solid #555; padding-bottom: 10px; margin-bottom: 10px; font-size: 12px; color: #888; text-transform: uppercase; font-weight: bold;">
                <div style="width: 10%; text-align: center;">Pos</div>
                <div style="width: 10%; text-align: center;">No</div>
                <div style="width: 25%;">Driver</div>
                <div style="width: 25%;">Team</div>
                <div style="width: 10%; text-align: center;">Laps</div>
                <div style="width: 10%; text-align: right;">Time/Retired</div>
                <div style="width: 10%; text-align: right; padding-right: 15px;">Pts</div>
            </div>
        """

        for index, row in results.iterrows():
            pos = str(int(row['Position'])) if pd.notnull(row['Position']) and row['Position'] > 0 else 'NC'
            no = str(row['DriverNumber'])
            
            first_name = row.get('FirstName', '')
            last_name = row.get('LastName', row.get('Abbreviation', 'Unknown'))
            driver_name = f"{first_name} {last_name}".strip()
            
            team = str(row['TeamName'])
            color = str(row.get('TeamColor', 'FFFFFF'))
            
            # GENERATE THE BROADCAST TAG
            driver_badge = render_driver_tag(driver_name, color)
            
            laps = str(int(row.get('Laps', 0))) if pd.notnull(row.get('Laps')) else '0'
            pts = str(int(row.get('Points', 0)))

            time_str = str(row['Status'])
            if pos == '1' and pd.notnull(row['Time']):
                ts = row['Time'].total_seconds()
                h, m = divmod(ts, 3600)
                m, s = divmod(m, 60)
                time_str = f"{int(h)}:{int(m):02d}:{s:06.3f}" if h > 0 else f"{int(m)}:{s:06.3f}"
            elif row['Status'] == 'Finished' and pd.notnull(row['Time']):
                gap = row['Time'].total_seconds()
                time_str = f"+{gap:.3f}s"

            html_content += f"""
            <div style="display: flex; border-bottom: 1px solid #222; padding: 12px 0; font-family: sans-serif; align-items: center;">
                <div style="width: 10%; text-align: center; font-weight: bold; font-size: 16px; color: white;">{pos}</div>
                <div style="width: 10%; text-align: center; font-size: 14px; color: #ccc;">{no}</div>
                
                <!-- INSERT BADGE HERE -->
                <div style="width: 25%; display: flex; align-items: center;">
                    {driver_badge}
                </div>
                
                <div style="width: 25%; color: #aaa; font-size: 14px;">{team}</div>
                <div style="width: 10%; text-align: center; font-size: 14px; color: white;">{laps}</div>
                <div style="width: 10%; text-align: right; font-size: 14px; color: white; font-variant-numeric: tabular-nums;">{time_str}</div>
                <div style="width: 10%; text-align: right; padding-right: 15px; font-weight: bold; font-size: 16px; color: white;">{pts}</div>
            </div>
            """
            
        html_content += "</div>"
        
        clean_html = html_content.replace("\n", "")
        st.markdown(clean_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Failed to load official results. (Error: {e})")