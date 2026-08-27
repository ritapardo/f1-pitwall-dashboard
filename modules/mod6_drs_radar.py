import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_session_basic

def render(year, selected_race, session_type, session_options):
    st.title(f"DRS Train Radar: {selected_race} {year}")
    
    try:
        with st.status("Analyzing field intervals and DRS chains...", expanded=True) as status:
            session = load_session_basic(year, selected_race, session_options[session_type])
            laps = session.laps
            status.update(label="Interval analysis complete", state="complete", expanded=False)
            
        valid_laps = laps.dropna(subset=['Time', 'Position', 'LapNumber']).copy()
        valid_laps['Position'] = valid_laps['Position'].astype(int)
        
        max_race_lap = int(valid_laps['LapNumber'].max())
        
        st.markdown("### Race Lap Inspector")
        selected_lap = st.slider("Select Lap to Inspect Field Intervals", min_value=2, max_value=max_race_lap, value=min(15, max_race_lap))
        
        lap_data = valid_laps[valid_laps['LapNumber'] == selected_lap].sort_values(by='Position').copy()
        
        if len(lap_data) > 1:
            lap_data['Time_Sec'] = lap_data['Time'].dt.total_seconds()
            # P1 gets a 0.0 gap, everyone else gets the gap to the car ahead
            lap_data['Gap_Ahead'] = lap_data['Time_Sec'].diff().fillna(0.0)
            
            lap_data['In_DRS_Range'] = (lap_data['Gap_Ahead'] <= 1.000) & (lap_data['Position'] > 1)
            
            lap_data['Train_ID'] = 0
            lap_data['Is_Leader'] = False 
            
            current_train = 0
            in_train = False
            train_members = []
            
            drivers_list = lap_data.to_dict('records')
            for i in range(1, len(drivers_list)):
                if drivers_list[i]['In_DRS_Range']:
                    if not in_train:
                        train_members = [i - 1, i]
                        in_train = True
                    else:
                        train_members.append(i)
                else:
                    if in_train and len(train_members) >= 3:
                        current_train += 1
                        for idx in train_members:
                            drivers_list[idx]['Train_ID'] = current_train
                        drivers_list[train_members[0]]['Is_Leader'] = True 
                    in_train = False
                    train_members = []
                    
            if in_train and len(train_members) >= 3:
                current_train += 1
                for idx in train_members:
                    drivers_list[idx]['Train_ID'] = current_train
                drivers_list[train_members[0]]['Is_Leader'] = True
                    
            processed_lap_df = pd.DataFrame(drivers_list)
            
            active_trains = processed_lap_df['Train_ID'].nunique() - (1 if 0 in processed_lap_df['Train_ID'].values else 0)
            cars_in_trains = len(processed_lap_df[processed_lap_df['Train_ID'] > 0])
            
            c1, c2, c3 = st.columns(3)
            c1.metric(label="Total Cars on Track", value=str(len(processed_lap_df)))
            c2.metric(label="Active DRS Trains", value=str(active_trains))
            c3.metric(label="Cars Trapped in Trains", value=str(cars_in_trains))
            
            if active_trains > 0:
                train_info = []
                for t_id in range(1, current_train + 1):
                    t_drivers = processed_lap_df[processed_lap_df['Train_ID'] == t_id]['Driver'].tolist()
                    leader = t_drivers[0]
                    followers = ", ".join(t_drivers[1:])
                    train_info.append(f"Train {t_id} ({len(t_drivers)} cars): Leader {leader} defending against {followers}")
                
                details_text = "<br>".join(train_info)
                st.markdown(f"<div style='padding:15px;background-color:#332200;color:#FFCC00;border-radius:5px; border-left: 5px solid #FFCC00; margin-bottom: 20px;'><b>DRS Train Active:</b><br>{details_text}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='padding:15px;background-color:#003311;color:#00FF7F;border-radius:5px; border-left: 5px solid #00FF7F; margin-bottom: 20px;'><b>Clean Air:</b> No active DRS trains (chains of 3 or more cars) detected on this lap.</div>", unsafe_allow_html=True)
            
            processed_lap_df['Status'] = 'Clean Air (>1.0s)'
            processed_lap_df.loc[processed_lap_df['In_DRS_Range'], 'Status'] = 'DRS Range (<=1.0s)'
            processed_lap_df.loc[(processed_lap_df['Train_ID'] > 0) & (~processed_lap_df['Is_Leader']), 'Status'] = 'Trapped in DRS Train'
            processed_lap_df.loc[(processed_lap_df['Train_ID'] > 0) & (processed_lap_df['Is_Leader']), 'Status'] = 'Defending (Train Leader)'
            
            color_map = {
                'Defending (Train Leader)': '#FFCC00',
                'Trapped in DRS Train': '#FF3333',
                'DRS Range (<=1.0s)': '#00AEEF',
                'Clean Air (>1.0s)': '#555555'
            }
            
            processed_lap_df['Label'] = "P" + processed_lap_df['Position'].astype(str) + " - " + processed_lap_df['Driver']
            
            ordered_labels = processed_lap_df['Label'].tolist()
            
            fig = px.bar(
                processed_lap_df, 
                x="Gap_Ahead",
                y="Label",
                orientation='h',
                color="Status",
                color_discrete_map=color_map,
                category_orders={
                    "Label": ordered_labels,
                    "Status": ['Defending (Train Leader)', 'Trapped in DRS Train', 'DRS Range (<=1.0s)', 'Clean Air (>1.0s)']
                },
                title=f"Interval to Car Ahead - Lap {selected_lap}",
                labels={"Gap_Ahead": "Gap to Car Ahead (Seconds)", "Label": "Position & Driver"}
            )
            
            fig.add_vline(x=1.0, line_dash="dash", line_color="#00FF7F", annotation_text="1.0s Threshold")
            
            fig.update_layout(
                height=650, 
                plot_bgcolor='#111111',
                paper_bgcolor='#111111',
                font=dict(color='white'),
                yaxis=dict(showgrid=False, tickmode='linear'),
                xaxis=dict(showgrid=True, gridcolor='#333333', title="Gap (Seconds)", range=[0, 10.0]),
                legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, width="stretch")
            
        else:
            st.warning("Insufficient timing data available for this lap.")
            
    except Exception as e:
        st.markdown(f"<div style='padding:15px;background-color:#330000;color:#FF6666;border-radius:5px;'>Failed to load DRS radar data. (Error: {e})</div>", unsafe_allow_html=True)