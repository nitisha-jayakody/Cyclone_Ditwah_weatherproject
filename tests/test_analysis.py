"""Tests for ditwah_weather.analysis."""

import numpy as np
import pandas as pd
import pytest

from ditwah_weather.analysis import (
    add_anomalies,
    annual_max_window,
    calculate_event_rainfall,
    calculate_historical_percentile,
    decadal_trend,
    return_period,
    window_totals,
)


def make_novembers(years, rain_by_date=None):
    """Build a daily DataFrame covering the whole of each given year."""
    dates = pd.date_range(f"{years[0]}-01-01", f"{years[-1]}-12-31")
    df = pd.DataFrame({"date": dates, "precipitation_sum": 0.0})
    for day, mm in (rain_by_date or {}).items():
        df.loc[df["date"] == day, "precipitation_sum"] = mm
    return df


def test_windows_do_not_cross_years():
    df = make_novembers([1999, 2000], {"1999-11-30": 100.0})
    totals = window_totals(df, first_year=1999, last_year=2000)
    # no window of 2000 may contain the 100 mm fallen on 30 Nov 1999
    assert totals.loc[2000].max() == 0.0
    assert totals.loc[1999].max() == 100.0


def test_window_count_per_year():
    df = make_novembers([2000, 2001])
    totals = window_totals(df, window=5, first_year=2000, last_year=2001)
    assert (totals.groupby(level="year").size() == 26).all()


def test_gap_in_data_is_not_bridged():
    df = make_novembers([2000], {"2000-11-10": 10.0})
    df = df[df["date"] != "2000-11-11"]  # remove one day
    totals = window_totals(df, first_year=2000, last_year=2000)
    assert totals.index.get_level_values("date").min() >= pd.Timestamp("2000-11-05")
    # windows containing the missing day are dropped, not computed on 4 days
    assert pd.Timestamp("2000-11-12") not in totals.index.get_level_values("date")


def test_event_rainfall_sum_and_errors():
    df = make_novembers([2025], {"2025-11-26": 100.0, "2025-11-30": 50.5})
    assert calculate_event_rainfall(df) == pytest.approx(150.5)
    df.loc[df["date"] == "2025-11-28", "precipitation_sum"] = np.nan
    with pytest.raises(ValueError):
        calculate_event_rainfall(df)


def test_percentile_extreme_event_is_100():
    df = make_novembers(range(1990, 1995), {"1992-11-10": 40.0})
    assert calculate_historical_percentile(
        df, 480.6, first_year=1990, last_year=1994) == 100.0


def test_annual_max_one_value_per_year():
    df = make_novembers([1999, 2000], {"1999-11-15": 30.0, "2000-11-15": 70.0})
    out = annual_max_window(df, first_year=1999, last_year=2000)
    assert out.to_dict() == {1999: 30.0, 2000: 70.0}


def test_anomalies_zero_in_baseline_and_positive_after():
    dates = pd.date_range("1961-01-01", "2000-12-31")
    temp = np.where(dates.year >= 1991, 31.0, 30.0)
    df = pd.DataFrame({"date": dates, "temperature_2m_max": temp})
    out = add_anomalies(df, base=(1961, 1990))
    assert out.loc[out["year"] <= 1990, "anomaly"].abs().max() < 1e-9
    assert out.loc[out["year"] >= 1991, "anomaly"].mean() == pytest.approx(1.0)


def test_decadal_trend_recovers_slope():
    years = np.arange(1950, 2020)
    slope, p = decadal_trend(years, 0.02 * (years - 1950) + 28)
    assert slope == pytest.approx(0.2)
    assert p < 0.001


def test_return_period_increases_with_value():
    rng = np.random.default_rng(0)
    history = rng.gumbel(loc=100, scale=20, size=85)
    assert return_period(history, 200) > return_period(history, 120) > 1