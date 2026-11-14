import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ==========================================================
# GLOBAL CHART THEME
# ==========================================================

BACKGROUND = "#111C2E"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
GRID = "#26364D"
ACCENT = "#38BDF8"
GREEN = "#34D399"


def style_chart(fig):

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(
            family="Inter, Segoe UI, sans-serif",
            color=TEXT
        ),
        margin=dict(l=30, r=30, t=55, b=30),
        title_font=dict(size=17, color=TEXT),
        hoverlabel=dict(
            bgcolor="#172438",
            font_color=TEXT
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font_color=MUTED
        )
    )

    fig.update_xaxes(
        gridcolor=GRID,
        zerolinecolor=GRID
    )

    fig.update_yaxes(
        gridcolor=GRID,
        zerolinecolor=GRID
    )

    return fig


# ==========================================================
# HOURLY CONSUMPTION
# ==========================================================

def hourly_consumption_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()

    data["datetime"] = pd.to_datetime(data["datetime"])

    data["hour"] = data["datetime"].dt.hour

    hourly = (
        data.groupby("hour")["energy_kwh"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        hourly,
        x="hour",
        y="energy_kwh",
        title="Average Energy Consumption by Hour",
        labels={
            "hour": "Hour of Day",
            "energy_kwh": "Average Energy (kWh)"
        }
    )

    fig.update_traces(
        marker_color=ACCENT,
        hovertemplate="Hour: %{x}:00<br>Energy: %{y:.3f} kWh"
    )

    return style_chart(fig)


# ==========================================================
# DAILY CONSUMPTION
# ==========================================================

def daily_consumption_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()

    data["datetime"] = pd.to_datetime(data["datetime"])

    daily = (
        data.set_index("datetime")["energy_kwh"]
        .resample("D")
        .sum()
        .reset_index()
    )

    fig = px.line(
        daily,
        x="datetime",
        y="energy_kwh",
        title="Daily Energy Consumption",
        labels={
            "datetime": "Date",
            "energy_kwh": "Energy (kWh)"
        }
    )

    fig.update_traces(
        line=dict(color=ACCENT, width=2),
        fill="tozeroy",
        fillcolor="rgba(56,189,248,0.08)"
    )

    return style_chart(fig)


# ==========================================================
# WEEKDAY CONSUMPTION
# ==========================================================

def weekday_consumption_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()

    data["datetime"] = pd.to_datetime(data["datetime"])

    data["weekday"] = data["datetime"].dt.day_name()

    order = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    weekday = (
        data.groupby("weekday")["energy_kwh"]
        .mean()
        .reindex(order)
        .reset_index()
    )

    fig = px.bar(
        weekday,
        x="weekday",
        y="energy_kwh",
        title="Average Consumption by Weekday",
        category_orders={"weekday": order},
        labels={
            "weekday": "Weekday",
            "energy_kwh": "Average Energy (kWh)"
        }
    )

    fig.update_traces(marker_color=GREEN)

    return style_chart(fig)


# ==========================================================
# MONTHLY CONSUMPTION
# ==========================================================
# ==================================================
# MONTHLY CONSUMPTION
# ==================================================

def monthly_consumption_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()

    data["datetime"] = pd.to_datetime(data["datetime"])

    # Identify the first and last dates in the selected data.
    first_date = data["datetime"].min().date()
    last_date = data["datetime"].max().date()

    # Calculate total energy consumption for each calendar month.
    monthly = (
        data.set_index("datetime")["energy_kwh"]
        .resample("MS")
        .sum()
        .reset_index()
    )

    # Identify whether each displayed month is partially selected.
    partial_months = []

    for month in monthly["datetime"]:

        month_start = month.date()
        month_end = (month + pd.offsets.MonthEnd(0)).date()

        is_partial = (
            (month_start == monthly["datetime"].iloc[0].date()
             and first_date > month_start)
            or
            (month_start == monthly["datetime"].iloc[-1].date()
             and last_date < month_end)
        )

        partial_months.append(is_partial)

    monthly["month_label"] = monthly["datetime"].dt.strftime("%b %Y")

    monthly["month_label"] = [
        label + (" *" if partial else "")
        for label, partial in zip(
            monthly["month_label"],
            partial_months
        )
    ]

    has_partial_month = any(partial_months)

    # A single month is better displayed as a point than one oversized bar.
    if len(monthly) == 1:

        title = (
            "Selected-Month Energy Consumption (Partial Month)"
            if has_partial_month
            else "Monthly Energy Consumption"
        )

        fig = px.line(
            monthly,
            x="month_label",
            y="energy_kwh",
            markers=True,
            title=title,
            labels={
                "month_label": "Month",
                "energy_kwh": "Energy Consumption (kWh)"
            }
        )

        fig.update_traces(
            line=dict(color=ACCENT, width=2),
            marker=dict(size=11, color=ACCENT),
            hovertemplate=(
                "Month: %{x}<br>"
                "Energy: %{y:,.2f} kWh"
                "<extra></extra>"
            )
        )

    else:

        title = (
            "Monthly Energy Consumption (* Partial Month)"
            if has_partial_month
            else "Monthly Energy Consumption"
        )

        fig = px.bar(
            monthly,
            x="month_label",
            y="energy_kwh",
            title=title,
            labels={
                "month_label": "Month",
                "energy_kwh": "Energy Consumption (kWh)"
            }
        )

        fig.update_traces(
            marker_color=ACCENT,
            hovertemplate=(
                "Month: %{x}<br>"
                "Energy: %{y:,.2f} kWh"
                "<extra></extra>"
            )
        )

    return style_chart(fig)


# ==========================================================
# CONSUMPTION DISTRIBUTION
# ==========================================================

def consumption_distribution_chart(df):

    if df.empty:
        return go.Figure()

    fig = px.histogram(
        df,
        x="energy_kwh",
        nbins=40,
        title="Distribution of Hourly Energy Consumption",
        labels={
            "energy_kwh": "Energy (kWh)",
            "count": "Number of Hours"
        }
    )

    fig.update_traces(
        marker_color=ACCENT,
        opacity=0.8
    )

    return style_chart(fig)


# ==========================================================
# DAILY COST
# ==========================================================
def daily_cost_chart(daily_series, tariff):

    if daily_series.empty:
        return go.Figure()

    # Use the same daily values as the Cost Breakdown table.
    daily = daily_series.rename("energy_kwh").reset_index()

    daily.columns = ["datetime", "energy_kwh"]

    daily["cost"] = daily["energy_kwh"] * tariff

    fig = px.line(
        daily,
        x="datetime",
        y="cost",
        markers=True,
        title="Estimated Daily Electricity Cost",
        labels={
            "datetime": "Date",
            "cost": "Estimated Cost (€)"
        }
    )

    fig.update_traces(
        line=dict(color=GREEN, width=2),
        marker=dict(size=5),
        hovertemplate=(
            "Date: %{x|%d %b %Y}<br>"
            "Estimated Cost: €%{y:,.2f}"
            "<extra></extra>"
        )
    )

    return style_chart(fig)


# ==================================================
# DATA QUALITY: MONTHLY COVERAGE
# ==================================================

def monthly_coverage_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()
    data["datetime"] = pd.to_datetime(data["datetime"])

    monthly = (
        data.set_index("datetime")["coverage_percent"]
        .resample("MS")
        .mean()
        .reset_index()
    )

    fig = px.line(
        monthly,
        x="datetime",
        y="coverage_percent",
        markers=True,
        title="Monthly Data Coverage",
        labels={
            "datetime": "Month",
            "coverage_percent": "Average Coverage (%)"
        }
    )

    fig.update_traces(
        line=dict(color=ACCENT, width=2),
        marker=dict(size=6),
        hovertemplate=(
            "Month: %{x|%b %Y}<br>"
            "Average Coverage: %{y:.2f}%"
            "<extra></extra>"
        )
    )

    fig.update_yaxes(range=[0, 105])

    return style_chart(fig)


# ==================================================
# DATA QUALITY: COMPLETE VS INCOMPLETE HOURS
# ==================================================

def monthly_completeness_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()
    data["datetime"] = pd.to_datetime(data["datetime"])

    data["status"] = data["is_complete"].map({
        1: "Complete",
        0: "Incomplete"
    })

    monthly = (
        data.groupby([
            pd.Grouper(key="datetime", freq="MS"),
            "status"
        ])
        .size()
        .reset_index(name="hours")
    )

    fig = px.bar(
        monthly,
        x="datetime",
        y="hours",
        color="status",
        barmode="group",
        title="Complete vs Incomplete Hours",
        labels={
            "datetime": "Month",
            "hours": "Number of Hours",
            "status": "Data Status"
        },
        color_discrete_map={
            "Complete": GREEN,
            "Incomplete": "#F87171"
        }
    )

    fig.update_traces(
        hovertemplate=(
            "Month: %{x|%b %Y}<br>"
            "Status: %{fullData.name}<br>"
            "Hours: %{y:,}"
            "<extra></extra>"
        )
    )

    return style_chart(fig)


# ==========================================================
# FORECAST
# ==========================================================
FORECAST_COLOR = "#F59E0B"
HIGH_COLOR = "#F87171"
LOW_COLOR = "#60A5FA"

LEGEND_TOP_RIGHT = dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
)


