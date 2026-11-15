import requests
import pandas as pd

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
]

def get_daily_weather(latitude, longitude, start_date, end_date):
    """Download daily historical weather data from Open-Meteo."""

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": DAILY_VARIABLES,
        "timezone": "Asia/Colombo",
    }

    response = requests.get(BASE_URL, params=params, timeout=60)
    response.raise_for_status()

    daily = response.json()["daily"]
    df = pd.DataFrame(daily)
    df["date"] = pd.to_datetime(df["date"])

    return df