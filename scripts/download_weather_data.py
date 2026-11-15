from pathlib import Path
import pandas as pd

from ditwah_weather.api import get_daily_weather
from ditwah_weather.cleaning import clean_weather_data
from ditwah_weather.config import LOCATIONS

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def main():
    for location in LOCATIONS:
        print(f"Downloading {location.name}...")

        raw = get_daily_weather(
            latitude=location.latitude,
            longitude=location.longitude,
            start_date="1940-01-01",
            end_date="2025-12-31",
        )

        clean = clean_weather_data(raw, location.name)

        filename = location.name.lower().replace(" ", "_")
        clean.to_csv(DATA_DIR / f"{filename}_weather.csv", index=False)

        print(f"Saved {filename}_weather.csv")

if __name__ == "__main__":
    main()