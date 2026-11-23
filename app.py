"""Streamlit dashboard for the Cyclone Ditwah weather analysis."""

import sys
from pathlib import Path

# Path fix MUST happen before importing the local src/ package
src_path = str(Path.cwd() / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# pylint: disable=wrong-import-position
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ditwah_weather.analysis import (
    add_anomalies,
    annual_anomaly,
    annual_max_window,
    calculate_event_rainfall,
    calculate_historical_percentile,
    return_period,
)
from ditwah_weather.config import LOCATIONS
from ditwah_weather.io import load_all

# App Configuration
st.set_page_config(page_title="Ditwah Weather Report", layout="wide", page_icon="🌧️")


@st.cache_data
def get_data():
    """Load and cache all 10 Sri Lankan weather datasets."""
    data_dir = Path.cwd() / "data"
    return load_all(data_dir)


try:
    df = get_data()
except FileNotFoundError:
    st.error("Data not found. Please run `python scripts/download_weather_data.py` first.")
    st.stop()

# ==========================================
# SIDEBAR (Persistent across all pages)
# ==========================================
st.sidebar.title("🌧️ Cyclone Ditwah")
st.sidebar.markdown("Explore the historical climate context of Sri Lanka's extreme weather.")

cities = sorted(df["city"].unique().tolist())
default_idx = cities.index("Dankotuwa") if "Dankotuwa" in cities else 0
selected_city = st.sidebar.selectbox("📍 Select a Grid Point", cities, index=default_idx)

city_df = df[df["city"] == selected_city].copy()


# ==========================================
# PAGE 1: Overview & Warming Trend
# ==========================================
def page_overview():
    """Render the climate context, city overview, and warming trend comparisons."""
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
        coords = pd.DataFrame(
            [{"City": loc.name, "lat": loc.latitude, "lon": loc.longitude} for loc in LOCATIONS]
        )
        fig_map = px.scatter_map(
            coords,
            lat="lat",
            lon="lon",
            hover_name="City",
            zoom=5.5,
            center={"lat": 7.8, "lon": 80.7},
        )
        fig_map.update_traces(marker=dict(size=12, color="#d62728"))
        fig_map.update_layout(
            map_style="carto-positron", margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=300
        )
        st.plotly_chart(fig_map, use_container_width=True)

    st.divider()

    # --- SECTION 2: Annual Temperature Anomaly Bar Chart ---
    st.subheader(f"The Shifting Baseline Climate: {selected_city}")
    st.info(
        "**Main Finding:** All 10 analyzed grid points show a warming trend over the past 85 years "
        "(statistically significant at p < 0.05 in 9 out of 10 cities, with Kandy borderline at p = 0.08).",
        icon="📈",
    )

    df_anom = add_anomalies(city_df, base=(1961, 1990), var="temperature_2m_max")
    city_annual = annual_anomaly(df_anom).reset_index()
    city_annual["Rolling_10yr"] = city_annual["anomaly"].rolling(10, center=True).mean()

    fig_temp = px.bar(
        city_annual,
        x="year",
        y="anomaly",
        labels={"year": "Year", "anomaly": "Temperature Anomaly (°C)"},
        color="anomaly",
        color_continuous_scale="RdBu_r",
    )
    fig_temp.add_trace(
        go.Scatter(
            x=city_annual["year"],
            y=city_annual["Rolling_10yr"],
            mode="lines",
            name="10-Year Trend",
            line=dict(color="black", width=3),
        )
    )
    fig_temp.update_layout(template="plotly_white", coloraxis_showscale=False)
    st.plotly_chart(fig_temp, use_container_width=True)

    st.divider()

    # --- SECTION 3: Interactive Monthly Heatmap Comparison ---
    st.subheader("Warming Trend: Deep Dive City Comparison")
    st.markdown(
        "Compare the monthly temperature anomalies between two cities. "
        "Use the slider to zoom in on a specific period."
    )

    years = df["date"].dt.year
    min_year = int(years.min())
    max_year = int(years.max())

    selected_years = st.slider(
        "Select Year Range:",
        min_value=min_year,
        max_value=max_year,
        value=(1990, max_year),
        step=1,
    )

    col_sel1, col_sel2 = st.columns(2)
    compare_city_1 = col_sel1.selectbox(
        "Select First City",
        cities,
        index=cities.index("Nuwara Eliya") if "Nuwara Eliya" in cities else 0,
    )
    compare_city_2 = col_sel2.selectbox(
        "Select Second City",
        cities,
        index=cities.index("Trincomalee") if "Trincomalee" in cities else 1,
    )

    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
    }

    def build_monthly_pivot(city_name, year_range):
        """Compute monthly temperature anomalies on the full record, then slice years."""
        c_df = df[df["city"] == city_name].copy()
        anom_df = add_anomalies(c_df, base=(1961, 1990), var="temperature_2m_max")
        anom_df = anom_df[
            (anom_df["year"] >= year_range[0]) & (anom_df["year"] <= year_range[1])
        ]
        monthly = anom_df.groupby(["year", "month"])["anomaly"].mean().reset_index()
        pivot = monthly.pivot(index="month", columns="year", values="anomaly")
        pivot.index = pivot.index.map(month_names)
        return pivot

    pivot_1 = build_monthly_pivot(compare_city_1, selected_years)
    pivot_2 = build_monthly_pivot(compare_city_2, selected_years)

    # Share the exact same symmetric color scale across both cities
    shared_max = max(
        abs(pivot_1.min().min()),
        abs(pivot_1.max().max()),
        abs(pivot_2.min().min()),
        abs(pivot_2.max().max()),
    )
    if pd.isna(shared_max):
        shared_max = 2.0

    def plot_heatmap(pivot_df, zmax):
        fig = px.imshow(
            pivot_df,
            labels={"x": "Year", "y": "Month", "color": "Anomaly (°C)"},
            x=pivot_df.columns,
            y=pivot_df.index,
            color_continuous_scale="RdBu_r",
            zmin=-zmax,
            zmax=zmax,
            aspect="auto",
        )
        fig.update_xaxes(side="top")
        fig.update_layout(template="plotly_white", margin={"t": 50, "b": 20})
        return fig

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown(f"**{compare_city_1}**")
        st.plotly_chart(
            plot_heatmap(pivot_1, shared_max), use_container_width=True, key="heatmap_1"
        )
    with col_chart2:
        st.markdown(f"**{compare_city_2}**")
        st.plotly_chart(
            plot_heatmap(pivot_2, shared_max), use_container_width=True, key="heatmap_2"
        )


