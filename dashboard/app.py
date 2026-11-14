import sqlite3
import sys
import textwrap

from pathlib import Path

import pandas as pd
import streamlit as st

# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = PROJECT_ROOT / "src"

DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "energy_v2.db"
)

sys.path.insert(0, str(SRC_DIR))


# ==========================================================
# IMPORTS
# ==========================================================

from components import (
    apply_custom_css,
    render_header,
    render_section_title,
    render_kpi_cards,
    render_footer
)

from charts import (
    hourly_consumption_chart,
    daily_consumption_chart,
    weekday_consumption_chart,
    monthly_consumption_chart,
    consumption_distribution_chart,
    daily_cost_chart,
    forecast_chart,
    backtest_chart,
    anomaly_chart,
    monthly_coverage_chart,
    monthly_completeness_chart
    
)

from database import load_hourly_data

from analysis import build_daily_series, kpi_summary

from forecasting import MODELS, compare_models, forecast_future

from anomaly_detection import (
    detect_daily_anomalies,
    detect_hourly_anomalies,
    find_data_gaps
)


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Energy Insight",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()


# ==========================================================
# DATABASE
# ==========================================================

@st.cache_data
def load_data():

    df = load_hourly_data()

    df["energy_kwh"] = pd.to_numeric(
        df["energy_kwh"],
        errors="coerce"
    )

    df["coverage_percent"] = pd.to_numeric(
        df["coverage_percent"],
        errors="coerce"
    )

    return df


try:

    hourly_df = load_data()

except Exception as error:

    st.error(f"Unable to load the energy database: {error}")
    st.stop()


# ==========================================================
# DATA PREPARATION
# ==========================================================

complete_df = hourly_df.loc[
    (hourly_df["is_complete"] == 1)
    & hourly_df["energy_kwh"].notna()
].copy()

if complete_df.empty:

    st.error("No complete hourly records are available.")
    st.stop()


# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.title("⚡ Energy Insight")
st.sidebar.caption("Household Energy Analytics")

st.sidebar.divider()

page_options = {
    "Dashboard": "Overview",
    "Consumption Analysis": "Consumption Analysis",
    "Cost Analysis": "Cost Analysis",
    "Forecast & Anomalies": "Forecast & Anomalies",
    "Data Explorer": "Data Explorer"
}

selected_page = st.sidebar.radio(
    "NAVIGATION",
    list(page_options.values())
)

st.sidebar.divider()
st.sidebar.subheader("FILTERS")

minimum_date = complete_df["datetime"].min().date()
maximum_date = complete_df["datetime"].max().date()

selected_dates = st.sidebar.date_input(
    "Select date range",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date
)

tariff = st.sidebar.number_input(
    "Electricity tariff (€/kWh)",
    min_value=0.01,
    max_value=2.00,
    value=0.25,
    step=0.01
)

if isinstance(selected_dates, (tuple, list)):

    if len(selected_dates) == 2:

        start_date, end_date = selected_dates

    elif len(selected_dates) == 1:

        start_date = selected_dates[0]
        end_date = selected_dates[0]

    else:

        start_date = minimum_date
        end_date = maximum_date

else:

    start_date = selected_dates
    end_date = selected_dates


# ==========================================================
# FILTER DATA
# ==========================================================

period_df = complete_df.loc[
    (complete_df["datetime"].dt.date >= start_date)
    & (complete_df["datetime"].dt.date <= end_date)
].copy()

if period_df.empty:

    st.warning("No complete data is available for this date range.")
    st.stop()


# ==========================================================
# KPI CALCULATIONS
# ==========================================================

kpis = kpi_summary(hourly_df, start_date, end_date, tariff)

total_energy = kpis["total_energy_kwh"]

average_daily = kpis["average_daily_kwh"]

peak_consumption = kpis["peak_hour_kwh"]

estimated_cost = kpis["estimated_cost"]

data_coverage = kpis["data_coverage_percent"]

# Fully observed days only: days with missing hours are NaN, not 0.
daily_energy = build_daily_series(period_df)


# ==========================================================
# HEADER
# ==========================================================


st.caption(
    f"Showing data from {start_date} to {end_date}"
)


# ==========================================================
# PAGE 1: OVERVIEW
# ==========================================================

