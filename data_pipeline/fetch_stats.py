from nba_api.stats.endpoints import leaguedashplayerstats
from pathlib import Path

# Get NBA player stats for the 2025-26 season
stats = leaguedashplayerstats.LeagueDashPlayerStats(
    season = "2025-26",
    per_mode_detailed = "PerGame",
    timeout = 30
)

# Convert API response into a DataFrame
players = stats.get_data_frames() [0]

# Create the data folder if it doesn't already exist
output = Path("data/nba_stats.csv")
output.parent.mkdir(parents = True, exist_ok = True)

# Save the player stats to a CSV file
players.to_csv(output, index = False)

print(f"Saved {len(players)} players to {output}")