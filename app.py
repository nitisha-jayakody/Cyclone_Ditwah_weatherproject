import sys
from pathlib import Path

# Path fix MUST happen first
src_path = str(Path.cwd() / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ditwah_weather.io import load_all
from ditwah_weather.analysis import (
    add_anomalies, annual_anomaly, annual_max_window, 
    calculate_event_rainfall, calculate_historical_percentile, return_period
)
# Import LOCATIONS so we can build the map
from ditwah_weather.config import LOCATIONS

# Add an emoji to the page tab
st.set_page_config(page_title="Ditwah Weather Report", layout="wide", page_icon="🌧️")

@st.cache_data
def get_data():
    data_dir = Path.cwd() / "data"
    return load_all(data_dir)

try:
    df = get_data()
except FileNotFoundError:
    st.error("Data not found. Please run the download script first.")
    st.stop()

st.sidebar.title("🌧️ Cyclone Ditwah (2025)")
st.sidebar.markdown("Explore the historical climate context of Sri Lanka's extreme weather.")

cities = df['city'].unique().tolist()
default_idx = cities.index("Dankotuwa") if "Dankotuwa" in cities else 0
city = st.sidebar.selectbox("📍 Select a Grid Point", cities, index=default_idx)

city_df = df[df['city'] == city].copy()

st.title(f"Climate & Weather Extremes: {city}")

# --- Top-level metrics ---
event_rain = calculate_event_rainfall(city_df, start='2025-11-26', end='2025-11-30')
percentile = calculate_historical_percentile(city_df, event_total=event_rain, window=5, month=11, first_year=1940, last_year=2024)
hist_max = annual_max_window(city_df, window=5, month=11, first_year=1940, last_year=2024)
rp = return_period(hist_max.values, event_rain)
rp_str = "> 10,000 years" if rp > 10000 else f"~{int(round(rp, -1)):,} years"

col1, col2, col3 = st.columns(3)
col1.metric("Ditwah 5-Day Rainfall", f"{event_rain:.1f} mm")
col2.metric("Historical Percentile", f"{percentile}%")
col3.metric("Estimated Return Period", rp_str)

st.divider()

# --- Create Interactive Tabs ---
tab1, tab2, tab3 = st.tabs(["🗺️ Cyclone Footprint", "🌧️ Rain Extremes", "🌡️ Warming Trend"])

with tab1:
    st.subheader("National Footprint of the Storm")
    st.markdown("Where did Cyclone Ditwah hit the hardest?")
    
    # Calculate event rain for ALL cities just for the map
    map_data = []
    for loc in LOCATIONS:
        # Match the spelling from io.py (e.g. "Nuwara Eliya" -> "Nuwara_eliya")
        city_name_in_df = loc.name.lower().replace(" ", "_").capitalize()
        
        loc_df = df[df['city'] == city_name_in_df]
        loc_rain = calculate_event_rainfall(loc_df, start='2025-11-26', end='2025-11-30')
        map_data.append({'City': loc.name, 'lat': loc.latitude, 'lon': loc.longitude, 'Rain (mm)': loc_rain})
        
    map_df = pd.DataFrame(map_data)
    
    fig_map = px.scatter_map(
        map_df, lat="lat", lon="lon", size="Rain (mm)", color="Rain (mm)",
        hover_name="City", color_continuous_scale="Blues", zoom=6.5, center={"lat": 7.8, "lon": 80.7}
    )
    fig_map.update_layout(map_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

with tab2:
    st.subheader("How unprecedented was the storm?")
    
    dankotuwa_max_rain = hist_max.reset_index()
    fig_rain = px.bar(dankotuwa_max_rain, x='year', y='precipitation_sum',
                      labels={'year': 'Year', 'precipitation_sum': '5-Day Rainfall (mm)'})
    fig_rain.update_traces(marker_color='#1f77b4', name='Historical Max', showlegend=True)
    fig_rain.add_trace(go.Bar(x=[2025], y=[event_rain], name='Cyclone Ditwah', marker_color='red'))
    fig_rain.update_layout(template='plotly_white', legend=dict(x=0.02, y=0.98))
    
    st.plotly_chart(fig_rain, use_container_width=True)
    
    # Hide the complex stats in an expander box
    with st.expander("📊 Statistical Note: How is the Return Period calculated?"):
        st.markdown("We use a **Generalized Extreme Value (GEV)** model. Instead of looking at average daily rain (the 'bell curve'), GEV isolates only the absolute worst 5-day storm of each year. A return period of '10,000 years' means there is only a 0.01% chance of a storm this severe happening in any given year.")

with tab3:
    st.subheader("The Shifting Baseline Climate")
    
    df_anom = add_anomalies(city_df, base=(1961, 1990), var='temperature_2m_max')
    city_annual = annual_anomaly(df_anom).reset_index()
    city_annual['Rolling_10yr'] = city_annual['anomaly'].rolling(10, center=True).mean()
    
    fig_temp = px.bar(city_annual, x='year', y='anomaly', 
                      labels={'year': 'Year', 'anomaly': 'Temperature Anomaly (°C)'},
                      color='anomaly', color_continuous_scale='RdBu_r')
    fig_temp.add_trace(go.Scatter(x=city_annual['year'], y=city_annual['Rolling_10yr'],
                                  mode='lines', name='10-Year Trend', line=dict(color='black', width=3)))
    fig_temp.update_layout(template='plotly_white', coloraxis_showscale=False)
    
    st.plotly_chart(fig_temp, use_container_width=True)