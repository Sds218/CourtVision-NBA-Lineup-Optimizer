import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.knapsack import roster_lineup, knapsack_lineup


def brute_force(scores, salaries, budget, starters, bench, bw):
    """Try every roster; best 'starters' scores count fully, rest count bw."""
    k = starters + bench
    best = None
    for combo in itertools.combinations(range(len(scores)), k):
        if sum(salaries[i] for i in combo) <= budget:
            v = sorted((scores[i] for i in combo), reverse=True)
            total = sum(v[:starters]) + bw * sum(v[starters:])
            if best is None or total > best:
                best = total
    return best


def test_matches_brute_force():
    rng = random.Random(5)
    for _ in range(400):
        n = rng.randint(2, 9)
        starters, bench = rng.randint(0, 3), rng.randint(0, 3)
        if starters + bench > n:
            continue
        scores = [rng.randint(0, 40) for _ in range(n)]
        salaries = [rng.randint(1, 15) for _ in range(n)]
        budget = rng.randint(5, 60)
        bw = rng.choice([0, 0.25, 0.4, 0.5, 1.0])
        expected = brute_force(scores, salaries, budget, starters, bench, bw)
        r = roster_lineup(scores, salaries, budget, starters, bench, bw, scale=1)
        if expected is None:
            assert r["feasible"] is False
        else:
            assert r["feasible"]
            assert abs(r["weighted_score"] - expected) < 1e-6
            assert r["total_salary"] <= budget
            assert len(r["starters"]) == starters and len(r["bench"]) == bench


def test_starters_outscore_bench():
    scores = [50, 40, 30, 20, 10, 5]
    salaries = [5, 5, 5, 5, 5, 5]
    r = roster_lineup(scores, salaries, 100, 2, 2, 0.4, scale=1)
    assert min(scores[i] for i in r["starters"]) >= max(scores[i] for i in r["bench"])


def test_bench_weight_one_equals_plain_knapsack():
    scores, salaries = [10, 7, 6, 9, 3], [5, 4, 3, 6, 2]
    r = roster_lineup(scores, salaries, 12, 2, 1, 1.0, scale=1)
    plain = knapsack_lineup(scores, salaries, 12, 3, scale=1)
    assert r["weighted_score"] == plain["total_score"]


def test_infeasible_and_bad_weight():
    assert roster_lineup([1, 2], [50, 60], 10, 1, 1, 0.4, scale=1)["feasible"] is False
    try:
        roster_lineup([1, 2], [1, 1], 10, 1, 1, 1.5)
    except ValueError:
        return
    assert False