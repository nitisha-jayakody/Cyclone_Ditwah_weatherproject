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
raw_cities = df['city'].unique().tolist()
cities = [c.replace("_", " ").title() for c in raw_cities]

default_idx = cities.index("Dankotuwa") if "Dankotuwa" in cities else 0
selected_city = st.sidebar.selectbox("📍 Select a Grid Point", cities, index=default_idx)

# Pre-filter the data for the selected city (convert back to dataset format)
db_city = selected_city.replace(" ", "_").capitalize()
if db_city == "Nuwara_eliya": db_city = "Nuwara_eliya" # Specific case handler
city_df = df[df['city'] == db_city].copy()


# ==========================================
# PAGE 1: Overview & Warming Trend
# ==========================================
def page_overview():
    st.title("Sri Lanka: Climate Context & Warming Trends")
    
    # --- SECTION 1: Intro & Map ---
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
    
    # --- SECTION 2: Your Original Bar Chart (Linked to Sidebar) ---
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
    
    st.divider()

    # --- SECTION 3: The Interactive Heatmap Comparison Tool ---
    st.subheader("Warming Trend: Deep Dive City Comparison")
    st.markdown("Compare the monthly temperature anomalies between two cities. Use the slider to zoom in on a specific decade.")
    
    # FIX: Extract the year from the date column first!
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    
    # 1. Add the Year Range Slider
    min_year = int(df['year'].min())
    max_year = int(df['year'].max())
    
    # The slider returns a tuple (start_year, end_year)
    selected_years = st.slider(
        "Select Year Range:",
        min_value=min_year,
        max_value=max_year,
        value=(1990, max_year), # Default to showing the last ~35 years to start
        step=1
    )
    
    # Side-by-side dropdowns for comparison
    col_sel1, col_sel2 = st.columns(2)
    compare_city_1 = col_sel1.selectbox("Select First City", cities, index=cities.index("Nuwara_eliya") if "Nuwara_eliya" in cities else 0)
    compare_city_2 = col_sel2.selectbox("Select Second City", cities, index=cities.index("Trincomalee") if "Trincomalee" in cities else 1)
    
# Function to generate a monthly heatmap for a given city and year range
    def create_heatmap(city_name, year_range):
        # 1. Get the FULL data for the city first
        c_df = df[df['city'] == city_name].copy()
        c_df['date'] = pd.to_datetime(c_df['date'])
        
        # 2. Calculate anomalies using the FULL dataset so the 1961-1990 baseline exists
        anom_df = add_anomalies(c_df, base=(1961, 1990), var='temperature_2m_max')
        anom_df['month'] = anom_df['date'].dt.month
        
        # 3. NOW filter by the user's selected year range!
        anom_df = anom_df[(anom_df['year'] >= year_range[0]) & (anom_df['year'] <= year_range[1])]
        
        # Group by year and month to get the average monthly anomaly
        monthly_anom = anom_df.groupby(['year', 'month'])['anomaly'].mean().reset_index()
        
        # Pivot the data for the heatmap (Rows: Month, Columns: Year)
        pivot_df = monthly_anom.pivot(index='month', columns='year', values='anomaly')
        month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
        pivot_df.index = pivot_df.index.map(month_names)
        
        # Determine a strict color scale limit so both charts share the exact same scale
        max_val = max(abs(pivot_df.min().min()), abs(pivot_df.max().max()))
        if pd.isna(max_val): max_val = 2.0 # Fallback
        
        # Create Plotly Heatmap
        fig = px.imshow(pivot_df,
                        labels=dict(x="Year", y="Month", color="Anomaly (°C)"),
                        x=pivot_df.columns,
                        y=pivot_df.index,
                        color_continuous_scale='RdBu_r',
                        zmin=-max_val, 
                        zmax=max_val,  
                        aspect='auto')
                        
        # Move the X-axis (Years) to the top so it doesn't overlap tooltips
        fig.update_xaxes(side="top")
        fig.update_layout(template='plotly_white', margin=dict(t=50, b=20))
        return fig

    # Display the heatmaps side by side
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown(f"**{compare_city_1}**")
        st.plotly_chart(create_heatmap(compare_city_1, selected_years), use_container_width=True, key="heatmap_1")
    with col_chart2:
        st.markdown(f"**{compare_city_2}**")
        st.plotly_chart(create_heatmap(compare_city_2, selected_years), use_container_width=True, key="heatmap_2")

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