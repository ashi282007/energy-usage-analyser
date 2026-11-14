"""Automated tests for the Energy Insight backend.

Run from the project folder (the one that contains src/ and data/):

    python -m pytest tests -v

The first groups use small made-up data whose correct answers are known in
advance. The last group checks the real database (skipped if it is missing).
"""

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "src"))

import analysis                      # noqa: E402
import anomaly_detection as ad       # noqa: E402
import clean_data                    # noqa: E402
import forecasting as fc             # noqa: E402


# --------------------------------------------------
# Helpers that build small test data
# --------------------------------------------------

def hourly_frame(days, value=1.0, start="2024-01-01"):
    """`days` full days of hourly data, every hour complete."""

    times = pd.date_range(start, periods=days * 24, freq="h")

    return pd.DataFrame({
        "datetime": times,
        "energy_kwh": value,
        "is_complete": 1,
        "coverage_percent": 100.0
    })


def make_incomplete(df, mask):
    """Mark the rows selected by `mask` as incomplete hours."""

    df = df.copy()
    df.loc[mask, "energy_kwh"] = np.nan
    df.loc[mask, "is_complete"] = 0
    df.loc[mask, "coverage_percent"] = 50.0

    return df


# --------------------------------------------------
# analysis.build_daily_series
# --------------------------------------------------

def test_daily_series_sums_full_days():

    daily = analysis.build_daily_series(hourly_frame(3))

    assert list(daily) == [24.0, 24.0, 24.0]


def test_daily_series_partial_day_is_nan_not_zero():

    df = hourly_frame(3)

    # two hours of day 2 have no reading
    df = make_incomplete(df, df["datetime"].between(
        "2024-01-02 03:00", "2024-01-02 04:00"))

    daily = analysis.build_daily_series(df)

    assert np.isnan(daily.iloc[1])
    assert daily.iloc[0] == 24.0 and daily.iloc[2] == 24.0


def test_daily_series_scales_partial_day_when_allowed():

    df = hourly_frame(2)

    df = make_incomplete(df, df["datetime"].between(
        "2024-01-02 03:00", "2024-01-02 04:00"))

    daily = analysis.build_daily_series(df, min_hours=20)

    assert daily.iloc[1] == pytest.approx(24.0)


def test_daily_series_keeps_missing_days_in_the_index():

    df = hourly_frame(4)

    df = df[df["datetime"].dt.day != 2]          # remove a whole day

    daily = analysis.build_daily_series(df)

    assert len(daily) == 4                        # no gap in the index
    assert np.isnan(daily.iloc[1])


# --------------------------------------------------
# analysis.kpi_summary and key_findings
# --------------------------------------------------

def test_kpi_summary_uses_all_hours_for_coverage_and_full_days_for_average():

    day1 = hourly_frame(1, value=1.0, start="2024-01-01")
    day2 = hourly_frame(1, value=2.0, start="2024-01-02")

    # second day: only the first 12 hours are complete
    day2 = make_incomplete(day2, day2["datetime"].dt.hour >= 12)

    hourly = pd.concat([day1, day2], ignore_index=True)

    result = analysis.kpi_summary(
        hourly, pd.Timestamp("2024-01-01").date(),
        pd.Timestamp("2024-01-02").date(), tariff=0.5
    )

    assert result["total_energy_kwh"] == pytest.approx(24 * 1.0 + 12 * 2.0)
    assert result["average_daily_kwh"] == pytest.approx(24.0)   # day 2 excluded
    assert result["full_days"] == 1
    # (24*100 + 12*100 + 12*50) / 48
    assert result["data_coverage_percent"] == pytest.approx(87.5)
    assert result["estimated_cost"] == pytest.approx(48.0 * 0.5)


def test_key_findings_recover_a_known_pattern():

    df = hourly_frame(28, value=1.0)

    df.loc[df["datetime"].dt.hour == 20, "energy_kwh"] = 3.0   # busy evening
    df.loc[df["datetime"].dt.hour == 4, "energy_kwh"] = 0.5    # quiet night

    result = analysis.key_findings(df, price_per_kwh=0.30, evening_cut=0.20)

    assert result["busiest_hour"] == 20
    assert result["quietest_hour"] == 4
    assert result["baseload_kwh_per_day"] == pytest.approx(0.5 * 24)
    assert result["weekend_vs_weekday_percent"] == pytest.approx(0.0)

    evening_per_day = 1 + 1 + 3 + 1 + 1                        # hours 18-22
    assert result["evening_saving_kwh_per_year"] == pytest.approx(
        evening_per_day * 0.20 * 365)
    assert result["evening_saving_eur_per_year"] == pytest.approx(
        evening_per_day * 0.20 * 365 * 0.30)


