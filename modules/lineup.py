"""Locked (untouchable) players, similar-player search, full roster builder.

optimize_with_locked: untouchable players are ALWAYS on the roster. We take
them out of the pool, subtract their salaries from the budget, shrink the
lineup size, and let the knapsack DP fill the remaining spots.

similar_players: finds the players whose stat profile is closest to a target
(Euclidean distance on min-max normalized stats).

build_roster: starters + bench for the app, with locked players and an
optional position filter.
"""
import math

from modules.scoring import DEFAULT_WEIGHTS, min_max
from modules.knapsack import optimize_lineup, roster_lineup

EPS = 1e-9


def _summarize(res, locked, rest, budget, k, score_col, salary_col):
    """Merge the locked players back into a knapsack result."""
    # Greedy can return a partial roster, so keep whatever was picked.
    picked = rest.iloc[res["selected"]]
    lineup = _concat(locked, picked) if len(locked) else picked
    chosen = lineup

    total_score = float(chosen[score_col].sum())
    total_salary = float(chosen[salary_col].sum())
    size = len(chosen)
    return {
        "method": res["method"],
        "lineup": lineup,
        "total_score": round(total_score, 6),
        "total_salary": round(total_salary, 6),
        "remaining_cap": round(budget - total_salary, 6),
        "roster_size": size,
        "feasible": res["feasible"],
        "constraints_ok": (res["feasible"] and size == k
                           and total_salary <= budget + EPS),
        "runtime_s": res["runtime_s"],
        "dp_states": res["dp_states"],
    }


def _concat(a, b):
    import pandas as pd
    return pd.concat([a, b], ignore_index=True)


def optimize_with_locked(df, budget, k, locked_names,
                         score_col="Performance", salary_col="Salary"):
    """Best lineup of exactly k players that always includes locked_names.

    Returns {"error": str|None, "dp": result, "greedy": result}.
    """
    df = df.reset_index(drop=True)
    is_locked = df["Player"].isin(list(locked_names))
    locked = df[is_locked].reset_index(drop=True)
    rest = df[~is_locked].reset_index(drop=True)

    if len(locked) > k:
        return {"error": f"{len(locked)} untouchable players are in the pool "
                         f"but the lineup only has {k} spots."}

    locked_salary = float(locked[salary_col].sum())
    left = round(budget - locked_salary, 6)
    if left < 0:
        return {"error": f"Untouchable players cost ${locked_salary:.1f}M, "
                         f"which is over the ${budget}M budget."}

    dp, greedy = optimize_lineup(rest, left, k - len(locked),
                                 score_col, salary_col)
    return {
        "error": None,
        "dp": _summarize(dp, locked, rest, budget, k, score_col, salary_col),
        "greedy": _summarize(greedy, locked, rest, budget, k,
                             score_col, salary_col),
    }


def similar_players(df, target, exclude=(), stat_cols=None, top_n=3):
    """The top_n players closest in profile to `target`.

    df:       DataFrame with a 'Player' column and stat columns
    target:   name of the player to compare against
    exclude:  names that may not appear in the answer (e.g. untouchables)
    stat_cols: stats that define the profile (default: scoring weight stats
               that exist in df)
    """
    df = df.reset_index(drop=True)
    names = df["Player"].tolist()
    if target not in names:
        raise ValueError(f"{target} is not in the data")

    cols = [c for c in (stat_cols or DEFAULT_WEIGHTS) if c in df.columns]
    if not cols:
        raise ValueError("No stat columns to compare")

    # every stat on the same 0..1 scale, then straight-line distance
    norm = {c: min_max([float(v) for v in df[c]]) for c in cols}
    t = names.index(target)
    rows = []
    for i, name in enumerate(names):
        if i == t or name in exclude:
            continue
        dist = math.sqrt(sum((norm[c][i] - norm[c][t]) ** 2 for c in cols))
        rows.append((dist, name, i))

    rows.sort(key=lambda r: (r[0], r[1]))          # closest first, then A-Z
    top = rows[:top_n]

    max_dist = math.sqrt(len(cols))                 # farthest possible
    out = df.iloc[[i for _, _, i in top]].copy().reset_index(drop=True)
    out["Similarity %"] = [round(100 * (1 - d / max_dist), 1)
                           for d, _, _ in top]
    if "Salary" in df.columns:
        out["Salary vs target ($M)"] = [
            round(float(df.loc[i, "Salary"] - df.loc[t, "Salary"]), 2)
            for _, _, i in top
        ]
    return out


def build_roster(df, cap, starters, bench, locked_names=(), positions=None,
                 bench_weight=0.4, score_col="Performance",
                 salary_col="Salary"):
    """Full roster (starters + bench) for the app.

    locked_names: players who must be on the roster (owned / untouchable)
    positions:    if given, the OTHER spots are filled only from these
                  positions (locked players are kept whatever their position)

    Returns {"error": str|None, "result": roster_lineup dict,
             "starters": DataFrame, "bench": DataFrame}.
    """
    df = df.reset_index(drop=True)
    names = df["Player"].tolist()
    locked = [names.index(n) for n in dict.fromkeys(locked_names)
              if n in names]
    allowed = None
    if positions:
        allowed = {i for i, pos in enumerate(df["Position"]) if pos in positions}

    k = starters + bench
    if len(df) < k:
        return {"error": f"Only {len(df)} players available for {k} spots."}
    if len(locked) > k:
        return {"error": f"{len(locked)} locked players but only {k} spots."}
    locked_salary = float(df.loc[locked, salary_col].sum()) if locked else 0.0
    if locked_salary > cap + EPS:
        return {"error": f"Locked players cost ${locked_salary:.1f}M, "
                         f"over the ${cap}M cap."}

    res = roster_lineup(df[score_col].tolist(), df[salary_col].tolist(),
                        cap, starters, bench, bench_weight,
                        locked=locked, allowed=allowed)
    if not res["feasible"]:
        return {"error": "No roster fits this cap with those requirements. "
                         "Raise the cap, shrink the bench, or allow more "
                         "positions.", "result": res}

    start_df = df.iloc[res["starters"]].copy()
    bench_df = df.iloc[res["bench"]].copy()
    start_df.insert(0, "Role", "Starter")
    bench_df.insert(0, "Role", "Bench")
    return {"error": None, "result": res,
            "starters": start_df.reset_index(drop=True),
            "bench": bench_df.reset_index(drop=True)}