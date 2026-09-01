import fastf1
import pandas as pd
import streamlit as st
import os

if not os.path.exists("cache"):
    os.makedirs("cache")
fastf1.Cache.enable_cache("cache")

@st.cache_data(show_spinner=False)
def get_calendar(year):
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule['EventFormat'] != 'testing'].copy()
    return races

@st.cache_data(show_spinner=False)
def load_session_laps(year, event, session_id):
    session = fastf1.get_session(year, event, session_id)
    session.load(telemetry=False, weather=False, messages=False)
    return session.laps

@st.cache_data(show_spinner=False)
def load_session_results(year, event, session_id):
    session = fastf1.get_session(year, event, session_id)
    session.load(telemetry=False, weather=False, messages=False)
    return session.results


@st.cache_resource(show_spinner=False)
def load_session_basic(year, event, session_id):
    session = fastf1.get_session(year, event, session_id)
    session.load(telemetry=False, weather=False, messages=False)
    return session


@st.cache_resource(show_spinner=False)
def load_session_telemetry(year, event, session_id):
    session = fastf1.get_session(year, event, session_id)
    session.load(telemetry=True, weather=False, messages=False)
    return session

@st.cache_data(show_spinner=False)
def get_season_standings(year):
    schedule = get_calendar(year)
    
    # Filter completed events and sort chronologically
    past_events = schedule[
        (schedule['EventDate'] < pd.Timestamp.now()) & (schedule['RoundNumber'] > 0)
    ].sort_values(by='RoundNumber').copy()
    
    if past_events.empty:
        return pd.DataFrame()

    season_records = []
    
    for _, event in past_events.iterrows():
        round_num = event['RoundNumber']
        event_name = event['EventName']
        event_format = event['EventFormat']
        
        weekend_points = {}
        driver_meta = {}
        
        # Sprint points if applicable
        if event_format == 'sprint':
            try:
                sprint_sess = fastf1.get_session(year, round_num, 'S')
                sprint_sess.load(telemetry=False, weather=False, messages=False)
                for _, row in sprint_sess.results.iterrows():
                    abbr = row.get('Abbreviation')
                    if pd.notna(abbr):
                        pts = float(row.get('Points', 0) or 0)
                        weekend_points[abbr] = weekend_points.get(abbr, 0.0) + pts
                        if abbr not in driver_meta:
                            driver_meta[abbr] = {
                                'Team': row.get('TeamName', 'Unknown'),
                                'Color': str(row.get('TeamColor', 'FFFFFF') or 'FFFFFF')
                            }
            except Exception:
                pass

        # Grand Prix Race points
        try:
            race_sess = fastf1.get_session(year, round_num, 'R')
            race_sess.load(telemetry=False, weather=False, messages=False)
            for _, row in race_sess.results.iterrows():
                abbr = row.get('Abbreviation')
                if pd.notna(abbr):
                    pts = float(row.get('Points', 0) or 0)
                    weekend_points[abbr] = weekend_points.get(abbr, 0.0) + pts
                    driver_meta[abbr] = {
                        'Team': row.get('TeamName', 'Unknown'),
                        'Color': str(row.get('TeamColor', 'FFFFFF') or 'FFFFFF')
                    }
        except Exception:
            continue
            
        for driver, pts in weekend_points.items():
            meta = driver_meta.get(driver, {'Team': 'Unknown', 'Color': 'FFFFFF'})
            season_records.append({
                'Round': round_num,
                'Race': event_name,
                'Driver': driver,
                'Team': meta['Team'],
                'Color': meta['Color'],
                'Weekend_Points': pts
            })
            
    df = pd.DataFrame(season_records)
    
    if not df.empty:
        df = df.sort_values(by=['Driver', 'Round']).reset_index(drop=True)
        df['Cumulative_Points'] = df.groupby('Driver')['Weekend_Points'].cumsum()
        
    return df

def render_driver_tag(driver_name, team_color):
    """
    Generates a broadcast-style HTML tag for a driver.
    """
    color = f"#{team_color}" if not str(team_color).startswith('#') else team_color
    if color == "#nan" or color == "#":
        color = "#FFFFFF"
        
    html = f"""
    <div style="display: flex; align-items: center; background-color: #1e1e1e; padding: 6px 14px; border-radius: 4px; border: 1px solid #333333; width: fit-content; margin-bottom: 8px;">
        <div style="width: 8px; height: 20px; background-color: {color}; margin-right: 12px; border-radius: 2px;"></div>
        <span style="color: #ffffff; font-weight: 700; font-size: 18px; letter-spacing: 1.5px; text-transform: uppercase; white-space: nowrap;">{driver_name}</span>
    </div>
    """
    return html