# --------------------------------------------------
# anomaly_detection
# --------------------------------------------------

def noisy_daily_series(seed=0, days=200, level=25.0, noise=2.0):

    rng = np.random.default_rng(seed)

    index = pd.date_range("2024-01-01", periods=days, freq="D", name="date")

    return pd.Series(level + rng.normal(0, noise, days), index=index,
                     name="energy_kwh")


def test_daily_anomaly_detection_flags_an_injected_spike():

    series = noisy_daily_series()

    spike_day = series.index[100]

    series.loc[spike_day] = 70.0

    frame = ad.detect_daily_anomalies(series)

    assert bool(frame.loc[spike_day, "is_anomaly"])
    assert frame.loc[spike_day, "direction"] == "high"
    assert frame["is_anomaly"].sum() <= 4        # almost no false alarms


def test_daily_anomaly_detection_flags_an_unusually_low_day():

    series = noisy_daily_series(seed=1)

    low_day = series.index[60]

    series.loc[low_day] = 2.0

    frame = ad.detect_daily_anomalies(series, direction="low")

    assert bool(frame.loc[low_day, "is_anomaly"])
    assert (frame.loc[frame["is_anomaly"], "direction"] == "low").all()


def test_nan_days_are_skipped_not_flagged():

    series = noisy_daily_series()

    series.iloc[10:15] = np.nan

    frame = ad.detect_daily_anomalies(series)

    assert len(frame) == len(series) - 5


def test_constant_series_does_not_crash_and_flags_nothing():

    series = pd.Series(
        10.0, index=pd.date_range("2024-01-01", periods=60, freq="D"))

    frame = ad.detect_daily_anomalies(series)

    assert frame["is_anomaly"].sum() == 0
    assert np.isfinite(frame["score"]).all()


def test_hourly_detection_ignores_incomplete_hours():

    df = hourly_frame(60, value=1.0)

    rng = np.random.default_rng(3)
    df["energy_kwh"] = 1.0 + rng.normal(0, 0.05, len(df))

    bad = df["datetime"] == "2024-01-10 12:00"
    df.loc[bad, "energy_kwh"] = 50.0
    df.loc[bad, "is_complete"] = 0               # a faulty, incomplete hour

    frame = ad.detect_hourly_anomalies(df)

    assert pd.Timestamp("2024-01-10 12:00") not in frame.index


def test_find_data_gaps_reports_only_long_runs():

    df = hourly_frame(3)

    long_gap = df["datetime"].between("2024-01-02 00:00", "2024-01-02 07:00")
    short_gap = df["datetime"].between("2024-01-03 10:00", "2024-01-03 12:00")

    df = make_incomplete(df, long_gap | short_gap)

    gaps = ad.find_data_gaps(df, min_hours=6)

    assert len(gaps) == 1
    assert gaps.loc[0, "hours"] == 8


# --------------------------------------------------
# forecasting
# --------------------------------------------------

def test_backtest_never_uses_the_days_it_predicts():
    """With series[i] = i, a naive forecast for a block must equal the value
    of the day before the block. Anything else would mean data leaked."""

    series = pd.Series(
        np.arange(120, dtype=float),
        index=pd.date_range("2024-01-01", periods=120, freq="D"))

    bt = fc.backtest(series, fc.naive_last_value, horizon=7, test_days=56)

    for _, block in bt.groupby("fold"):
        assert block["forecast"].nunique() == 1
        assert block["forecast"].iloc[0] == block["actual"].min() - 1


