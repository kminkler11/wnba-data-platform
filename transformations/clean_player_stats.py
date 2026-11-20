import json
from pathlib import Path

import pandas as pd

SEASON = "2026"

# Load latest raw dataset
files = sorted(
    Path("data/raw").glob(f"wnba_player_stats_{SEASON}_*.json")
)

if not files:
    raise FileNotFoundError("No raw player stats found")

with open(files[-1]) as file:
    raw_data = json.load(file)

result_set = raw_data["resultSets"][0]

df = pd.DataFrame(
    result_set["rowSet"],
    columns=result_set["headers"]
)

# Identify repeated player/team combinations
keys = ["PLAYER_ID", "TEAM_ID"]

duplicates = df[df.duplicated(keys, keep=False)]

print(f"Raw rows: {len(df)}")
print(f"Repeated player/team rows: {len(duplicates)}")

# Inspect known split records
nia = df[df["PLAYER_ID"] == 1628269]

if len(nia) != 2:
    raise ValueError("Expected two records for Nia Brodie")

# Calculate candidate combined totals
count_columns = [
    "GP", "MIN", "FGM", "FGA",
    "FG3M", "FG3A", "FTM", "FTA",
    "OREB", "DREB", "REB", "AST",
    "TOV", "STL", "BLK", "PTS"
]

combined = nia[count_columns].sum()

print("\nCandidate combined statistics:")
print(combined.to_string())

# Recalculate shooting percentages
fg_pct = (
    combined["FGM"] / combined["FGA"]
    if combined["FGA"] > 0 else 0
)

print(f"\nCombined FG%: {fg_pct:.3f}")
print("\nNo records have been modified yet.")



# Validate candidate aggregation
calculated_points = (
    2 * (combined["FGM"] - combined["FG3M"])
    + 3 * combined["FG3M"]
    + combined["FTM"]
)

calculated_rebounds = combined["OREB"] + combined["DREB"]

assert calculated_points == combined["PTS"], (
    "Point totals do not reconcile"
)

assert calculated_rebounds == combined["REB"], (
    "Rebound totals do not reconcile"
)

assert combined["GP"] == 44, (
    "Unexpected games played for Nia Brodie"
)

print("\nAll candidate aggregation checks passed!")