def forecast_chart(forecast_df, history=None, history_days=60):
    """Forecast with its prediction range.

    ``history`` (optional) is the daily kWh Series that precedes the
    forecast. Passing it shows the recent actual values next to the
    forecast, so the chart can be judged at a glance.
    """

    if forecast_df.empty:
        return go.Figure()

    fig = go.Figure()

    if history is not None and len(history) > 0:

        recent = history.loc[
            history.index >= history.index[-1] - pd.Timedelta(days=history_days)
        ]

        fig.add_trace(
            go.Scatter(
                x=recent.index,
                y=recent.values,
                mode="lines",
                name="Actual daily use",
                line=dict(color=ACCENT, width=2)
            )
        )

    if {"lower", "upper"}.issubset(forecast_df.columns):

        # Invisible upper line, then the lower line filled up to it.
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["upper"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["lower"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(245,158,11,0.20)",
                name="80% prediction range",
                hoverinfo="skip"
            )
        )

    fig.add_trace(
        go.Scatter(
            x=forecast_df["date"],
            y=forecast_df["forecast"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color=FORECAST_COLOR, width=3, dash="dash"),
            marker=dict(size=6)
        )
    )

    fig.update_layout(
        title="Daily Energy Forecast",
        xaxis_title="Date",
        yaxis_title="Energy (kWh per day)",
        hovermode="x unified"
    )

    style_chart(fig)

    fig.update_layout(legend=LEGEND_TOP_RIGHT)

    return fig


