"""Statistical engine for the Cyclone Ditwah weather analysis.

All functions are pure (no plotting, no file I/O): they take a pandas
DataFrame with at least a ``date`` column and the relevant weather variable,
and return numbers, Series or DataFrames. Notebooks and the Streamlit app
should import these functions rather than re-implementing the logic.
"""

import numpy as np
import pandas as pd
from scipy import stats

from ditwah_weather.config import (
    BASELINE_END,
    BASELINE_START,
    EVENT_END,
    EVENT_START,
)

PRECIP = "precipitation_sum"
TEMP_MAX = "temperature_2m_max"


# --------------------------------------------------------------------------
# Event and rainfall windows
# --------------------------------------------------------------------------
def calculate_event_rainfall(df, start=EVENT_START, end=EVENT_END, var=PRECIP):
    """Calculate the total rainfall of an event.

    Args:
        df: DataFrame with a ``date`` column and the column ``var``.
        start: First day of the event (inclusive).
        end: Last day of the event (inclusive).
        var: Name of the precipitation column (mm).

    Returns:
        Total precipitation (mm) between ``start`` and ``end``.

    Raises:
        ValueError: If the event window is empty or contains missing values.
    """
    dates = pd.to_datetime(df["date"])
    mask = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
    window = df.loc[mask, var]

    if window.empty:
        raise ValueError(f"No data between {start} and {end}")
    if window.isna().any():
        raise ValueError(f"Missing values inside the event window {start} - {end}")
    return float(window.sum())


def window_totals(
    df,
    window=5,
    month=11,
    first_year=BASELINE_START,
    last_year=BASELINE_END,
    var=PRECIP,
):
    """Compute rolling multi-day totals inside one calendar month.

    The rolling window is restarted for every year, so a window never mixes
    days from two different years (e.g. 27-30 Nov of one year with 1-4 Nov
    of the next one). Days missing from the data produce NaN windows, which
    are dropped.

    Args:
        df: DataFrame with a ``date`` column and the column ``var``.
        window: Length of the rolling window in days.
        month: Calendar month (1-12) the windows must lie in.
        first_year: First year to include.
        last_year: Last year to include.
        var: Name of the precipitation column (mm).

    Returns:
        Series of window totals (mm) with a (year, date) MultiIndex, where
        ``date`` is the last day of each window.
    """
    series = (
        df.assign(date=pd.to_datetime(df["date"]))
        .set_index("date")
        .sort_index()[var]
        .asfreq("D")  # make gaps explicit (NaN) so rows are consecutive days
    )

    in_period = (
        (series.index.month == month)
        & (series.index.year >= first_year)
        & (series.index.year <= last_year)
    )
    selected = series[in_period]

    totals = selected.groupby(selected.index.year).rolling(window).sum().dropna()
    totals.index = totals.index.set_names(["year", "date"])
    return totals


def annual_max_window(df, **kwargs):
    """Return the maximum rolling total for each year.

    Args:
        df: DataFrame with a ``date`` column and a precipitation column.
        **kwargs: Passed to :func:`window_totals` (window, month, years, var).

    Returns:
        Series indexed by year with the largest window total (mm) of that
        year: one independent value per year.
    """
    return window_totals(df, **kwargs).groupby(level="year").max()


def calculate_historical_percentile(df, event_total, **kwargs):
    """Compare an event total with historical windows of the same length.

    Args:
        df: DataFrame with a ``date`` column and a precipitation column.
        event_total: Rainfall total (mm) of the event to compare.
        **kwargs: Passed to :func:`window_totals` (window, month, years, var).

    Returns:
        Percentage (0-100, 2 decimals) of historical windows with a total
        strictly lower than ``event_total``. Returns 0.0 if there are no
        historical windows.
    """
    totals = window_totals(df, **kwargs)
    if totals.empty:
        return 0.0
    return round(float((totals < event_total).mean() * 100), 2)


# --------------------------------------------------------------------------
# Temperature anomalies and trends
# --------------------------------------------------------------------------
def add_anomalies(df, base=(1961, 1990), var=TEMP_MAX):
    """Add the deviation of ``var`` from its monthly baseline average.

    The baseline is the mean of each calendar month over the years in
    ``base`` (computed per city if a ``city`` column exists). Subtracting it
    removes the seasonal cycle so that long-term changes become visible.

    Args:
        df: DataFrame with a ``date`` column and the column ``var``.
        base: (first_year, last_year) of the reference period, inclusive.
        var: Name of the column to compute anomalies for.

    Returns:
        Copy of ``df`` with the extra columns ``year``, ``month``,
        ``climatology`` and ``anomaly``.
    """
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["year"] = out["date"].dt.year
    out["month"] = out["date"].dt.month

    keys = ["city", "month"] if "city" in out.columns else ["month"]
    in_base = out["year"].between(*base)
    climatology = out[in_base].groupby(keys)[var].mean().rename("climatology")

    out = out.join(climatology, on=keys)
    out["anomaly"] = out[var] - out["climatology"]
    return out


def annual_anomaly(df_anomalies):
    """Average the daily anomalies of :func:`add_anomalies` by year.

    Args:
        df_anomalies: Output of :func:`add_anomalies`.

    Returns:
        Series indexed by year with the mean anomaly.
    """
    return df_anomalies.groupby("year")["anomaly"].mean()


def decadal_trend(years, values):
    """Fit a straight line and express its slope per decade.

    Args:
        years: Sequence of years (x values).
        values: Sequence of observations (y values), same length as ``years``.

    Returns:
        Tuple ``(slope_per_decade, p_value)``. Pairs with a missing value
        are ignored.
    """
    x = np.asarray(years, dtype=float)
    y = np.asarray(values, dtype=float)
    valid = ~np.isnan(x) & ~np.isnan(y)
    result = stats.linregress(x[valid], y[valid])
    return float(result.slope * 10), float(result.pvalue)


# --------------------------------------------------------------------------
# Extreme value analysis
# --------------------------------------------------------------------------
def return_period(history, event_value):
    """Estimate the return period of an extreme value.

    A Generalised Extreme Value (GEV) distribution is fitted to ``history``
    (typically one annual maximum per year). The return period is the
    inverse of the probability of exceeding ``event_value`` in a year.

    With few observations and an extreme event the estimate is very
    uncertain: interpret it as an order of magnitude, not an exact number.

    Args:
        history: Sequence of annual maxima (must NOT include the event).
        event_value: Value whose return period is wanted.

    Returns:
        Return period in years, or ``numpy.inf`` if the fitted distribution
        gives the event zero probability.
    """
    params = stats.genextreme.fit(np.asarray(history, dtype=float))
    exceedance = stats.genextreme.sf(event_value, *params)
    return float(np.inf) if exceedance == 0 else float(1 / exceedance)