# ==========================================
# PAGE 2: Rainfall Extremes
# ==========================================
def page_extremes():
    """Render extreme rainfall metrics and historical November comparison."""
    st.title(f"Rainfall Extremes: {selected_city}")
    st.info(
        "**Main Finding:** While the background climate is warming, Cyclone Ditwah was an "
        "extreme statistical outlier—breaking all 85-year November rainfall records in 6 of the 10 grid points.",
        icon="🚨",
    )

    event_rain = calculate_event_rainfall(city_df, start="2025-11-26", end="2025-11-30")
    percentile = calculate_historical_percentile(
        city_df, event_total=event_rain, window=5, month=11, first_year=1940, last_year=2024
    )
    hist_max = annual_max_window(
        city_df, window=5, month=11, first_year=1940, last_year=2024
    )
    rp = return_period(hist_max.values, event_rain)
    rp_str = "> 10,000 years" if rp > 10000 else f"~{int(round(rp, -1)):,} years"

    col1, col2, col3 = st.columns(3)
    col1.metric("Ditwah 5-Day Rainfall", f"{event_rain:.1f} mm")
    col2.metric("Historical Percentile", f"{percentile}%")
    col3.metric("Estimated Return Period", rp_str)

    st.divider()

    st.subheader("How unprecedented was the storm?")
    city_max_rain = hist_max.reset_index()
    fig_rain = px.bar(
        city_max_rain,
        x="year",
        y="precipitation_sum",
        labels={"year": "Year", "precipitation_sum": "5-Day Rainfall (mm)"},
    )
    fig_rain.update_traces(marker_color="#1f77b4", name="Historical Max", showlegend=True)
    fig_rain.add_trace(
        go.Bar(x=[2025], y=[event_rain], name="Cyclone Ditwah", marker_color="red")
    )
    fig_rain.update_layout(template="plotly_white", legend={"x": 0.02, "y": 0.98})
    st.plotly_chart(fig_rain, use_container_width=True)

    with st.expander("📊 Statistical Note: How is the Return Period calculated?"):
        st.markdown(
            "We fit a **Generalized Extreme Value (GEV)** distribution to the annual maximum "
            "5-day November rainfall from 1940 to 2024 (85 independent block maxima). "
            "Because 85 years is a short sample for an unprecedented event, return periods "
            "should be interpreted as an order of magnitude rather than an exact forecast."
        )


# ==========================================
# PAGE 3: Cyclone Footprint
# ==========================================
def page_footprint():
    """Render the interactive spatial map of Cyclone Ditwah across all 10 locations."""
    st.title("National Footprint of the Storm")
    st.info(
        "**Main Finding:** Cyclone Ditwah dumped 480–570 mm of rain in 5 days across the west "
        "and north-central regions (Negombo, Anuradhapura, and Dankotuwa), while southern and "
        "southeastern coastal areas (Galle and Batticaloa) recorded lower totals.",
        icon="🗺️",
    )

    map_data = []
    for loc in LOCATIONS:
        loc_df = df[df["city"] == loc.name]
        loc_rain = calculate_event_rainfall(loc_df, start="2025-11-26", end="2025-11-30")
        hist_max = annual_max_window(
            loc_df, window=5, month=11, first_year=1940, last_year=2024
        )
        rp = return_period(hist_max.values, loc_rain)
        rp_str = "> 10,000 years" if rp > 10000 else f"~{int(round(rp, -1)):,} years"

        event_mask = (loc_df["date"] >= "2025-11-26") & (loc_df["date"] <= "2025-11-30")
        max_wind = round(float(loc_df.loc[event_mask, "wind_speed_10m_max"].max()), 1)

        map_data.append(
            {
                "City": loc.name,
                "lat": loc.latitude,
                "lon": loc.longitude,
                "Ditwah Rain (mm)": round(loc_rain, 1),
                "Max Wind (km/h)": max_wind,
                "Estimated Return Period": rp_str,
            }
        )

    map_df = pd.DataFrame(map_data)

    fig_map = px.scatter_map(
        map_df,
        lat="lat",
        lon="lon",
        size="Ditwah Rain (mm)",
        color="Ditwah Rain (mm)",
        hover_name="City",
        hover_data=["Estimated Return Period", "Max Wind (km/h)"],
        color_continuous_scale="Blues",
        zoom=6.5,
        center={"lat": 7.8, "lon": 80.7},
    )
    fig_map.update_layout(map_style="carto-positron", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)


# ==========================================
# APP ROUTER
# ==========================================
pg = st.navigation(
    [
        st.Page(page_overview, title="Climate & Warming", icon="🌡️", default=True),
        st.Page(page_extremes, title="Rain Extremes", icon="🌧️"),
        st.Page(page_footprint, title="Cyclone Footprint", icon="🗺️"),
    ]
)

pg.run()