"""Project-wide settings for CourtVision."""

LINEUP_SIZE = 5            # fixed lineup size (team decision)

SALARY_CAP_M = 164.961     # 2026-27 NBA salary cap, $ millions
TAX_LEVEL_M = 200.428      # 2026-27 luxury tax level, $ millions
DEFAULT_BUDGET_M = 150     # a starting five uses most of the cap

# Franchise players the app must warn about (match the "Player" column)
UNTOUCHABLE = {"Jayson Tatum"}