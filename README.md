# 🌧️ Cyclone Ditwah Weather Report

Cyclone Ditwah Weather Report lets you explore the historical climate context of Sri Lanka, evaluate local warming trends, and analyze the unprecedented severity of the November 2025 cyclone in an interactive web app.

![built with Streamlit](https://imgshields.io/badge/built%20with-Streamlit-FF4B4B.svg) ![python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)

## What the app does

The app has three main tabs:

| Tab | What you can do |
| :--- | :--- |
| **Cyclone Footprint** | An interactive map of Sri Lanka showing where Cyclone Ditwah hit the hardest, displaying total 5-day rainfall across 10 grid points. |
| **Rain Extremes** | A historical bar chart comparing the cyclone's rainfall to the highest 5-day precipitation recorded every November from 1940 to 2024. |
| **Warming Trend** | A visualization of the shifting baseline climate, showing annual temperature anomalies compared to the 1961-1990 historical average with a 10-year rolling trend. |

## How the statistical analysis works

To determine if the cyclone was just a bad storm or a true statistical outlier, we calculate specific extreme weather metrics:

| Metric | Description |
| :--- | :--- |
| **Event Rainfall** | The total accumulated precipitation (mm) during the 5-day storm window (Nov 26-30, 2025). |
| **Historical Percentile** | How the event compares to all previous November 5-day windows since 1940 (100% means it broke the all-time record). |
| **Return Period (GEV)** | Estimated probability of recurrence using a Generalized Extreme Value distribution fit to annual historical maxima. |

Statistical models and calculations live in one place, `ditwah_weather/analysis.py`, so they are easy to audit or change.

## Data sources

* **[Open-Meteo Historical Weather API](https://open-meteo.com/)**: used to fetch daily historical reanalysis grid data (temperature, precipitation, wind speed) from 1940 to 2025 for 10 major locations in Sri Lanka.
* `data/`: the local folder where the CSV files for each location are saved. The repository does not track these large files by default, so they must be downloaded during the initial setup.

## Libraries

| Library | Used for |
| :--- | :--- |
| `requests` | calling the Open-Meteo API |
| `pandas` | storing, cleaning, and filtering the weather time-series data |
| `plotly` | interactive maps and charts |
| `streamlit` | the web application |
| `jupyter` | running the narrative analysis notebook |
| `pytest` | unit testing the data loaders and mathematical functions |

Exact versions are listed in `requirements.txt`.

## Setup

1. Clone the repository and enter the folder:

```bash
git clone https://github.com/nitisha-jayakody/Cyclone_Ditwah_weatherproject.git
cd Cyclone_Ditwah_weatherproject
```

2. Create a virtual environment and install the dependencies (Python 3.13 or newer):

```bash
python -m venv .venv
source .venv/bin/activate       # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Download the historical climate dataset via the API:

```bash
python scripts/download_weather_data.py
```

## Run

Start the web app:

```bash
streamlit run app.py
```

The browser opens at `http://localhost:8501`. Use the sidebar to move between grid points.

The backend can also be used without Streamlit, like any library:

```python
from ditwah_weather.io import load_all
from ditwah_weather.analysis import calculate_event_rainfall
from pathlib import Path

# Load data and calculate Ditwah's rainfall for Dankotuwa
df = load_all(Path("data"))
dankotuwa_df = df[df['city'] == "Dankotuwa"]
rain = calculate_event_rainfall(dankotuwa_df, start='2025-11-26', end='2025-11-30')
print(f"Total Rainfall: {rain} mm")
```

## The analysis notebook

`notebooks/analysis_report.ipynb` uses the `ditwah_weather` package step by step: it loads the historical data, calculates the warming trends, identifies extreme rainfall events, and fits the GEV distribution to estimate return periods. Start Jupyter from the project folder and open it:

```bash
jupyter notebook
```

## Project structure

```text
Cyclone_Ditwah_weatherproject/
├── app.py                      # Streamlit entry point: declares the dashboard
├── src/
│   └── ditwah_weather/         # the backend package (no Streamlit code here)
│       ├── __init__.py
│       ├── api.py              # Open-Meteo API calls and error handling
│       ├── cleaning.py         # data formatting and validation
│       ├── config.py           # constants (e.g., LOCATIONS coordinates)
│       ├── io.py               # the data loader functions
│       └── analysis.py         # anomalies, percentiles, and GEV statistics
├── scripts/
│   └── download_weather_data.py # script to fetch raw data to the data/ folder
├── tests/
│   ├── test_io.py              # unit tests for the data loader
│   └── test_analysis.py        # unit tests for the math
├── data/                       # the downloaded CSV datasets (ignored by git)
├── notebooks/
│   └── analysis_report.ipynb   # the project, step by step, in a notebook
├── docs/
│   └── REVIEW_GUIDE.md         # study notes for the oral exam
├── .gitignore
├── requirements.txt
└── README.md
```

Everything in `src/ditwah_weather/` is plain Python that can be reused in a notebook (see `notebooks/`) or a script, while `app.py` only deals with showing things on screen.