# ==========================================================
# BACKTEST
# ==========================================================

def backtest_chart(backtest_df, days=84):
    """Forecast vs what really happened on days the model never saw."""

    if backtest_df.empty:
        return go.Figure()

    data = backtest_df

    if "date" in data.columns:
        x_all = data["date"]
    else:
        x_all = data.index

    keep = x_all > x_all.max() - pd.Timedelta(days=days)

    data = data.loc[keep]

    x = data["date"] if "date" in data.columns else data.index

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=data["actual"],
            name="Actual",
            mode="lines",
            line=dict(color=ACCENT, width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=data["forecast"],
            name="Forecast made without seeing these days",
            mode="lines",
            line=dict(color=FORECAST_COLOR, width=2, dash="dash")
        )
    )

    fig.update_layout(
        title=f"Backtest: last {days} days",
        xaxis_title="Date",
        yaxis_title="Energy (kWh per day)",
        hovermode="x unified"
    )

    style_chart(fig)

    fig.update_layout(legend=LEGEND_TOP_RIGHT)

    return fig


# ==========================================================
# ANOMALIES
# ==========================================================

def anomaly_chart(anomaly_df, hourly=False):
    """Consumption over time with the flagged anomalies highlighted.

    ``anomaly_df`` comes from detect_daily_anomalies or
    detect_hourly_anomalies. Use ``hourly=True`` for the hourly version,
    which draws ~34,000 points with WebGL to stay fast.
    """

    if anomaly_df.empty:
        return go.Figure()

    fig = go.Figure()

    if hourly:

        fig.add_trace(
            go.Scattergl(
                x=anomaly_df.index,
                y=anomaly_df["energy_kwh"],
                mode="markers",
                name="All hours",
                marker=dict(size=3, color=MUTED, opacity=0.35),
                hoverinfo="skip"
            )
        )

        unit, y_title = "hour", "Energy (kWh per hour)"

    else:

        # asfreq inserts missing days as NaN, so outages appear as breaks
        # in the line instead of being joined together.
        full = anomaly_df.asfreq("D")

        fig.add_trace(
            go.Scatter(
                x=full.index,
                y=full["energy_kwh"],
                mode="lines",
                name="Daily use",
                line=dict(color=ACCENT, width=1.5)
            )
        )

        unit, y_title = "day", "Energy (kWh per day)"

    for direction, color in [("high", HIGH_COLOR), ("low", LOW_COLOR)]:

        flagged = anomaly_df[anomaly_df["direction"] == direction]

        if flagged.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=flagged.index,
                y=flagged["energy_kwh"],
                mode="markers",
                name=f"Unusually {direction} {unit}",
                marker=dict(
                    size=9,
                    color=color,
                    line=dict(width=1, color="white")
                ),
                customdata=flagged[["expected_kwh", "score"]].to_numpy(),
                hovertemplate=(
                    "%{x}<br>"
                    "Actual: %{y:.2f} kWh<br>"
                    "Expected: %{customdata[0]:.2f} kWh<br>"
                    "Score: %{customdata[1]:.1f}<extra></extra>"
                )
            )
        )

    fig.update_layout(
        title="Detected Anomalies",
        xaxis_title="Date",
        yaxis_title=y_title
    )

    style_chart(fig)

    fig.update_layout(legend=LEGEND_TOP_RIGHT)

    return fig

