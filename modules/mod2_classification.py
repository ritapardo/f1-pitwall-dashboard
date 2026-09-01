import streamlit as st
import pandas as pd
from utils.data_loader import load_session_results, render_driver_tag

def render(year, selected_race, session_type, session_options):
    st.title(f"Official Classification: {selected_race} {year}")
    
    try:
        with st.spinner("Fetching official results..."):
            results = load_session_results(year, selected_race, session_options[session_type])
            
        # 1. Use a native HTML <table> tag wrapped in a container with horizontal scroll (overflow-x: auto)
        # This ensures the table is fully responsive on mobile devices without overlapping text.
        html_content = """
        <div style="background-color: #111111; padding: 20px; border-radius: 10px; border: 1px solid #333; overflow-x: auto;">
            <table style="width: 100%; min-width: 800px; border-collapse: collapse; color: white; font-family: sans-serif;">
                <thead>
                    <tr style="border-bottom: 2px solid #555; font-size: 12px; color: #888; text-transform: uppercase;">
                        <th style="padding: 10px; text-align: center;">Pos</th>
                        <th style="padding: 10px; text-align: center;">No</th>
                        <th style="padding: 10px; text-align: left;">Driver</th>
                        <th style="padding: 10px; text-align: left;">Team</th>
                        <th style="padding: 10px; text-align: center;">Laps</th>
                        <th style="padding: 10px; text-align: right;">Time/Retired</th>
                        <th style="padding: 10px; text-align: right;">Pts</th>
                    </tr>
                </thead>
                <tbody>
        """

        for index, row in results.iterrows():
            # Handle non-finishers (NC - Not Classified)
            pos = str(int(row['Position'])) if pd.notnull(row['Position']) and row['Position'] > 0 else 'NC'
            no = str(row['DriverNumber'])
            
            # Construct driver's full name safely
            first_name = row.get('FirstName', '')
            last_name = row.get('LastName', row.get('Abbreviation', 'Unknown'))
            driver_name = f"{first_name} {last_name}".strip()
            
            team = str(row['TeamName'])
            color = str(row.get('TeamColor', 'FFFFFF'))
            
            # Generate the broadcast-style HTML tag for the driver
            driver_badge = render_driver_tag(driver_name, color)
            
            laps = str(int(row.get('Laps', 0))) if pd.notnull(row.get('Laps')) else '0'
            pts = str(int(row.get('Points', 0)))

            # Calculate time deltas or display DNF status
            time_str = str(row['Status'])
            if pos == '1' and pd.notnull(row['Time']):
                ts = row['Time'].total_seconds()
                h, m = divmod(ts, 3600)
                m, s = divmod(m, 60)
                time_str = f"{int(h)}:{int(m):02d}:{s:06.3f}" if h > 0 else f"{int(m)}:{s:06.3f}"
            elif row['Status'] == 'Finished' and pd.notnull(row['Time']):
                gap = row['Time'].total_seconds()
                time_str = f"+{gap:.3f}s"

            # 2. Add table rows (<tr>). 
            # The 'white-space: nowrap' property is crucial here to prevent text from breaking into multiple lines on small screens.
            html_content += f"""
                    <tr style="border-bottom: 1px solid #222;">
                        <td style="padding: 12px 10px; text-align: center; font-weight: bold; font-size: 16px;">{pos}</td>
                        <td style="padding: 12px 10px; text-align: center; font-size: 14px; color: #ccc;">{no}</td>
                        <td style="padding: 12px 10px; white-space: nowrap;">{driver_badge}</td>
                        <td style="padding: 12px 10px; color: #aaa; font-size: 14px; white-space: nowrap;">{team}</td>
                        <td style="padding: 12px 10px; text-align: center; font-size: 14px;">{laps}</td>
                        <td style="padding: 12px 10px; text-align: right; font-size: 14px; font-variant-numeric: tabular-nums; white-space: nowrap;">{time_str}</td>
                        <td style="padding: 12px 10px; text-align: right; font-weight: bold; font-size: 16px;">{pts}</td>
                    </tr>
            """
            
        html_content += """
                </tbody>
            </table>
        </div>
        """
        
        # Strip newlines to avoid Streamlit markdown rendering bugs
        clean_html = html_content.replace("\n", "")
        st.markdown(clean_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Failed to load official results. (Error: {e})")