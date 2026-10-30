"""Player scoring: weighted sum of min-max normalized stats, scaled 0-100."""

# stat column -> weight (relative; re-scaled below). Negative = penalty.
DEFAULT_WEIGHTS = {
    "Points": 0.30,
    "Assists": 0.15,
    "Rebounds": 0.15,
    "TS%": 0.15,         # efficiency
    "Steals": 0.05,      # defense
    "Blocks": 0.05,      # defense
    "Minutes": 0.10,     # playing time
    "Turnovers": -0.05,  # penalty: more turnovers is worse
}


def min_max(values):
    """Scale numbers to 0..1. If all values are equal, return all 0."""
    lo, hi = min(values), max(values)
    if hi == lo:                      # avoids dividing by zero
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def composite_scores(stats, weights=None):
    """stats: {stat_name: [value for each player]} -> list of 0-100 scores."""
    weights = DEFAULT_WEIGHTS if weights is None else weights
    if not stats:
        return []
    n = len(next(iter(stats.values())))
    if n == 0:
        return []

    # only use stats that exist in the data (the demo has just 3 of them)
    w = {c: x for c, x in weights.items() if c in stats}
    if not w:
        raise ValueError("None of the weighted stats are in the data.")

    pos_total = sum(x for x in w.values() if x > 0)   # makes the best score 100
    penalty = sum(-x for x in w.values() if x < 0) / pos_total

    raw = [0.0] * n
    for stat, weight in w.items():
        norm = min_max([float(v) for v in stats[stat]])
        for i in range(n):
            raw[i] += (weight / pos_total) * norm[i]

    # raw lies in [-penalty, 1]; stretch that range to 0..100
    return [round((r + penalty) / (1 + penalty) * 100, 2) for r in raw]


def add_performance(df, weights=None, column="Performance"):
    """Add a Performance column to a pandas DataFrame (returns a copy)."""
    out = df.copy()
    weights = DEFAULT_WEIGHTS if weights is None else weights
    stats = {c: out[c].tolist() for c in weights if c in out.columns}
    out[column] = composite_scores(stats, weights) if len(out) else []
    return out