# ==========================================================
# DATA QUALITY CHARTS
# ==========================================================

def monthly_coverage_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()

    data["datetime"] = pd.to_datetime(data["datetime"])

    monthly = (
        data.set_index("datetime")["coverage_percent"]
        .resample("MS")
        .mean()
        .reset_index()
    )

    fig = px.line(
        monthly,
        x="datetime",
        y="coverage_percent",
        markers=True,
        title="Monthly Data Coverage",
        labels={
            "datetime": "Month",
            "coverage_percent": "Average Coverage (%)"
        }
    )

    fig.update_traces(
        line=dict(color=ACCENT, width=2),
        marker=dict(size=6),
        hovertemplate=(
            "Month: %{x|%b %Y}<br>"
            "Average Coverage: %{y:.2f}%"
            "<extra></extra>"
        )
    )

    fig.update_yaxes(range=[0, 105])

    return style_chart(fig)


def monthly_completeness_chart(df):

    if df.empty:
        return go.Figure()

    data = df.copy()

    data["datetime"] = pd.to_datetime(data["datetime"])

    data["status"] = data["is_complete"].map({
        1: "Complete",
        0: "Incomplete"
    })

    monthly = (
        data.groupby([
            pd.Grouper(key="datetime", freq="MS"),
            "status"
        ])
        .size()
        .reset_index(name="hours")
    )

    fig = px.bar(
        monthly,
        x="datetime",
        y="hours",
        color="status",
        barmode="group",
        title="Complete vs Incomplete Hours",
        labels={
            "datetime": "Month",
            "hours": "Number of Hours",
            "status": "Data Status"
        },
        color_discrete_map={
            "Complete": GREEN,
            "Incomplete": "#F87171"
        }
    )

    fig.update_traces(
        hovertemplate=(
            "Month: %{x|%b %Y}<br>"
            "Status: %{fullData.name}<br>"
            "Hours: %{y:,}"
            "<extra></extra>"
        )
    )

    return style_chart(fig)
