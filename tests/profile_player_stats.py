
import json
from pathlib import Path

import pandas as pd

# Load the latest raw file
files = sorted(Path("data/raw").glob("wnba_player_stats_2026_*.json"))

if not files:
    raise FileNotFoundError("No 2026 player stats file found")

with open(files[-1]) as file:
    raw_data = json.load(file)

result_set = raw_data["resultSets"][0]

df = pd.DataFrame(
    result_set["rowSet"],
    columns=result_set["headers"]
)

print("\n--- DATA QUALITY CHECKS ---")

# Check 1: Missing player IDs
print("Missing player IDs:", df["PLAYER_ID"].isna().sum())

# Check 2: Unique players
print("Unique players:", df["PLAYER_ID"].nunique())

# Check 3: Duplicate player IDs
duplicates = df[df.duplicated("PLAYER_ID", keep=False)]

print("Rows with repeated player IDs:", len(duplicates))

if not duplicates.empty:
    print(
        duplicates[
            ["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP"]
        ].sort_values("PLAYER_ID").to_string(index=False)
    )

# Check 4: Missing values across all columns
missing = df.isna().sum()
print("\nColumns with missing values:")
print(missing[missing > 0].to_string())

# Check 5: Negative statistics
for column in ["GP", "MIN", "PTS", "REB", "AST"]:
    count = (df[column] < 0).sum()
    print(f"Negative {column} values: {count}")





# Investigate repeated player records
player = df[df["PLAYER_ID"] == 1628269]

print("\n--- DUPLICATE INVESTIGATION ---")

columns = [
    "PLAYER_ID",
    "PLAYER_NAME",
    "TEAM_ID",
    "TEAM_ABBREVIATION",
    "AGE",
    "GP",
    "MIN",
    "PTS",
    "REB",
    "AST",
    "TEAM_COUNT"
]

print(player[columns].to_string(index=False))

# Identify every field that differs between the records
different_columns = [
    col for col in df.columns
    if player[col].nunique(dropna=False) > 1
]

print("\nColumns with different values:")
print(different_columns)




# Check uniqueness at the expected grain
key_columns = ["PLAYER_ID", "TEAM_ID"]

duplicate_keys = df[
    df.duplicated(subset=key_columns, keep=False)
]

print("\n--- EXPECTED GRAIN VALIDATION ---")
print(f"Total rows: {len(df)}")
print(f"Unique player/team combinations: {df[key_columns].drop_duplicates().shape[0]}")
print(f"Rows violating uniqueness: {len(duplicate_keys)}")

if not duplicate_keys.empty:
    print("\nDuplicate records:")
    print(
        duplicate_keys[
            ["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", "PTS"]
        ].to_string(index=False)
    )

    print("\nWARNING: Player/team uniqueness check failed.")
else:
    print("\nPASS: Player/team combinations are unique.")
