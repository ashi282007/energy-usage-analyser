"""Shared analysis helpers.

Both forecasting.py and anomaly_detection.py need the same thing: one
electricity total (kWh) per day. It lives here so the rule for "what counts
as a usable day" is defined in exactly one place.
"""

import calendar

import numpy as np
import pandas as pd


def build_daily_series(df, min_hours=24):
    """Return daily energy use (kWh) as a Series with one row per calendar day.

    Parameters
    ----------
    df : DataFrame
        Hourly data with the columns ``datetime``, ``energy_kwh`` and
        ``is_complete`` (the ``hourly_usage`` table from energy_v2.db).
    min_hours : int
        A day is only kept if it has at least this many complete hours.
        With the default (24) a day must be fully observed. A smaller number
        keeps partly observed days and scales their total up to 24 hours,
        which assumes the missing hours look like the observed ones.

    Days that do not qualify are NaN (not 0), so they are never mistaken
    for "no electricity used". The index covers every day from the first
    to the last observation without gaps, which the forecasting models
    rely on.
    """

    complete = df.loc[
        (df["is_complete"] == 1) & df["energy_kwh"].notna(),
        ["datetime", "energy_kwh"]
    ]

    per_day = (
        complete.set_index("datetime")["energy_kwh"]
        .resample("D")
        .agg(["sum", "count"])
    )

    # Scale partly observed days up to a full 24 hours.
    daily = per_day["sum"] / per_day["count"].replace(0, np.nan) * 24

    # Drop days that do not have enough complete hours.
    daily[per_day["count"] < min_hours] = np.nan

    daily.name = "energy_kwh"
    daily.index.name = "date"

    return daily


# --------------------------------------------------
# 2. PERIOD FILTER AND KPI SUMMARY (used by the dashboard)
# --------------------------------------------------

def filter_period(df, start_date, end_date):
    """Rows whose datetime lies between start_date and end_date (inclusive)."""

    dates = df["datetime"].dt.date

    return df.loc[(dates >= start_date) & (dates <= end_date)]


def kpi_summary(hourly_df, start_date, end_date, tariff):
    """Headline numbers for the dashboard cards.

    ``hourly_df`` must be the FULL hourly table (complete and incomplete
    hours), because data coverage has to be measured over every hour, not
    only over the complete ones.

    total_energy_kwh      sum of complete hours (hours with missing readings
                          are not estimated, so this is a lower bound)
    average_daily_kwh     mean of fully observed days only. A day with
                          missing hours would drag the average down.
    peak_hour_kwh         highest single complete hour
    estimated_cost        total_energy_kwh * tariff
    data_coverage_percent mean coverage over ALL hours in the period
    """

    period = filter_period(hourly_df, start_date, end_date)

    complete = period.loc[
        (period["is_complete"] == 1) & period["energy_kwh"].notna()
    ]

    daily = build_daily_series(complete)

    average_daily = daily.mean()

    if np.isnan(average_daily) and not complete.empty:
        # Period shorter than one fully observed day: scale the hourly mean.
        average_daily = complete["energy_kwh"].mean() * 24

    total_energy = complete["energy_kwh"].sum()

    return {
        "total_energy_kwh": total_energy,
        "average_daily_kwh": average_daily,
        "peak_hour_kwh": complete["energy_kwh"].max(),
        "estimated_cost": total_energy * tariff,
        "data_coverage_percent": period["coverage_percent"].mean(),
        "complete_hours": int(len(complete)),
        "total_hours": int(len(period)),
        "full_days": int(daily.notna().sum())
    }


# --------------------------------------------------
# 3. KEY FINDINGS (the numbers for the README table)
# --------------------------------------------------

def key_findings(
    complete_df,
    price_per_kwh=0.30,
    evening_cut=0.20,
    evening_start=18,
    evening_end=22
):
    """Usage patterns and a simple evening-saving scenario.

    ``complete_df`` holds the complete hourly observations only.

    Baseload is approximated by the quietest hour of the day times 24: the
    power the household draws even in its calmest hour. The saving scenario
    assumes the same percentage cut on every day of the year.
    """

    data = complete_df.copy()

    hourly_avg = data.groupby(data["datetime"].dt.hour)["energy_kwh"].mean()

    busiest_hour = int(hourly_avg.idxmax())
    quietest_hour = int(hourly_avg.idxmin())

    kwh_per_day = hourly_avg.sum()

    baseload_per_day = hourly_avg.min() * 24

    # Calendar patterns use fully observed days, so outages cannot bias them.
    daily = build_daily_series(data).dropna()

    weekend = daily[daily.index.dayofweek >= 5].mean()
    weekday = daily[daily.index.dayofweek < 5].mean()

    by_month = daily.groupby(daily.index.month).mean()

    evening_per_day = hourly_avg.loc[evening_start:evening_end].sum()

    saved_kwh = evening_per_day * evening_cut * 365

    return {
        "busiest_hour": busiest_hour,
        "busiest_hour_kwh": hourly_avg.max(),
        "quietest_hour": quietest_hour,
        "quietest_hour_kwh": hourly_avg.min(),
        "baseload_kwh_per_day": baseload_per_day,
        "baseload_share_percent": baseload_per_day / kwh_per_day * 100,
        "weekend_vs_weekday_percent": (weekend / weekday - 1) * 100,
        "highest_month": calendar.month_name[int(by_month.idxmax())],
        "highest_month_kwh_per_day": by_month.max(),
        "lowest_month": calendar.month_name[int(by_month.idxmin())],
        "lowest_month_kwh_per_day": by_month.min(),
        "evening_share_percent": evening_per_day / kwh_per_day * 100,
        "evening_saving_kwh_per_year": saved_kwh,
        "evening_saving_eur_per_year": saved_kwh * price_per_kwh
    }


# --------------------------------------------------
# 4. RUN THIS FILE TO PRINT THE NUMBERS FOR THE README
# --------------------------------------------------

if __name__ == "__main__":

    from database import load_hourly_data

    hourly = load_hourly_data()

    complete = hourly.loc[
        (hourly["is_complete"] == 1) & hourly["energy_kwh"].notna()
    ]

    print("KEY FINDINGS (complete hours only)\n")

    for name, value in key_findings(complete).items():
        print(f"{name:32s} {value:.2f}" if isinstance(value, float)
              else f"{name:32s} {value}")
