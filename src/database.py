"""
Centralised SQLite database management for Energy Insight.

Responsibilities
-----------------
1. Establish database connections.
2. Load hourly electricity consumption data.
3. Generate daily electricity consumption data.
4. Retrieve database summaries.
5. Retrieve available date ranges.
6. Provide basic database integrity information.

Database:
    data/processed/energy_v2.db

Table:
    hourly_usage
"""

import sqlite3
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. DATABASE CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "energy_v2.db"
)

TABLE_NAME = "hourly_usage"


# --------------------------------------------------
# 2. DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    """
    Create and return a SQLite database connection.

    Raises
    ------
    FileNotFoundError
        If the database does not exist.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    return sqlite3.connect(DB_PATH)


# --------------------------------------------------
# 3. LOAD HOURLY DATA
# --------------------------------------------------

def load_hourly_data(
    start_date=None,
    end_date=None,
    complete_only=False
):
    """
    Load hourly electricity consumption records.

    Parameters
    ----------
    start_date : str or None
        Optional starting date.

    end_date : str or None
        Optional ending date.

    complete_only : bool
        If True, return only fully observed hours.

    Returns
    -------
    DataFrame
        Hourly electricity consumption records.
    """

    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"

    params = []

    if start_date is not None:
        query += " AND datetime >= ?"
        params.append(str(start_date))

    if end_date is not None:
        query += " AND datetime < ?"
        params.append(str(end_date))

    if complete_only:
        query += """
            AND is_complete = 1
            AND energy_kwh IS NOT NULL
        """

    query += " ORDER BY datetime"

    with get_connection() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params=params
        )

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="coerce"
    )

    return df


# --------------------------------------------------
# 4. LOAD DAILY DATA
# --------------------------------------------------

def load_daily_data(min_hours=24):
    """
    Generate daily electricity consumption from hourly records.

    Uses the shared build_daily_series function so that
    the definition of a usable day stays consistent.
    """

    from analysis import build_daily_series

    hourly_df = load_hourly_data()

    return build_daily_series(
        hourly_df,
        min_hours=min_hours
    )


# --------------------------------------------------
# 5. DATABASE SUMMARY
# --------------------------------------------------

def get_data_summary():
    """
    Return basic statistics about the hourly database.
    """

    query = f"""
        SELECT
            COUNT(*) AS total_hours,

            SUM(
                CASE
                    WHEN is_complete = 1
                    THEN 1 ELSE 0
                END
            ) AS complete_hours,

            SUM(
                CASE
                    WHEN is_complete = 0
                    THEN 1 ELSE 0
                END
            ) AS incomplete_hours,

            AVG(coverage_percent) AS average_coverage,

            MIN(datetime) AS first_record,

            MAX(datetime) AS last_record,

            MIN(energy_kwh) AS minimum_energy,

            MAX(energy_kwh) AS maximum_energy,

            AVG(energy_kwh) AS average_energy

        FROM {TABLE_NAME}
    """

    with get_connection() as conn:
        summary = pd.read_sql_query(
            query,
            conn
        )

    return summary.iloc[0].to_dict()


# --------------------------------------------------
# 6. AVAILABLE DATE RANGE
# --------------------------------------------------

def get_date_range():
    """
    Return the first and last available timestamps.
    """

    query = f"""
        SELECT
            MIN(datetime) AS start_date,
            MAX(datetime) AS end_date
        FROM {TABLE_NAME}
    """

    with get_connection() as conn:
        result = pd.read_sql_query(
            query,
            conn
        )

    return {
        "start_date": pd.to_datetime(
            result.loc[0, "start_date"]
        ),
        "end_date": pd.to_datetime(
            result.loc[0, "end_date"]
        )
    }


# --------------------------------------------------
# 7. DATA QUALITY CHECK
# --------------------------------------------------

def get_data_quality():
    """
    Retrieve basic database quality indicators.
    """

    query = f"""
        SELECT

            COUNT(*) AS total_records,

            COUNT(DISTINCT datetime) AS unique_timestamps,

            SUM(
                CASE
                    WHEN energy_kwh < 0
                    THEN 1 ELSE 0
                END
            ) AS negative_energy_records,

            SUM(
                CASE
                    WHEN energy_kwh IS NULL
                    THEN 1 ELSE 0
                END
            ) AS missing_energy_records,

            SUM(
                CASE
                    WHEN valid_minutes > 60
                    THEN 1 ELSE 0
                END
            ) AS invalid_minute_counts

        FROM {TABLE_NAME}
    """

    with get_connection() as conn:
        result = pd.read_sql_query(
            query,
            conn
        )

    return result.iloc[0].to_dict()


# --------------------------------------------------
# 8. DATABASE TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("=" * 50)
    print("ENERGY INSIGHT - DATABASE TEST")
    print("=" * 50)

    # Test hourly data
    hourly = load_hourly_data()

    print("\nHOURLY DATA")
    print("Records:", f"{len(hourly):,}")
    print("Columns:", list(hourly.columns))

    # Test daily data
    daily = load_daily_data()

    print("\nDAILY DATA")
    print("Usable days:", f"{daily.notna().sum():,}")
    print("Missing days:", f"{daily.isna().sum():,}")

    # Test summary
    print("\nDATABASE SUMMARY")

    for key, value in get_data_summary().items():
        print(f"{key}: {value}")

    # Test data quality
    print("\nDATA QUALITY")

    for key, value in get_data_quality().items():
        print(f"{key}: {value}")

    # Test date range
    print("\nDATE RANGE")

    for key, value in get_date_range().items():
        print(f"{key}: {value}")

    print("\nDATABASE TEST COMPLETED SUCCESSFULLY!")
