import pandas as pd
from ditwah_weather.config import EVENT_START, EVENT_END, BASELINE_START, BASELINE_END

def calculate_event_rainfall(df):
    """Calculate total rainfall (in mm) during Cyclone Ditwah (Nov 26-30, 2025)."""
    mask = (df["date"] >= EVENT_START) & (df["date"] <= EVENT_END)
    return df[mask]["precipitation_sum"].sum()

def calculate_historical_percentile(df, event_total):
    """Compare the 2025 event rainfall to historical 5-day periods (1940-2024)."""
    
    # 1. Isolate the baseline years (1940 to 2024)
    baseline = df[(df["date"].dt.year >= BASELINE_START) & (df["date"].dt.year <= BASELINE_END)].copy()
    
    # 2. Filter for November only (to compare apples-to-apples)
    november_data = baseline[baseline["date"].dt.month == 11].copy()
    
    # 3. Calculate all possible 5-day rainfall totals in historical Novembers
    november_data = november_data.sort_values("date").set_index("date")
    rolling_5d = november_data["precipitation_sum"].rolling(window=5).sum().dropna()
    
    # 4. Calculate what percentage of historical periods were lower than our 2025 event
    if len(rolling_5d) == 0:
        return 0.0
    
    percentile = (rolling_5d < event_total).mean() * 100
    return round(percentile, 2)