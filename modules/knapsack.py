"""0/1 Knapsack DP for lineup selection.

dp[j][w] = best total score using exactly j players with total cost <= w.
"""
import math
import time

NEG_INF = float("-inf")
EPS = 1e-9


def _to_units(salaries, budget, scale):
    """Salaries ($M, decimals) -> whole-number costs.
    Costs round UP and the budget rounds DOWN, so we never exceed the cap."""
    costs = [math.ceil(s * scale - EPS) for s in salaries]
    cap = math.floor(budget * scale + EPS)
    return costs, cap


def _validate(scores, salaries, budget, k):
    if len(scores) != len(salaries):
        raise ValueError("scores and salaries must have the same length")
    if k < 0:
        raise ValueError("lineup size k cannot be negative")
    if budget < 0:
        raise ValueError("budget cannot be negative")
    for s in salaries:
        if s != s or s < 0:          # s != s catches NaN
            raise ValueError("salaries must be non-negative numbers")
    for v in scores:
        if v != v:
            raise ValueError("scores cannot be NaN")


def _build_table(scores, costs, cap, k, slot_weights=None, bonus=None):
    """Fill the DP table. Returns (dp, take, states).

    take[i][j][w] = 1 when taking player i improved dp[j][w]
    (we use it in step 3b to rebuild the lineup).
    """
    n = len(scores)

    # row j = players used, column w = budget available
    dp = [[NEG_INF] * (cap + 1) for _ in range(k + 1)]
    dp[0] = [0.0] * (cap + 1)        # 0 players -> score 0 at any budget
    take = [[bytearray(cap + 1) for _ in range(k + 1)] for _ in range(n)]

    states = 0                       # cells evaluated (for the report)
    for i in range(n):
        c, v = costs[i], scores[i]
        if c > cap:
            continue                 # can never afford this player
        for j in range(min(i + 1, k), 0, -1):       # downward = 0/1 property
            prev, cur, flags = dp[j - 1], dp[j], take[i][j]
            # score added if player i becomes the j-th pick (slot j)
            gain = v if slot_weights is None else v * slot_weights[j - 1]
            if bonus is not None:
                gain += bonus[i]     # big bonus = "must keep this player"
            for w in range(cap, c - 1, -1):         # downward as well
                states += 1
                candidate = prev[w - c] + gain       # take player i
                if candidate > cur[w]:               # better than skipping?
                    cur[w] = candidate
                    flags[w] = 1
    return dp, take, states

def _result(chosen, scores, salaries, budget, k, seconds, states, method):
    """Package a lineup into a dict the app can display."""
    total_salary = sum(salaries[i] for i in chosen)
    return {
        "method": method,
        "selected": sorted(chosen),             # positions in the input lists
        "total_score": round(sum(scores[i] for i in chosen), 6),
        "total_salary": round(total_salary, 6),
        "remaining_cap": round(budget - total_salary, 6),
        "roster_size": len(chosen),
        "feasible": len(chosen) == k,
        "constraints_ok": (len(chosen) == k
                           and len(set(chosen)) == len(chosen)
                           and total_salary <= budget + EPS),
        "runtime_s": seconds,
        "dp_states": states,                    # cells evaluated
    }


def knapsack_lineup(scores, salaries, budget, k, scale=10,
                    slot_weights=None, bonus=None):
    """Optimal lineup of exactly k players within the budget.

    If no lineup of k players fits, 'feasible' is False and 'selected' is [].
    """
    _validate(scores, salaries, budget, k)
    t0 = time.perf_counter()
    n = len(scores)

    # Edge cases that need no table
    if k == 0:
        return _result([], scores, salaries, budget, k,
                       time.perf_counter() - t0, 0, "knapsack_dp")
    if n < k:
        return _result([], scores, salaries, budget, k,
                       time.perf_counter() - t0, 0, "knapsack_dp")

    costs, cap = _to_units(salaries, budget, scale)
    dp, take, states = _build_table(scores, costs, cap, k, slot_weights, bonus)
    elapsed = time.perf_counter() - t0

    # No way to pick k players inside the budget
    if dp[k][cap] == NEG_INF:
        return _result([], scores, salaries, budget, k,
                       elapsed, states, "knapsack_dp")

    # Walk backward from the last player to rebuild the lineup
    chosen, j, w = [], k, cap
    for i in range(n - 1, -1, -1):
        if j > 0 and take[i][j][w]:
            chosen.append(i)
            j -= 1
            w -= costs[i]

    return _result(chosen, scores, salaries, budget, k,
                   elapsed, states, "knapsack_dp")


