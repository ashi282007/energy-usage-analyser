"""Simple, explainable forecasting for daily household electricity use.

Five baseline models are compared with a rolling backtest:

1. Naive                    - every day looks like the last known day.
2. Moving average (7 days)  - every day looks like the last 7 known days.
3. Moving average (14 days) - same idea with a longer memory.
4. Seasonal naive           - a day looks like the same weekday last week.
5. Seasonal average (4 wk)  - a day looks like the average of the same
                              weekday over the last four weeks.

The best model is the one with the lowest error on days it has not seen.
In this household the weekly pattern is weak compared with the day-to-day
noise, so models that follow the *recent level* tend to beat the weekday
models. That is a finding from the data, not something assumed in advance.
"""

from functools import partial

import numpy as np
import pandas as pd

DAY = pd.Timedelta(days=1)
WEEK = pd.Timedelta(days=7)


# --------------------------------------------------
# 1. MODELS
# --------------------------------------------------
# Every model has the same signature:
#     model(train, horizon) -> numpy array with `horizon` values
# `train` is a daily Series (NaN = unknown day). The forecast covers the
# `horizon` days right after the last date in `train`.


def _forecast_dates(train, horizon):
    return pd.date_range(train.index[-1] + DAY, periods=horizon, freq="D")


def _past_same_weekdays(train, target_date, n_weeks):
    """Up to n_weeks known values of the same weekday before target_date.

    Steps back in whole weeks from the target day until it lands inside the
    training window, then keeps collecting earlier weeks (skipping NaN days).
    """

    d = target_date - WEEK

    while d > train.index[-1]:
        d -= WEEK

    values = []

    while len(values) < n_weeks and d >= train.index[0]:
        value = train.get(d, np.nan)

        if not np.isnan(value):
            values.append(value)

        d -= WEEK

    return values


def naive_last_value(train, horizon):
    """Repeat the last known daily total."""

    last_known = train.dropna().iloc[-1]

    return np.full(horizon, last_known, dtype=float)


def moving_average(train, horizon, days=7):
    """Repeat the average of the last `days` known daily totals."""

    level = train.dropna().iloc[-days:].mean()

    return np.full(horizon, level, dtype=float)


def seasonal_average(train, horizon, weeks=4):
    """Average of the same weekday over the last `weeks` weeks."""

    fallback = train.dropna().iloc[-28:].mean()

    forecast = []

    for target in _forecast_dates(train, horizon):
        values = _past_same_weekdays(train, target, weeks)
        forecast.append(np.mean(values) if values else fallback)

    return np.array(forecast, dtype=float)


def seasonal_naive(train, horizon):
    """Value of the same weekday one week earlier."""

    return seasonal_average(train, horizon, weeks=1)


MODELS = {
    "Naive (last value)": naive_last_value,
    "Moving average (last 7 days)": partial(moving_average, days=7),
    "Moving average (last 14 days)": partial(moving_average, days=14),
    "Seasonal naive (same weekday, last week)": seasonal_naive,
    "Seasonal average (same weekday, last 4 weeks)": seasonal_average,
}

BASELINE_NAME = "Naive (last value)"


# --------------------------------------------------
# 2. BACKTEST
# --------------------------------------------------

def backtest(series, model, horizon=7, test_days=364):
    """Test a model on the most recent data it never saw.

    The most recent ``test_days`` days (default: 52 weeks, so every season
    is covered) are cut into blocks of ``horizon`` days. For each block the
    model only gets the history before the block and must forecast the whole
    block. Days with an unknown actual value (NaN) are skipped.

    Returns a DataFrame with columns: date, actual, forecast, fold.
    """

    n_folds = max(1, test_days // horizon)

    last_date = series.index[-1]

    frames = []

    for fold in range(n_folds, 0, -1):

        test_end = last_date - horizon * (fold - 1) * DAY
        test_start = test_end - (horizon - 1) * DAY

        train = series.loc[: test_start - DAY]

        if train.dropna().empty:
            continue

        actual = series.loc[test_start:test_end]

        frames.append(
            pd.DataFrame({
                "date": actual.index,
                "actual": actual.values,
                "forecast": model(train, horizon),
                "fold": n_folds - fold + 1
            })
        )

    result = pd.concat(frames, ignore_index=True)

    return result.dropna(subset=["actual"]).reset_index(drop=True)


def error_metrics(bt):
    """MAE, RMSE and MAPE of a backtest result."""

    error = bt["actual"] - bt["forecast"]

    return {
        "MAE (kWh/day)": error.abs().mean(),
        "RMSE (kWh/day)": float(np.sqrt((error ** 2).mean())),
        "MAPE (%)": (error.abs() / bt["actual"]).mean() * 100
    }


def compare_models(series, horizon=7, test_days=364):
    """Backtest every model and return one comparison table (best first).

    ``Improvement vs naive (%)`` says how much lower the MAE is than the
    naive baseline. A model that cannot beat the naive baseline is not
    adding anything.
    """

    rows = []

    for name, model in MODELS.items():

        bt = backtest(series, model, horizon, test_days)

        rows.append({"Model": name, **error_metrics(bt)})

    table = pd.DataFrame(rows)

    baseline_mae = table.loc[
        table["Model"] == BASELINE_NAME, "MAE (kWh/day)"
    ].iloc[0]

    table["Improvement vs naive (%)"] = (
        (1 - table["MAE (kWh/day)"] / baseline_mae) * 100
    )

    return table.sort_values("MAE (kWh/day)").reset_index(drop=True)


# --------------------------------------------------
# 3. FORECAST
# --------------------------------------------------

def forecast_future(series, method, horizon=14, test_days=364, interval=0.8):
    """Forecast the ``horizon`` days after the end of ``series``.

    The prediction range comes from the model's own backtest errors: the
    gap between actual and forecast on past days. With ``interval=0.8``,
    about 80% of past days fell inside the range.

    Returns (forecast_df, backtest_df). forecast_df has the columns
    date, forecast, lower and upper.
    """

    model = MODELS[method]

    bt = backtest(series, model, horizon, test_days)

    error = bt["actual"] - bt["forecast"]

    tail = (1 - interval) / 2

    low_error = error.quantile(tail)
    high_error = error.quantile(1 - tail)

    point = model(series, horizon)

    forecast_df = pd.DataFrame({
        "date": _forecast_dates(series, horizon),
        "forecast": point,
        "lower": np.clip(point + low_error, 0, None),
        "upper": point + high_error
    })

    return forecast_df, bt
