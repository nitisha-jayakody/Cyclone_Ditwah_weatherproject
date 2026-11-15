import pandas as pd

def clean_weather_data(df, location_name):
    """Clean and validate one location's weather DataFrame."""

    required = {
        "date",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.copy()
    df["location"] = location_name
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Negative rainfall is invalid.
    df["precipitation_sum"] = df["precipitation_sum"].clip(lower=0)

    return df