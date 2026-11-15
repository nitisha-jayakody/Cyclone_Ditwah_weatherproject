# Cyclone Ditwah Weather Analysis

This project analyses historical weather conditions in Sri Lanka during
Cyclone Ditwah, 26–30 November 2025, and compares them with historical
November climate conditions.

## Research question

Which selected Sri Lankan locations experienced the most extreme rainfall
during Cyclone Ditwah, and how did Negombo/Dankotuwa compare with them?

## Data

- Source: Open-Meteo Historical Weather API
- Period: 1940–2025
- Main variable: daily precipitation
- Secondary variables: maximum/minimum temperature and maximum wind speed
- Locations: 10 Sri Lankan towns or district centres

## How to run

1. Create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Download data: `python scripts/download_weather_data.py`
4. Run the notebook: `notebooks/01_cyclone_ditwah_analysis.ipynb`
5. Run the app: `streamlit run app.py`