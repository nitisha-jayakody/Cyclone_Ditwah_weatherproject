import requests
import pandas as pd
import time

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
]

def get_daily_weather(latitude, longitude, start_date, end_date):
    """
    Download daily historical weather data from Open-Meteo with rate limit handling.
    
    Args:
        latitude (float): Location latitude.
        longitude (float): Location longitude.
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        
    Returns:
        pd.DataFrame: A dataframe containing daily weather data.
        
    Raises:
        Exception: If the rate limit is exceeded 5 times.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": DAILY_VARIABLES,
        "timezone": "Asia/Colombo",
    }

    # Try up to 5 times to get the data if the server blocks us
    for attempt in range(5):
        response = requests.get(BASE_URL, params=params, timeout=60)
        
        # If we get a 429 Too Many Requests, wait 15 seconds and try again
        if response.status_code == 429:
            print(f"  [API Limit] Server says too fast. Waiting 15 seconds (Attempt {attempt + 1}/5)...")
            time.sleep(15)
            continue
            
        # If it's a different error, crash normally
        response.raise_for_status()

        # Process the successful data
        daily = response.json()["daily"]
        df = pd.DataFrame(daily)
        df["date"] = pd.to_datetime(df["time"])

        return df
        
    raise RuntimeError("API rate limit exceeded too many times. Please wait 5 minutes and try again.")