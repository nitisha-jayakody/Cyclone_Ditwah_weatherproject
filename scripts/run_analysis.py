"""Run the statistical analysis for Cyclone Ditwah."""

import sys
from pathlib import Path
import pandas as pd

# Setup path so Python finds the src folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# pylint: disable=wrong-import-position
from ditwah_weather.config import LOCATIONS
from ditwah_weather.analysis import calculate_event_rainfall, calculate_historical_percentile

DATA_DIR = PROJECT_ROOT / "data"

def main():
    print("Cyclone Ditwah (Nov 26-30, 2025) Rainfall Analysis\n" + "-"*50)
    
    for location in LOCATIONS:
        filename = location.name.lower().replace(" ", "_")
        filepath = DATA_DIR / f"{filename}_weather.csv"
        
        if not filepath.exists():
            print(f"Missing data for {location.name}. Skipping...")
            continue
            
        # Load the CSV
        df = pd.read_csv(filepath)
        df["date"] = pd.to_datetime(df["date"])
        
        # Run the math
        event_rain = calculate_event_rainfall(df)
        percentile = calculate_historical_percentile(df, event_rain)
        
        print(f"{location.name}:")
        print(f"  Cyclone Rainfall: {event_rain:.1f} mm")
        print(f"  Severity: {percentile}th percentile of all historical Novembers\n")

if __name__ == "__main__":
    main()