if selected_page == "Overview":

    from components import render_hero

    render_hero()

    render_section_title(
        "Energy Overview",
        "A snapshot of household electricity consumption."
    )

    render_kpi_cards(
        total_energy=total_energy,
        average_daily=average_daily,
        peak_consumption=peak_consumption,
        estimated_cost=estimated_cost,
        data_coverage=data_coverage
    )

    st.divider()

    render_section_title(
        "Consumption Trends",
        "Explore how energy consumption changes over time."
    )

    left, right = st.columns(2)

    with left:

        st.plotly_chart(
            daily_consumption_chart(period_df),
            use_container_width=True
        )

    with right:

        st.plotly_chart(
            hourly_consumption_chart(period_df),
            use_container_width=True
        )

    left, right = st.columns(2)

    with left:

        st.plotly_chart(
            weekday_consumption_chart(period_df),
            use_container_width=True
        )

    with right:

        st.plotly_chart(
            monthly_consumption_chart(period_df),
            use_container_width=True
        )

    render_section_title(
        "Automated Consumption Insights",
        "Quick observations derived from the selected data."
    )

    insight_columns = st.columns(3)

    hourly_average = (
        period_df.assign(
            hour=period_df["datetime"].dt.hour
        )
        .groupby("hour")["energy_kwh"]
        .mean()
    )

    weekday_average = (
        period_df.assign(
            weekday=period_df["datetime"].dt.day_name()
        )
        .groupby("weekday")["energy_kwh"]
        .mean()
    )

    daily_totals = (
        period_df.set_index("datetime")["energy_kwh"]
        .resample("D")
        .sum()
    )

    with insight_columns[0]:

        st.metric(
            "Highest Usage Hour",
            f"{hourly_average.idxmax():02d}:00"
        )

    with insight_columns[1]:

        st.metric(
            "Highest Usage Weekday",
            weekday_average.idxmax()
        )

    with insight_columns[2]:

        st.metric(
            "Highest Consumption Day",
            daily_totals.idxmax().strftime("%d %b %Y")
        )


# ==========================================================
# PAGE 2: CONSUMPTION ANALYSIS
# ==========================================================

elif selected_page == "Consumption Analysis":

    render_section_title(
        "Consumption Analysis",
        "Detailed analysis of household energy usage patterns."
    )

    st.plotly_chart(
        daily_consumption_chart(period_df),
        use_container_width=True
    )

    left, right = st.columns(2)

    with left:

        st.plotly_chart(
            hourly_consumption_chart(period_df),
            use_container_width=True
        )

    with right:

        st.plotly_chart(
            weekday_consumption_chart(period_df),
            use_container_width=True
        )

    st.plotly_chart(
        monthly_consumption_chart(period_df),
        use_container_width=True
    )

    render_section_title(
        "Consumption Distribution",
        "Understand the distribution of hourly energy usage."
    )

    st.plotly_chart(
        consumption_distribution_chart(period_df),
        use_container_width=True
    )

    st.metric(
        "Maximum Hourly Consumption",
        f"{period_df['energy_kwh'].max():.3f} kWh"
    )


# ==========================================================
# PAGE 3: COST ANALYSIS
# ==========================================================

elif selected_page == "Cost Analysis":

    render_section_title(
        "Electricity Cost Analysis",
        "Estimated electricity expenses based on your selected tariff."
    )

    daily_cost = (daily_energy * tariff).dropna()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Estimated Cost",
            f"€{estimated_cost:,.2f}"
        )

    with col2:

        st.metric(
            "Average Daily Cost",
            f"€{daily_cost.mean():.2f}"
        )

    with col3:

        st.metric(
            "Highest Daily Cost",
            f"€{daily_cost.max():.2f}"
        )

    st.plotly_chart(
        daily_cost_chart(daily_cost, tariff),
        use_container_width=True
)

    st.caption(
        "Daily chart and breakdown include fully observed days only. "
        "Partially observed days are excluded."
)

    render_section_title(
        "Cost Breakdown",
        "Daily estimated electricity expenses."
    )

    cost_table = daily_cost.reset_index()

    cost_table.columns = ["Date", "Estimated Cost (€)"]

    cost_table["Date"] = cost_table["Date"].dt.date

    st.dataframe(
        cost_table,
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "The electricity tariff is user-configurable and illustrative. "
        "These estimates are not historical electricity bills."
    )


# ==========================================================
# PAGE 4: FORECAST & ANOMALIES
# ==========================================================

