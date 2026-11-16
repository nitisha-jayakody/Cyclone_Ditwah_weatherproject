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
from ditwah_weather.config import LOCATIONS

# App Configuration
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

# ==========================================
# SIDEBAR (Persistent across all pages)
# ==========================================
st.sidebar.title("🌧️ Cyclone Ditwah")
st.sidebar.markdown("Explore the historical climate context of Sri Lanka's extreme weather.")

# The city toggle now controls the data globally for Page 1 and Page 2
cities = df['city'].unique().tolist()
default_idx = cities.index("Dankotuwa") if "Dankotuwa" in cities else 0
selected_city = st.sidebar.selectbox("📍 Select a Grid Point", cities, index=default_idx)

# Pre-filter the data for the selected city
city_df = df[df['city'] == selected_city].copy()


# ==========================================
# PAGE 1: Overview & Warming Trend
# ==========================================
def page_overview():
    st.title("Sri Lanka: Climate Context & Warming Trends")
    
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.subheader("Why these cities?")
        st.markdown("""
        * **Dankotuwa:** My family lives here, making this extreme weather analysis deeply personal.
        * **Negombo:** The main coastal city near my home. It bore the absolute brunt of Cyclone Ditwah's extreme rainfall.
        * **Colombo:** The commercial capital and most densely populated metropolitan area.
        * **Galle:** A major city in the deep south, highly exposed to the torrential rains of the southwestern monsoon.
        * **Nuwara Eliya & Kandy:** Central highlands. Nuwara Eliya is the coldest city, providing a high-altitude baseline.
        * **Trincomalee & Batticaloa:** East coast, historically the most vulnerable to Bay of Bengal cyclones.
        * **Ratnapura & Anuradhapura:** Representing the distinct wet (City of Gems) and dry (ancient reservoirs) zones.
        """)
    
    with col2:
        # Contextual Map of Sri Lanka
        coords = pd.DataFrame([{'City': loc.name, 'lat': loc.latitude, 'lon': loc.longitude} for loc in LOCATIONS])
        fig_map = px.scatter_map(
            coords, lat="lat", lon="lon", hover_name="City", zoom=5.5, center={"lat": 7.8, "lon": 80.7}
        )
        fig_map.update_traces(marker=dict(size=12, color='#d62728'))
        fig_map.update_layout(map_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0}, height=300)
        st.plotly_chart(fig_map, use_container_width=True)

    st.divider()
    
    st.subheader(f"The Shifting Baseline Climate: {selected_city}")
    st.info("**Main Finding:** All 10 analyzed grid points exhibit a highly statistically significant warming trend over the past 85 years.", icon="📈")
    
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


# ==========================================
# PAGE 2: Rainfall Extremes
# ==========================================
def page_extremes():
    st.title(f"Rainfall Extremes: {selected_city}")
    st.info("**Main Finding:** While the background climate is warming, Cyclone Ditwah was an unprecedented statistical outlier that broke all historical records.", icon="🚨")
    
    # Calculate stats based on sidebar selection
    event_rain = calculate_event_rainfall(city_df, start='2025-11-26', end='2025-11-30')
    percentile = calculate_historical_percentile(city_df, event_total=event_rain, window=5, month=11, first_year=1940, last_year=2024)
    hist_max = annual_max_window(city_df, window=5, month=11, first_year=1940, last_year=2024)
    rp = return_period(hist_max.values, event_rain)
    rp_str = "> 10,000 years" if rp > 10000 else f"~{int(round(rp, -1)):,} years"
    
    # Top Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Ditwah 5-Day Rainfall", f"{event_rain:.1f} mm")
    col2.metric("Historical Percentile", f"{percentile}%")
    col3.metric("Estimated Return Period", rp_str)
    
    st.divider()
    
    st.subheader("How unprecedented was the storm?")
    city_max_rain = hist_max.reset_index()
    fig_rain = px.bar(city_max_rain, x='year', y='precipitation_sum',
                      labels={'year': 'Year', 'precipitation_sum': '5-Day Rainfall (mm)'})
    fig_rain.update_traces(marker_color='#1f77b4', name='Historical Max', showlegend=True)
    fig_rain.add_trace(go.Bar(x=[2025], y=[event_rain], name='Cyclone Ditwah', marker_color='red'))
    fig_rain.update_layout(template='plotly_white', legend=dict(x=0.02, y=0.98))
    
    st.plotly_chart(fig_rain, use_container_width=True)
    
    with st.expander("📊 Statistical Note: How is the Return Period calculated?"):
        st.markdown("We use a **Generalized Extreme Value (GEV)** model. Instead of looking at average daily rain (the 'bell curve'), GEV isolates only the absolute worst 5-day storm of each year.")


# ==========================================
# PAGE 3: Cyclone Footprint
# ==========================================
def page_footprint():
    st.title("National Footprint of the Storm")
    st.info("**Main Finding:** Cyclone Ditwah made landfall on the western coast, devastating Negombo and Dankotuwa with nearly 500-600mm of rain in just 5 days, while the eastern coast remained relatively spared.", icon="🗺️")
    
    map_data = []
    for loc in LOCATIONS:
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


# ==========================================
# APP ROUTER
# ==========================================
# This acts just like the professor's multi-page setup, but keeps it cleanly in one file!
pg = st.navigation([
    st.Page(page_overview, title="Climate & Warming", icon="🌡️"),
    st.Page(page_extremes, title="Rain Extremes", icon="🌧️"),
    st.Page(page_footprint, title="Cyclone Footprint", icon="🗺️")
])

pg.run()