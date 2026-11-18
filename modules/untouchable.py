"""Find franchise-level ("untouchable") players from the data itself.

No live API is needed. Rule:
  * With a Team column: a player is untouchable when he is the best player
    on his team (by Performance score) AND is in the league's top
    `top_percent` percent of the pool.
  * Without a Team column: only the top `max_without_team` players in the
    whole pool are flagged.
  * Names in `manual` are always included (manual override).

Ranking uses the same merge sort and tie-break rule as ranking.py.
"""
import math

from modules.ranking import merge_sort


def find_untouchables(df, score_col="Performance", team_col="Team",
                      top_percent=10, per_team=1, max_without_team=10,
                      manual=()):
    """Names of untouchable players, best score first."""
    df = df.reset_index(drop=True)
    if df.empty:
        return []

    names = df["Player"].tolist()
    scores = df[score_col].tolist()
    salaries = (df["Salary"].tolist() if "Salary" in df.columns
                else [0] * len(df))
    items = [{"name": names[i], "salary": salaries[i], "score": scores[i],
              "i": i} for i in range(len(df))]
    ranked = merge_sort(items)                      # best first

    n_elite = max(1, math.ceil(len(df) * top_percent / 100))
    elite = {p["i"] for p in ranked[:n_elite]}

    chosen = set()
    if team_col in df.columns:
        taken = {}
        for p in ranked:
            team = df.loc[p["i"], team_col]
            if team != team:                        # missing team name
                continue
            if taken.get(team, 0) < per_team:
                taken[team] = taken.get(team, 0) + 1
                if p["i"] in elite:
                    chosen.add(p["i"])
    else:
        chosen = {p["i"] for p in ranked[:max_without_team]}

    for p in ranked:
        if p["name"] in manual:
            chosen.add(p["i"])

    return [p["name"] for p in ranked if p["i"] in chosen]