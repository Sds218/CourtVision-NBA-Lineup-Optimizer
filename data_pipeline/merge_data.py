import pandas as pd
import unicodedata
import re

# Normalizes names to help match players across datasets
def normalize_name(name):
    name = str(name).strip().lower()
    name = unicodedata.normalize("NFKD", name)

    name = "".join(
        char for char in name
        if not unicodedata.combining(char)
    )

    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name.strip())

    return name

# Loads the three NBA datasets
stats = pd.read_csv("data/nba_stats.csv")
salaries = pd.read_csv("data/nba_salaries.csv")
positions = pd.read_csv("data/nba_positions.csv")

# Creates normalized names for matching
stats["name_key"] = stats["PLAYER_NAME"].apply(normalize_name)
salaries["name_key"] = salaries["player"].apply(normalize_name)

# Merge Player stats with salary info
combined = stats.merge(
    salaries[["name_key","team", "salary"]],
    on="name_key",
    how="left",
    validate="one_to_one"
)

# Fixes different team abbreviations between datasets
team_codes = {
    "PHO": "PHX",
    "BRK": "BKN",
    "CHO": "CHA"
}

combined["team"] = combined["team"].replace(team_codes)

print("Total players:", len(combined))
print("Matched salaries:", combined["salary"].notna().sum())
print("Missing salaries:", combined["salary"].isna().sum())

# Save players without matching salary info
missing = combined[combined["salary"].isna()].copy()

missing[
    ["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION"]
].to_csv("data/missing_salaries.csv", index=False)

print(f"Saved {len(missing)} unmatched players.")

valid_players = combined[combined["salary"].notna()].copy()

# Convert salaries from dollars to millions
valid_players["Salary"] = valid_players["salary"] / 1_000_000

# Match positions using each player's NBA ID
valid_players = valid_players.merge(
    positions[["PLAYER_ID", "POSITION"]],
    on="PLAYER_ID",
    how="left",
    validate="one_to_one"
)

# Find players whose teams do not match
team_mismatches = valid_players[
    valid_players["TEAM_ABBREVIATION"] != valid_players["team"]
]

team_mismatches[
    ["PLAYER_NAME", "TEAM_ABBREVIATION", "team", "salary"]
].to_csv("data/team_mismatches.csv", index=False)

print(f"Saved {len(team_mismatches)} team mismatches for review.")

print("\nPosition merge results:")

print("Players with positions:",
      valid_players["POSITION"].notna().sum())

print("Players missing positions:",
      valid_players["POSITION"].isna().sum())

print("\nPosition types:")
print(valid_players["POSITION"].value_counts(dropna=False))

# Rename columns to match CourtVision's format
courtvision_players = valid_players.rename(columns={
    "PLAYER_NAME": "Player",
    "POSITION": "Position",
    "PTS": "Points",
    "REB": "Rebounds",
    "AST": "Assists"
}).copy()

courtvision_players = courtvision_players[
    ["Player", "Position", "Salary",
     "Points", "Rebounds", "Assists"]
]

print("\nMissing values in final dataset:")
print(courtvision_players.isna().sum())

if courtvision_players.isna().any().any():
    raise ValueError("Missing values found in the final dataset.")

# Save the final dataset for CourtVision
courtvision_players.to_csv(
    "data/nba_players.csv",
    index=False
)

print(f"Saved {len(courtvision_players)} players for CourtVision.")