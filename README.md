# 🌧️ Cyclone Ditwah Weather Report

Cyclone Ditwah Weather Report lets you explore the historical climate context of Sri Lanka (1940–2025), evaluate long-term warming trends across 10 locations, and analyze the unprecedented rainfall severity of Cyclone Ditwah (26–30 November 2025) through an interactive Streamlit dashboard and an explanatory Jupyter notebook.

![built with Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B.svg) ![python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)

## What the app does

The Streamlit app has three main pages accessible from the sidebar:

| Page | What you can do |
| :--- | :--- |
| **Climate & Warming** | Explore the 10 analyzed Sri Lankan grid points, inspect annual temperature anomalies against the 1961–1990 baseline with a 10-year rolling mean, and compare monthly anomaly heatmaps side by side for any two cities and year range. |
| **Rain Extremes** | Compare Cyclone Ditwah's 5-day rainfall against the highest November 5-day precipitation recorded every year from 1940 to 2024, alongside historical percentiles and GEV return periods. |
| **Cyclone Footprint** | View an interactive map of Sri Lanka showing the spatial distribution of 5-day rainfall, peak wind speed, and estimated return periods across all 10 locations. |

## How the statistical analysis works

To distinguish long-term climate warming from an extreme weather outlier, the project computes four core metrics:

| Metric | Description |
| :--- | :--- |
| **Temperature Anomalies & Trends** | Daily deviations from the 1961–1990 monthly baseline averaged by year, with decadal warming slopes and p-values via linear regression. |
| **Event Rainfall** | Total accumulated precipitation (mm) during the 5-day storm window (Nov 26–30, 2025). |
| **Historical Percentile** | Percentage of all historical November 5-day windows (1940–2024) strictly lower than the event rainfall (100% means it broke the 85-year record). |
| **Return Period (GEV)** | Estimated recurrence interval from a Generalized Extreme Value (GEV) distribution fitted to annual November 5-day maxima (1940–2024). |

All statistical models and calculations live in `src/ditwah_weather/analysis.py`, keeping presentation layers (`app.py` and the notebook) free of duplicated logic.

## Data sources

* **[Open-Meteo Historical Weather API](https://open-meteo.com/)**: daily historical reanalysis grid data (`temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `wind_speed_10m_max`) from 1940 to 2025 for 10 Sri Lankan locations.
* `data/`: local folder where cleaned CSV files are stored. Large CSV files are excluded from Git via `.gitignore` and must be downloaded during setup.

## Libraries

| Library | Used for |
| :--- | :--- |
| `requests` | calling the Open-Meteo Historical Weather API |
| `pandas` | loading, cleaning, and aggregating weather time-series data |
| `numpy` | numerical array operations |
| `scipy` | linear trend regression and GEV extreme value distribution fitting |
| `plotly` | interactive maps, bar charts, and monthly anomaly heatmaps |
| `streamlit` | building the interactive multi-page web dashboard |
| `jupyterlab` / `ipykernel` | running the narrative analysis notebook |
| `pytest` | unit testing the data loader and statistical functions |

Exact versions are pinned in `requirements.txt`.

## Setup

1. Clone the repository and enter the folder:

```bash
git clone [https://github.com/nitisha-jayakody/Cyclone_Ditwah_weatherproject.git](https://github.com/nitisha-jayakody/Cyclone_Ditwah_weatherproject.git)
cd Cyclone_Ditwah_weatherproject
```

2. Create a virtual environment and install dependencies (Python 3.13 or newer):

```bash
python3 -m venv .venv
source .venv/bin/activate       # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Download the historical weather dataset via the Open-Meteo API:

```bash
python scripts/download_weather_data.py
```

> **Note on API rate limits:** Fetching 85+ years of daily records across 10 locations can trigger HTTP `429` rate limits on Open-Meteo. `scripts/download_weather_data.py` pauses between requests and skips any city CSV already present in `data/`, while `src/ditwah_weather/api.py` retries on `429` responses:
>
> ```python
> for attempt in range(5):
>     response = requests.get(BASE_URL, params=params, timeout=60)
>     if response.status_code == 429:
>         print(f"  [API Limit] Server says too fast. Waiting 15 seconds (Attempt {attempt + 1}/5)...")
>         time.sleep(15)
>         continue
>     response.raise_for_status()
> ```
>
> If the API temporarily blocks your connection for a few minutes, wait briefly and re-run `python scripts/download_weather_data.py` to resume from the remaining cities.

## Run

### Streamlit web app

```bash
streamlit run app.py
```

The browser opens at `http://localhost:8501`. Use the sidebar to switch pages and select any of the 10 Sri Lankan grid points.

### Analysis notebook

`notebooks/analysis_report.ipynb` walks through the full analysis step by step (data loading, warming trends, rain extremes, GEV return periods, and CSV export):

```bash
jupyter lab
```

### Command-line summary & unit tests

```bash
# Quick terminal summary of Cyclone Ditwah rainfall and percentiles
python scripts/run_analysis.py

# Run the unit test suite
pytest
```

### Using the backend package directly

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

from ditwah_weather.io import load_all
from ditwah_weather.analysis import calculate_event_rainfall

df = load_all(Path("data"))
dankotuwa_df = df[df["city"] == "Dankotuwa"]
rain = calculate_event_rainfall(dankotuwa_df, start="2025-11-26", end="2025-11-30")
print(f"Total Rainfall: {rain:.1f} mm")
```

## Project structure

```text
Cyclone_Ditwah_weatherproject/
├── app.py                           # Streamlit dashboard entry point
├── src/
│   └── ditwah_weather/              # Reusable backend package (no Streamlit/plotting)
│       ├── __init__.py
│       ├── api.py                   # Open-Meteo API calls and rate-limit handling
│       ├── cleaning.py              # Data validation and cleaning rules
│       ├── config.py                # Event dates and 10 Sri Lankan grid coordinates
│       ├── io.py                    # Multi-city CSV loader
│       └── analysis.py              # Anomalies, trends, percentiles, and GEV stats
├── scripts/
│   ├── download_weather_data.py     # Fetches and cleans raw API data into data/
│   └── run_analysis.py              # CLI summary of Cyclone Ditwah severity
├── tests/
│   ├── test_io.py                   # Unit tests for the data loader
│   └── test_analysis.py             # Unit tests for the statistical engine
├── notebooks/
│   └── analysis_report.ipynb        # Step-by-step narrative analysis report
├── data/                            # Downloaded CSV files (ignored by Git)
├── outputs/                         # Exported summary tables (ignored by Git)
├── pytest.ini                       # Pytest configuration
├── .gitignore
├── requirements.txt
└── README.md
```