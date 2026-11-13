import pandas as pd
import time
from pathlib import Path
from nba_api.stats.endpoints import commonplayerinfo

# Load NBA players from stats file
players = pd.read_csv("data/nba_stats.csv")

output_file = Path("data/nba_positions.csv")

# Load previously saved positions so we don't download them again
if output_file.exists():
    positions = pd.read_csv(output_file).to_dict("records")
else:
    positions = []

# Keep track of players already saved with a position
completed_ids = {int(p["PLAYER_ID"]) for p in positions}

# Go through each player and get their positions from NBA API
for _, player in players.iterrows():

    player_id = int(player["PLAYER_ID"])
    player_name = player["PLAYER_NAME"]

    if player_id in completed_ids:
        print(f"Skipping {player_name} - already saved")
        continue

    try:
        info = commonplayerinfo.CommonPlayerInfo(
            player_id=player_id,
            timeout=30
        )

        player_info = info.get_data_frames()[0]

        if player_info.empty:
            print(f"No position information for {player_name}")
            continue

        position = player_info.iloc[0]["POSITION"]

        # Add the player's ID and position to our list
        positions.append({
            "PLAYER_ID": player_id,
            "POSITION": position
        })

        # Save after each player is case the program stops early
        pd.DataFrame(positions).to_csv(
            output_file,
            index=False
        )

        completed_ids.add(player_id)

        print(f"Saved {player_name}: {position}")

    except Exception as e:
        print(f"Failed to retrieve {player_name}: {e}")

    # Small delay between API requests
    time.sleep(1)

print("\nFinished processing players.")
print(f"Total positions saved: {len(completed_ids)}")
