"""Anomaly detection for household electricity use.

Idea
----
Electricity use depends on the season, on weekday vs weekend and (for hourly
data) on the time of day. A single global threshold would just flag every
cold winter evening. So each value is compared only with *similar* values:

    daily  : same month and same day type (weekday / weekend)
    hourly : same month, same day type and same hour of the day

Score
-----
The comparison uses the modified z-score (Iglewicz & Hoaglin, 1993):

    score = (value - median) / (1.4826 * MAD)

where MAD is the median absolute deviation of the group. Median and MAD
are robust: a few extreme days do not distort the baseline, which would
happen with the ordinary mean and standard deviation. A score above
+3.5 or below -3.5 is the textbook cut-off for a potential outlier.

An anomaly is only a *statistically unusual* value. It can be a holiday
trip, a party, a faulty appliance or a measurement problem; the data alone
cannot say which.
"""

import numpy as np
import pandas as pd

# Scale factors that turn MAD (or the mean absolute deviation, used as a
# fallback when MAD is 0) into a standard-deviation-like unit.
MAD_SCALE = 1.4826
MEAN_AD_SCALE = 1.253314


# --------------------------------------------------
# 1. CORE: ROBUST SCORE WITHIN GROUPS
# --------------------------------------------------

def _robust_scores(values, group_keys):
    """Median baseline and modified z-score of each value inside its group."""

    median = values.groupby(group_keys).transform("median")

    abs_dev = (values - median).abs()

    mad = abs_dev.groupby(group_keys).transform("median")
    mean_ad = abs_dev.groupby(group_keys).transform("mean")

    # If more than half of a group has the identical value, MAD is 0.
    # Fall back to the mean absolute deviation so the score stays defined.
    scale = (MAD_SCALE * mad).where(mad > 0, MEAN_AD_SCALE * mean_ad)

    score = (values - median) / scale.replace(0, np.nan)

    return median, score.fillna(0.0)


def _flag(frame, threshold, direction):
    """Add the is_anomaly and direction columns."""

    if direction == "high":
        flagged = frame["score"] > threshold
    elif direction == "low":
        flagged = frame["score"] < -threshold
    else:
        flagged = frame["score"].abs() > threshold

    frame["is_anomaly"] = flagged

    frame["direction"] = np.where(
        flagged,
        np.where(frame["score"] > 0, "high", "low"),
        ""
    )

    return frame


# --------------------------------------------------
# 2. DAILY ANOMALIES
# --------------------------------------------------

def detect_daily_anomalies(daily, threshold=3.5, direction="both"):
    """Flag unusual days.

    Parameters
    ----------
    daily : Series
        Daily kWh from ``analysis.build_daily_series`` (NaN days are skipped).
    threshold : float
        Modified z-score cut-off. 3.5 is the standard choice; a higher value
        flags fewer, more extreme days.
    direction : {"both", "high", "low"}
        "high" = unusually high use, "low" = unusually low use.

    Returns
    -------
    DataFrame indexed by date with the columns energy_kwh, expected_kwh
    (group median), score, is_anomaly and direction. All days are returned;
    filter on ``is_anomaly`` to get just the anomalies.
    """

    values = daily.dropna()

    frame = values.to_frame("energy_kwh")

    keys = [
        values.index.month,
        (values.index.dayofweek >= 5).astype(int)
    ]

    median, score = _robust_scores(values, keys)

    frame["expected_kwh"] = median
    frame["score"] = score

    return _flag(frame, threshold, direction)


# --------------------------------------------------
# 3. HOURLY ANOMALIES
# --------------------------------------------------

def detect_hourly_anomalies(df, threshold=10.0, direction="both"):
    """Flag unusual hours.

    ``df`` is the hourly table (columns datetime, energy_kwh, is_complete).
    Only complete hours are used. Hourly use is far more spiky than daily
    use (a night-time heating cycle, or an oven plus a kettle, is a big jump
    from the median but perfectly normal), so the default cut-off is 10
    instead of 3.5. With 10, about 1.5% of hours are flagged on this data
    set; lower it to see more, raise it to see only the most extreme hours.

    Returns the same columns as ``detect_daily_anomalies``, indexed by
    datetime.
    """

    complete = df.loc[
        (df["is_complete"] == 1) & df["energy_kwh"].notna()
    ].set_index("datetime")

    values = complete["energy_kwh"]

    keys = [
        values.index.month,
        (values.index.dayofweek >= 5).astype(int),
        values.index.hour
    ]

    median, score = _robust_scores(values, keys)

    frame = values.to_frame("energy_kwh")

    frame["expected_kwh"] = median
    frame["score"] = score

    return _flag(frame, threshold, direction)


# --------------------------------------------------
# 4. DATA GAPS
# --------------------------------------------------

def find_data_gaps(hourly_df, min_hours=6):
    """List runs of consecutive incomplete hours (sensor or logging outages).

    Gaps are not electricity anomalies: during an outage the meter simply
    recorded nothing. Showing them next to the anomalies helps tell the two
    apart.

    Returns a DataFrame with gap_start, gap_end (last missing hour) and
    hours, longest gaps first.
    """

    data = hourly_df.sort_values("datetime")

    missing = data["is_complete"] != 1

    # Consecutive rows with the same missing/not-missing state share an id.
    run_id = (missing != missing.shift()).cumsum()

    gaps = (
        data[missing]
        .groupby(run_id[missing])["datetime"]
        .agg(gap_start="min", gap_end="max", hours="size")
    )

    gaps = gaps[gaps["hours"] >= min_hours]

    return (
        gaps.sort_values("hours", ascending=False)
        .reset_index(drop=True)
    )
