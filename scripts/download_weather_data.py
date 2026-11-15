"""Download daily weather data for configured locations."""

import sys
import os
import time
from pathlib import Path
import pandas as pd

# Locate the project root and the src directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Add src to Python's module search path.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# pylint: disable=wrong-import-position
from ditwah_weather.api import get_daily_weather
from ditwah_weather.cleaning import clean_weather_data
from ditwah_weather.config import LOCATIONS

# Define the output directory.
DATA_DIR = PROJECT_ROOT / "data"

def main():
    """Download, clean, and save weather data for each location."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for location in LOCATIONS:
        # Generate the output filename and path first
        filename = location.name.lower().replace(" ", "_")
        output_path = DATA_DIR / f"{filename}_weather.csv"

        # SKIP CHECK: If the CSV already exists, skip to the next city
        if output_path.exists():
            print(f"Skipping {location.name} (already downloaded)...")
            continue

        print(f"Downloading {location.name}...")

        # Download raw weather data.
        raw = get_daily_weather(
            latitude=location.latitude,
            longitude=location.longitude,
            start_date="1940-01-01",
            end_date="2025-12-31",
        )

        # Clean the downloaded data.
        clean = clean_weather_data(raw, location.name)

        # Save the cleaned data as CSV.
        clean.to_csv(output_path, index=False)

        print(f"Saved {filename}_weather.csv")
        
        # Pause for 5 seconds before asking the API for the next city
        print("Waiting 5 seconds to avoid API rate limits...")
        time.sleep(5)

if __name__ == "__main__":
    main()