def test_seasonal_models_win_on_a_pure_weekly_pattern():

    pattern = [10, 12, 11, 13, 12, 20, 22]

    series = pd.Series(
        pattern * 40,
        index=pd.date_range("2024-01-01", periods=280, freq="D"),
        dtype=float)

    table = fc.compare_models(series, horizon=7, test_days=84)

    best = table.iloc[0]

    assert "Seasonal" in best["Model"]
    assert best["MAE (kWh/day)"] == pytest.approx(0.0, abs=1e-9)

    naive_mae = table.loc[table["Model"] == fc.BASELINE_NAME,
                          "MAE (kWh/day)"].iloc[0]

    assert naive_mae > 1.0


def test_moving_average_model_value():

    series = pd.Series(
        [1.0, 2.0, 3.0, 4.0],
        index=pd.date_range("2024-01-01", periods=4, freq="D"))

    forecast = fc.moving_average(series, horizon=3, days=2)

    assert list(forecast) == [3.5, 3.5, 3.5]


def test_forecast_future_output_is_well_formed():

    series = noisy_daily_series(days=400)

    forecast_df, bt = fc.forecast_future(
        series, "Moving average (last 14 days)", horizon=14)

    assert len(forecast_df) == 14
    assert forecast_df["date"].iloc[0] == series.index[-1] + pd.Timedelta(days=1)
    assert (forecast_df["lower"] <= forecast_df["upper"]).all()
    assert (forecast_df["lower"] >= 0).all()
    assert len(bt) > 100


# --------------------------------------------------
# clean_data (hourly aggregation rules)
# --------------------------------------------------

def test_hourly_table_marks_incomplete_and_missing_hours():

    def hour_of_minutes(start, values):
        return pd.Series(
            values, index=pd.date_range(start, periods=len(values), freq="min"),
            dtype=float)

    hour0 = hour_of_minutes("2024-01-01 00:00", [2.0] * 60)            # complete
    hour1 = hour_of_minutes("2024-01-01 01:00", [3.0] * 50 + [np.nan] * 10)
    hour3 = hour_of_minutes("2024-01-01 03:00", [1.0] * 60)            # hour 2 absent

    minutes = pd.concat([hour0, hour1, hour3])

    table = clean_data.build_hourly_table(minutes)

    assert len(table) == 4                                   # hour 2 re-created

    complete, partial, absent, last = (table.iloc[i] for i in range(4))

    assert complete["is_complete"] == 1
    assert complete["energy_kwh"] == pytest.approx(2.0)

    assert partial["is_complete"] == 0
    assert np.isnan(partial["energy_kwh"])
    assert partial["valid_minutes"] == 50
    assert partial["coverage_percent"] == pytest.approx(50 / 60 * 100)
    assert partial["observed_energy_kwh"] == pytest.approx(3.0 * 50 / 60)

    assert absent["total_records"] == 0
    assert absent["is_complete"] == 0
    assert np.isnan(absent["energy_kwh"])

    assert last["energy_kwh"] == pytest.approx(1.0)


# --------------------------------------------------
# The real database (skipped when it is not there)
# --------------------------------------------------

DB_PATH = ROOT / "data" / "processed" / "energy_v2.db"

needs_db = pytest.mark.skipif(
    not DB_PATH.exists(), reason="energy_v2.db not found")


@pytest.fixture(scope="module")
def real_hourly():

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM hourly_usage ORDER BY datetime", conn)

    df["datetime"] = pd.to_datetime(df["datetime"])

    return df


@needs_db
def test_database_has_no_duplicate_timestamps(real_hourly):

    assert real_hourly["datetime"].is_unique


@needs_db
def test_database_covers_every_hour_without_gaps(real_hourly):

    steps = real_hourly["datetime"].diff().dropna()

    assert (steps == pd.Timedelta(hours=1)).all()


@needs_db
def test_database_completeness_flag_matches_valid_minutes(real_hourly):

    assert ((real_hourly["valid_minutes"] == 60)
            == (real_hourly["is_complete"] == 1)).all()


@needs_db
def test_database_energy_is_missing_exactly_when_hour_is_incomplete(real_hourly):

    assert (real_hourly["energy_kwh"].isna()
            == (real_hourly["is_complete"] == 0)).all()


@needs_db
def test_database_values_are_in_valid_ranges(real_hourly):

    assert real_hourly["coverage_percent"].between(0, 100).all()
    assert (real_hourly["energy_kwh"].dropna() >= 0).all()
