"""Build data/processed/energy_v2.db from the raw minute-level data.

Input : data/household_power_consumption.txt   (UCI dataset, one row per minute)
        (data/raw/household_power_consumption.txt is also accepted)
Output: data/processed/energy_v2.db            (table hourly_usage, one row per hour)

Run it from anywhere:  python clean_data.py
Then check the result: python validate_data.py

How an hour is built
--------------------
Global_active_power is measured in kW once per minute, and missing readings
are stored as "?" in the raw file. For every clock hour we keep:

  total_records       minute rows present in the raw file for that hour
  valid_minutes       minutes with a real reading
  coverage_percent    valid_minutes / 60 * 100
  avg_power_kw        mean of the valid minute readings (NaN if there are none)
  observed_energy_kwh energy from the valid minutes only = sum(kW) / 60
  is_complete         1 if all 60 minutes have a reading, else 0
  energy_kwh          avg_power_kw for complete hours, NaN otherwise

Why energy_kwh is NaN for incomplete hours: an average over 36 of 60 minutes
is not a full hour of usage. The dashboard therefore only analyses complete
hours, and nothing is silently filled in or invented.

kW averaged over exactly one hour equals kWh, which is why a complete hour's
energy_kwh is simply the mean of its 60 minute readings.
"""

import sqlite3
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

RAW_CANDIDATES = [
    ROOT / "data" / "household_power_consumption.txt",
    ROOT / "data" / "raw" / "household_power_consumption.txt"
]

DB_PATH = ROOT / "data" / "processed" / "energy_v2.db"

CREATE_TABLE = """
CREATE TABLE hourly_usage (
    datetime TEXT PRIMARY KEY,
    avg_power_kw REAL,
    energy_kwh REAL,
    observed_energy_kwh REAL,
    valid_minutes INTEGER,
    total_records INTEGER,
    coverage_percent REAL,
    is_complete INTEGER,
    hour INTEGER,
    weekday TEXT,
    month INTEGER,
    year INTEGER,
    is_weekend INTEGER
)
"""


# --------------------------------------------------
# 2. LOAD RAW MINUTE DATA
# --------------------------------------------------

def find_raw_file():

    for path in RAW_CANDIDATES:
        if path.exists():
            return path

    searched = "\n  ".join(str(p) for p in RAW_CANDIDATES)

    raise FileNotFoundError(
        "Raw data file not found. Looked in:\n  " + searched
    )


def load_minute_data(raw_path):

    raw = pd.read_csv(
        raw_path,
        sep=";",
        usecols=["Date", "Time", "Global_active_power"],
        na_values=["?"],
        low_memory=False
    )

    minutes = pd.DataFrame({
        "datetime": pd.to_datetime(
            raw["Date"] + " " + raw["Time"],
            format="%d/%m/%Y %H:%M:%S"
        ),
        "power_kw": pd.to_numeric(
            raw["Global_active_power"],
            errors="coerce"
        )
    })

    duplicates = int(minutes["datetime"].duplicated().sum())

    if duplicates:
        print("Duplicate minute timestamps removed:", duplicates)
        minutes = minutes.drop_duplicates(subset="datetime", keep="first")

    return minutes.set_index("datetime").sort_index()["power_kw"]


# --------------------------------------------------
# 3. AGGREGATE TO HOURS
# --------------------------------------------------

def build_hourly_table(power_kw):

    hourly = power_kw.resample("h").agg(["count", "size", "sum", "mean"])

    # Make sure every clock hour exists, even if the raw file has none.
    full_range = pd.date_range(hourly.index.min(), hourly.index.max(), freq="h")

    hourly = hourly.reindex(full_range)

    hourly["size"] = hourly["size"].fillna(0)
    hourly["count"] = hourly["count"].fillna(0)
    hourly["sum"] = hourly["sum"].fillna(0.0)

    table = pd.DataFrame(index=hourly.index)

    table["avg_power_kw"] = hourly["mean"]
    table["observed_energy_kwh"] = hourly["sum"] / 60
    table["valid_minutes"] = hourly["count"].astype(int)
    table["total_records"] = hourly["size"].astype(int)
    table["coverage_percent"] = table["valid_minutes"] / 60 * 100
    table["is_complete"] = (table["valid_minutes"] == 60)&(table["total_records"] ==60).astype(int)

    table["energy_kwh"] = table["avg_power_kw"].where(table["is_complete"] == 1)

    table["hour"] = table.index.hour
    table["weekday"] = table.index.day_name()
    table["month"] = table.index.month
    table["year"] = table.index.year
    table["is_weekend"] = (table.index.dayofweek >= 5).astype(int)

    table.index.name = "datetime"

    table = table.reset_index()

    # SQLite has no datetime type, so store ISO text.
    table["datetime"] = table["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return table[[
        "datetime", "avg_power_kw", "energy_kwh", "observed_energy_kwh",
        "valid_minutes", "total_records", "coverage_percent", "is_complete",
        "hour", "weekday", "month", "year", "is_weekend"
    ]]


# --------------------------------------------------
# 4. SAVE
# --------------------------------------------------

def save_to_database(table, db_path):

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:

        conn.execute("DROP TABLE IF EXISTS hourly_usage")
        conn.execute(CREATE_TABLE)

        table.to_sql("hourly_usage", conn, if_exists="append", index=False)


# --------------------------------------------------
# 5. MAIN
# --------------------------------------------------

def main():

    raw_path = find_raw_file()

    print("Reading:", raw_path)

    power_kw = load_minute_data(raw_path)

    missing_minutes = int(power_kw.isna().sum())

    print("Minute rows read:", f"{len(power_kw):,}")
    print("Minutes with missing readings:", f"{missing_minutes:,}")

    table = build_hourly_table(power_kw)

    save_to_database(table, DB_PATH)

    complete = int(table["is_complete"].sum())

    print()
    print("Saved:", DB_PATH)
    print("Hours saved:", f"{len(table):,}")
    print("Complete hours (all 60 minutes):", f"{complete:,}")
    print("Incomplete hours (excluded from analysis):",
          f"{len(table) - complete:,}")
    print("Period:", table["datetime"].iloc[0], "to", table["datetime"].iloc[-1])
    print("\nNext step: python validate_data.py")


if __name__ == "__main__":
    main()