def greedy_lineup(scores, salaries, budget, k):
    """Baseline: take players by score-per-salary while they fit.

    Fast, O(n log n), but NOT guaranteed optimal. It can also fail to
    fill the roster even when a valid lineup exists.
    """
    _validate(scores, salaries, budget, k)
    t0 = time.perf_counter()

    def ratio(i):
        # a free player has an infinite ratio, so he is taken first
        return scores[i] / salaries[i] if salaries[i] > 0 else float("inf")

    # best ratio first; the index breaks ties so the order is repeatable
    order = sorted(range(len(scores)), key=lambda i: (-ratio(i), i))

    chosen, spent = [], 0.0
    for i in order:
        if len(chosen) == k:
            break
        if spent + salaries[i] <= budget + EPS:
            chosen.append(i)
            spent += salaries[i]

    return _result(chosen, scores, salaries, budget, k,
                   time.perf_counter() - t0, len(order), "greedy")


def optimize_lineup(df, budget, k, score_col="Performance",
                    salary_col="Salary", scale=10):
    """For the Streamlit app: DataFrame in, (dp_result, greedy_result) out.

    Each result's 'selected' holds ROW POSITIONS in df, so the app can use
    df.iloc[result['selected']] to get the chosen players.
    """
    scores = df[score_col].tolist()
    salaries = df[salary_col].tolist()
    return (knapsack_lineup(scores, salaries, budget, k, scale),
            greedy_lineup(scores, salaries, budget, k))


LOCK_BONUS = 1_000_000.0   # far bigger than any real score total


def roster_lineup(scores, salaries, budget, starters=5, bench=5,
                  bench_weight=0.4, scale=10, locked=(), allowed=None):
    """Best roster of `starters` + `bench` players within the budget.

    A starter's score counts fully; a bench player's score counts
    `bench_weight` (0..1), because starters play more minutes.

    locked:  positions (in the input lists) of players who MUST be on the
             roster (already owned, untouchable, ...).
    allowed: if given, the only other positions that may be picked
             (e.g. "only centers"). Locked players are always allowed.

    Trick 1: if players are processed best-score-first, the j-th player picked
    is always the j-th best of the final roster. So the first `starters`
    picks are exactly the starters, and a plain knapsack with per-slot
    weights (1.0 for starter slots, bench_weight for bench slots) is enough.

    Trick 2: a locked player gets a huge fixed bonus inside the table, so
    every optimal roster keeps him. We then check he really fit the budget.
    """
    if not 0 <= bench_weight <= 1:
        raise ValueError("bench_weight must be between 0 and 1")
    if starters < 0 or bench < 0:
        raise ValueError("starters and bench cannot be negative")
    k = starters + bench
    _validate(scores, salaries, budget, k)

    locked = list(dict.fromkeys(locked))          # unique, keep order
    if any(not 0 <= i < len(scores) for i in locked):
        raise ValueError("locked contains a player that does not exist")
    if len(locked) > k:
        raise ValueError("more locked players than roster spots")

    # best score first; ties -> cheaper first (same rule as ranking.py)
    from modules.ranking import merge_sort
    items = [{"name": str(i), "salary": salaries[i], "score": scores[i],
              "i": i} for i in range(len(scores))
             if allowed is None or i in allowed or i in locked]
    order = [p["i"] for p in merge_sort(items)]

    slot_weights = [1.0] * starters + [bench_weight] * bench
    bonus = [LOCK_BONUS if i in locked else 0.0 for i in order]
    res = knapsack_lineup([scores[i] for i in order],
                          [salaries[i] for i in order],
                          budget, k, scale, slot_weights, bonus)

    # sorted positions -> original positions; ascending = best score first
    picked = [order[p] for p in res["selected"]]
    if res["feasible"] and not all(i in picked for i in locked):
        # the locked players alone do not fit the budget
        picked, res["feasible"] = [], False
    res["starters"] = picked[:starters]
    res["bench"] = picked[starters:]
    res["selected"] = sorted(picked)
    res["weighted_score"] = round(
        sum(scores[i] for i in res["starters"])
        + bench_weight * sum(scores[i] for i in res["bench"]), 6)
    # recompute totals from the real (un-bonused) numbers
    res["total_score"] = round(sum(scores[i] for i in picked), 6)
    res["total_salary"] = round(sum(salaries[i] for i in picked), 6)
    res["remaining_cap"] = round(budget - res["total_salary"], 6)
    res["roster_size"] = len(picked)
    res["constraints_ok"] = (res["feasible"] and len(picked) == k
                             and res["total_salary"] <= budget + EPS)
    res["method"] = "knapsack_roster"
    return res