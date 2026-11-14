import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_ROOT /
    "data" /
    "processed" /
    "energy_v2.db"
)

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()

cursor.execute("""
    SELECT
        COUNT(*),
        COUNT(DISTINCT datetime),
        SUM(
            CASE
                WHEN energy_kwh < 0 THEN 1
                ELSE 0
            END
        )
    FROM hourly_usage
""")

total, unique_timestamps, negative_energy = cursor.fetchone()

print("DATA VALIDATION REPORT")

print("Total records:", total)
print("Unique timestamps:", unique_timestamps)
print("Negative energy values:", negative_energy)

assert total == unique_timestamps, "Duplicate timestamps found!"

assert negative_energy == 0, "Negative energy detected!"

print("\nAll validation checks passed!")

conn.close()