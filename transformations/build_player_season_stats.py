
import json
from pathlib import Path

import pandas as pd

SEASON = "2026"

# Load latest raw dataset
raw_files = sorted(
    Path("data/raw").glob(f"wnba_player_stats_{SEASON}_*.json")
)

if not raw_files:
    raise FileNotFoundError("No raw data found")

with open(raw_files[-1]) as file:
    raw = json.load(file)

result = raw["resultSets"][0]

df = pd.DataFrame(
    result["rowSet"],
    columns=result["headers"]
)

# Define additive statistics
additive_columns = [
    "GP", "MIN", "FGM", "FGA",
    "FG3M", "FG3A", "FTM", "FTA",
    "OREB", "DREB", "REB", "AST",
    "TOV", "STL", "BLK", "PTS"
]

# Validate required columns
required_columns = [
    "PLAYER_ID", "PLAYER_NAME", "TEAM_ID",
    "TEAM_ABBREVIATION"
] + additive_columns

missing = set(required_columns) - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {missing}")

# Ensure player IDs and numeric statistics are valid
if df["PLAYER_ID"].isna().any():
    raise ValueError("Missing player IDs")

for column in additive_columns:
    df[column] = pd.to_numeric(df[column], errors="raise")

# Identify potential pre-aggregated total rows
# Common convention: team abbreviation TOT
total_rows = df[
    df["TEAM_ABBREVIATION"].isin(["TOT"])
]

if not total_rows.empty:
    raise ValueError(
        "Pre-aggregated total rows detected. "
        "Review these before combining records."
    )

# Aggregate all additive statistics by player
season_stats = (
    df.groupby("PLAYER_ID", as_index=False)[additive_columns]
    .sum()
)

# Select a display name consistently.
# Prefer the name from the row with the most minutes.
player_names = (
    df.sort_values(
        ["PLAYER_ID", "MIN"],
        ascending=[True, False]
    )
    .drop_duplicates("PLAYER_ID")
    [["PLAYER_ID", "PLAYER_NAME"]]
)

# Preserve all teams associated with each player.
player_teams = (
    df.groupby("PLAYER_ID")["TEAM_ABBREVIATION"]
    .agg(lambda teams: ", ".join(sorted(set(teams))))
    .reset_index(name="TEAMS")
)

# Combine attributes and statistics
cleaned = (
    season_stats
    .merge(player_names, on="PLAYER_ID", validate="one_to_one")
    .merge(player_teams, on="PLAYER_ID", validate="one_to_one")
)

# Recalculate percentages using aggregated totals
for made, attempted, output in [
    ("FGM", "FGA", "FG_PCT"),
    ("FG3M", "FG3A", "FG3_PCT"),
    ("FTM", "FTA", "FT_PCT")
]:
    cleaned[output] = (
        cleaned[made] /
        cleaned[attempted].replace(0, float("nan"))
    ).fillna(0)

cleaned["SEASON"] = SEASON

# Validate the target grain
assert not cleaned.duplicated(
    ["PLAYER_ID", "SEASON"]
).any()

assert len(cleaned) == df["PLAYER_ID"].nunique()

# Export cleaned dataset
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

output_path = (
    output_dir / f"player_season_stats_{SEASON}.csv"
)

cleaned.to_csv(output_path, index=False)

print(f"Raw records: {len(df)}")
print(f"Unique players: {df['PLAYER_ID'].nunique()}")
print(f"Cleaned records: {len(cleaned)}")
print(f"Players with multiple rows: "
      f"{df['PLAYER_ID'].value_counts().gt(1).sum()}")
print(f"Saved to: {output_path}")
