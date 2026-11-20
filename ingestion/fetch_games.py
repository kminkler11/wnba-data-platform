import json
from pathlib import Path
from datetime import datetime, timezone

from nba_api.stats.endpoints import leaguedashplayerstats

# Configuration
SEASON = "2026"
LEAGUE_ID = "10"  # WNBA

# Request player statistics
print(f"Fetching WNBA player stats for {SEASON}...")

response = leaguedashplayerstats.LeagueDashPlayerStats(
    season=SEASON,
    league_id_nullable=LEAGUE_ID,
    season_type_all_star="Regular Season",
    per_mode_detailed="Totals",
    timeout=30
)

# Preserve the raw API response
raw_data = json.loads(response.get_json())

# Validate that data was returned
if not raw_data.get("resultSets"):
    raise ValueError("API returned no result sets")

# Create the output directory
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

# Save the response
timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
output_file = output_dir / f"wnba_player_stats_{SEASON}_{timestamp}.json"

with open(output_file, "w") as file:
    json.dump(raw_data, file, indent=2)

print(f"Data saved to {output_file}")
print("Ingestion complete!")




# INSPECT DATA

import pandas as pd

# Extract the first result set
result_set = raw_data["resultSets"][0]

# Convert the API response into a DataFrame
df = pd.DataFrame(
    result_set["rowSet"],
    columns=result_set["headers"]
)

print("\n--- DATA PROFILE ---")
print(f"Number of rows: {len(df)}")
print(f"Number of columns: {len(df.columns)}")

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head().to_string(index=False))

print("\nMissing values:")
print(df.isnull().sum().loc[lambda x: x > 0])