elif selected_page == "Forecast & Anomalies":

    render_section_title(
        "Forecast & Anomaly Detection",
        "Forecast upcoming consumption and spot unusual days or hours."
    )

    # The models learn from the whole dataset. The sidebar date range only
    # controls which anomalies and data gaps are displayed.
    daily_series = build_daily_series(complete_df)

    forecast_tab, anomaly_tab = st.tabs(["Forecast", "Anomalies"])


    # ---------- FORECAST TAB ----------

    with forecast_tab:

        horizon = st.slider(
            "Forecast horizon (days)",
            min_value=7,
            max_value=28,
            value=14
        )

        # Backtest every model on the most recent 52 weeks.
        comparison = compare_models(daily_series, horizon=horizon)

        method_names = list(MODELS)

        method = st.selectbox(
            "Forecasting method",
            method_names,
            index=method_names.index(comparison.loc[0, "Model"]),
            help="Defaults to the model with the lowest backtest error."
        )

        forecast_df, backtest_df = forecast_future(
            daily_series,
            method,
            horizon=horizon
        )

        selected = comparison[comparison["Model"] == method].iloc[0]

        forecast_total = forecast_df["forecast"].sum()

        k1, k2, k3, k4 = st.columns(4)

        k1.metric(
            f"Expected Energy (next {horizon} days)",
            f"{forecast_total:,.1f} kWh"
        )

        k2.metric(
            "Expected Daily Average",
            f"{forecast_df['forecast'].mean():.1f} kWh"
        )

        k3.metric(
            "Estimated Cost",
            f"€{forecast_total * tariff:,.2f}"
        )

        k4.metric(
            "Typical Error (MAE)",
            f"±{selected['MAE (kWh/day)']:.1f} kWh/day"
        )

        st.plotly_chart(
            forecast_chart(forecast_df, history=daily_series),
            use_container_width=True
        )

        st.caption(
            f"The forecast starts on "
            f"{forecast_df['date'].min().strftime('%d %b %Y')}, the day after "
            f"the last complete observation in this dataset. It demonstrates "
            f"how the method performs; it is not a prediction for today's date."
        )

        render_section_title(
            "How accurate is each model?",
            "Each model is tested on the last 52 weeks: it only sees data "
            f"from before each test block and must predict the next {horizon} "
            "days. Lower error is better."
        )

        st.dataframe(
            comparison,
            use_container_width=True,
            hide_index=True,
            column_config={
                "MAE (kWh/day)": st.column_config.NumberColumn(format="%.2f"),
                "RMSE (kWh/day)": st.column_config.NumberColumn(format="%.2f"),
                "MAPE (%)": st.column_config.NumberColumn(format="%.1f"),
                "Improvement vs naive (%)":
                    st.column_config.NumberColumn(format="%+.1f")
            }
        )

        with st.expander("Backtest chart: forecast vs what really happened"):

            st.plotly_chart(
                backtest_chart(backtest_df),
                use_container_width=True
            )

        with st.expander("How do these forecasts work?"):

            st.markdown(
                """
                - **Naive**: every future day equals the last known day.
                - **Moving average**: every future day equals the average of
                  the last 7 (or 14) known days.
                - **Seasonal naive / seasonal average**: a future day equals
                  the same weekday last week (or the average of the same
                  weekday over the last 4 weeks).
                - **Prediction range**: taken from the model's own backtest
                  errors, so about 80% of past days fell inside it.
                - **Why simple models?** In this household the weekday
                  pattern is weak compared with day-to-day variation, so
                  models that follow the *recent level* usually beat the
                  weekday models. The comparison table shows this directly.
                """
            )


    # ---------- ANOMALIES TAB ----------

    with anomaly_tab:

        a1, a2, a3 = st.columns(3)

        level = a1.radio(
            "Detect anomalies by",
            ["Day", "Hour"],
            horizontal=True
        )

        direction_label = a2.selectbox(
            "Direction",
            ["Both", "Unusually high", "Unusually low"]
        )

        direction = {
            "Both": "both",
            "Unusually high": "high",
            "Unusually low": "low"
        }[direction_label]

        if level == "Day":
            slider_min, slider_max, slider_default = 2.0, 8.0, 3.5
        else:
            slider_min, slider_max, slider_default = 3.0, 30.0, 10.0

        threshold = a3.slider(
            "Sensitivity threshold",
            min_value=slider_min,
            max_value=slider_max,
            value=slider_default,
            step=0.5,
            key=f"anomaly_threshold_{level}",
            help="Higher value = fewer, more extreme anomalies."
        )

        if level == "Day":
            frame = detect_daily_anomalies(daily_series, threshold, direction)
        else:
            frame = detect_hourly_anomalies(hourly_df, threshold, direction)

        # Show only the period chosen in the sidebar.
        period_frame = frame[
            (frame.index >= pd.Timestamp(start_date)) &
            (frame.index < pd.Timestamp(end_date) + pd.Timedelta(days=1))
        ]

        anomalies = period_frame[period_frame["is_anomaly"]]

        unit = "days" if level == "Day" else "hours"

        m1, m2, m3 = st.columns(3)

        m1.metric(f"Flagged {unit.capitalize()}", f"{len(anomalies):,}")

        m2.metric(
            f"Share of {unit}",
            f"{len(anomalies) / max(len(period_frame), 1) * 100:.1f}%"
        )

        if anomalies.empty:

            m3.metric("Strongest Anomaly", "-")

        else:

            strongest = anomalies["score"].abs().idxmax()

            m3.metric(
                "Strongest Anomaly",
                strongest.strftime(
                    "%d %b %Y" if level == "Day" else "%d %b %Y %H:00"
                ),
                f"{anomalies.loc[strongest, 'energy_kwh']:.2f} kWh "
                f"(expected {anomalies.loc[strongest, 'expected_kwh']:.2f})",
                delta_color="off"
            )

        st.plotly_chart(
            anomaly_chart(period_frame, hourly=(level == "Hour")),
            use_container_width=True
        )

        if not anomalies.empty:

            table = (
                anomalies
                .assign(abs_score=anomalies["score"].abs())
                .sort_values("abs_score", ascending=False)
                .reset_index()
                [[anomalies.index.name, "energy_kwh", "expected_kwh",
                  "score", "direction"]]
            )

            table.columns = [
                "Date" if level == "Day" else "Date & Hour",
                "Energy (kWh)",
                "Expected (kWh)",
                "Score",
                "Type"
            ]

            render_section_title("Flagged records (strongest first)")

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Energy (kWh)": st.column_config.NumberColumn(format="%.2f"),
                    "Expected (kWh)": st.column_config.NumberColumn(format="%.2f"),
                    "Score": st.column_config.NumberColumn(format="%.1f")
                }
            )

            st.download_button(
                label="Download anomalies as CSV",
                data=table.to_csv(index=False).encode("utf-8"),
                file_name=f"energy_anomalies_{level.lower()}.csv",
                mime="text/csv"
            )

        with st.expander("Data gaps (meter outages, not anomalies)"):

            gaps = find_data_gaps(hourly_df, min_hours=6)

            gaps = gaps[
                (gaps["gap_end"] >= pd.Timestamp(start_date)) &
                (gaps["gap_start"] <
                 pd.Timestamp(end_date) + pd.Timedelta(days=1))
            ]

            st.caption(
                "Stretches of at least 6 hours without a complete reading. "
                "These days are left out of the daily analysis, so they appear "
                "as breaks in the chart rather than as zero consumption."
            )

            if gaps.empty:
                st.info("No gaps of 6 hours or more in the selected period.")
            else:
                st.dataframe(
                    gaps.rename(columns={
                        "gap_start": "First missing hour",
                        "gap_end": "Last missing hour",
                        "hours": "Hours missing"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

        with st.expander("How are anomalies detected?"):

            st.markdown(
                """
                Each value is compared only with **similar** values: the same
                month and day type (weekday or weekend), and for hourly data
                also the same hour of the day. This stops ordinary winter
                evenings from being flagged.

                The comparison uses the **modified z-score**
                `(value - median) / (1.4826 x MAD)`. Median and MAD (median
                absolute deviation) are robust: a few extreme days do not
                distort the baseline. A score beyond +/-3.5 is the standard
                cut-off for daily data. Hourly data is much spikier, so its
                default is 10.

                **Limits:** an anomaly is only statistically unusual. It can
                be a holiday, a party, a faulty appliance or a measurement
                problem, and the data alone cannot tell which. A long unusual
                period (for example a month-long holiday) also shifts its own
                baseline and may not be flagged.
                """
            )


# ==========================================================
# PAGE 5: DATA EXPLORER
# ==========================================================

# ==========================================================
# PAGE 5: DATA EXPLORER
# ==========================================================

elif selected_page == "Data Explorer":

    render_section_title(
        "Data Explorer",
        "Explore dataset health, data quality and hourly observations."
    )

    # ------------------------------------------------------
    # 1. DATASET HEALTH — ENTIRE DATASET
    # ------------------------------------------------------

    st.markdown("### Dataset Health")

    st.caption(
        "These statistics describe the entire processed dataset, "
        "not just the selected date range."
    )

    total_hours = len(hourly_df)

    complete_hours = int(
        (hourly_df["is_complete"] == 1).sum()
    )

    incomplete_hours = total_hours - complete_hours

    average_coverage = hourly_df["coverage_percent"].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Hours",
        f"{total_hours:,}"
    )

    col2.metric(
        "Complete Hours",
        f"{complete_hours:,}"
    )

    col3.metric(
        "Incomplete Hours",
        f"{incomplete_hours:,}"
    )

    col4.metric(
        "Average Coverage",
        f"{average_coverage:.2f}%"
    )

    st.divider()

    # ------------------------------------------------------
    # 2. FILTER DATA FOR THE SELECTED DATE RANGE
    # ------------------------------------------------------

    st.markdown("### Selected Period")

    st.caption(
        f"Currently exploring {start_date} to {end_date}."
    )

    explorer_df = hourly_df.loc[
        (hourly_df["datetime"].dt.date >= start_date)
        & (hourly_df["datetime"].dt.date <= end_date)
    ].copy()

    if explorer_df.empty:

        st.warning(
            "No records are available for the selected date range."
        )

    else:

        # --------------------------------------------------
        # 3. DATA QUALITY VISUALISATIONS
        # --------------------------------------------------

        render_section_title(
            "Data Quality Trends",
            "Understand how data completeness changes over time."
        )

        left, right = st.columns(2)

        with left:

            st.plotly_chart(
                monthly_coverage_chart(explorer_df),
                use_container_width=True
            )

        with right:

            st.plotly_chart(
                monthly_completeness_chart(explorer_df),
                use_container_width=True
            )

        # --------------------------------------------------
        # 4. SELECTED PERIOD QUALITY SUMMARY
        # --------------------------------------------------

        period_total = len(explorer_df)

        period_complete = int(
            (explorer_df["is_complete"] == 1).sum()
        )

        period_incomplete = period_total - period_complete

        period_coverage = explorer_df["coverage_percent"].mean()

        st.markdown("### Selected Period Quality Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Records",
            f"{period_total:,}"
        )

        col2.metric(
            "Complete Records",
            f"{period_complete:,}"
        )

        col3.metric(
            "Incomplete Records",
            f"{period_incomplete:,}"
        )

        col4.metric(
            "Average Coverage",
            f"{period_coverage:.2f}%"
        )

        st.divider()

        # --------------------------------------------------
        # 5. HOURLY DATA TABLE
        # --------------------------------------------------

        render_section_title(
            "Hourly Dataset",
            "Inspect individual hourly observations."
        )

        include_incomplete = st.checkbox(
            "Include incomplete hourly records",
            value=False
        )

        if include_incomplete:

            display_df = explorer_df.copy()

        else:

            display_df = explorer_df.loc[
                (explorer_df["is_complete"] == 1)
                & explorer_df["energy_kwh"].notna()
            ].copy()

        st.caption(
            f"Displaying {len(display_df):,} records."
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------------------
        # 6. CSV EXPORT
        # --------------------------------------------------

        csv_data = display_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Selected Data (CSV)",
            data=csv_data,
            file_name="energy_insight_selected_data.csv",
            mime="text/csv"
        )

        st.divider()

        # --------------------------------------------------
        # 7. DATA QUALITY RECORDS
        # --------------------------------------------------

        render_section_title(
            "Data Quality Records",
            "Inspect the completeness of individual hourly readings."
        )

        quality_columns = [
            "datetime",
            "valid_minutes",
            "total_records",
            "coverage_percent",
            "is_complete"
        ]

        available_columns = [
            column for column in quality_columns
            if column in explorer_df.columns
        ]

        quality_df = explorer_df[available_columns].copy()

        st.dataframe(
            quality_df,
            use_container_width=True,
            hide_index=True
        )



# ==========================================================
# FOOTER
# ==========================================================

render_footer()