import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.knapsack import roster_lineup, knapsack_lineup


def brute_force(scores, salaries, budget, starters, bench, bw, locked=()):
    """Try every roster; best 'starters' scores count fully, rest count bw."""
    k = starters + bench
    best = None
    for combo in itertools.combinations(range(len(scores)), k):
        if not all(l in combo for l in locked):
            continue
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


# ---- locked players and position filter ----
def test_locked_player_is_kept_even_if_poor_value():
    scores = [90, 80, 70, 60, 50, 10]
    salaries = [10, 10, 10, 10, 10, 30]       # last player: bad value
    r = roster_lineup(scores, salaries, 100, 2, 2, 0.4, scale=1, locked=[5])
    assert 5 in r["selected"] and r["feasible"]
    assert r["total_salary"] <= 100


def test_locked_that_does_not_fit_is_infeasible():
    r = roster_lineup([5, 5, 5], [10, 10, 90], 50, 1, 1, 0.4, scale=1, locked=[2])
    assert r["feasible"] is False and r["selected"] == []


def test_allowed_restricts_other_spots():
    scores = [50, 40, 30, 20]
    salaries = [5, 5, 5, 5]
    r = roster_lineup(scores, salaries, 100, 1, 1, 0.4, scale=1,
                      locked=[3], allowed={2})
    assert sorted(r["selected"]) == [2, 3]


def test_locked_matches_brute_force():
    rng = random.Random(21)
    for _ in range(200):
        n = rng.randint(3, 8)
        starters, bench = rng.randint(1, 3), rng.randint(0, 2)
        k = starters + bench
        if k > n:
            continue
        scores = [rng.randint(0, 40) for _ in range(n)]
        salaries = [rng.randint(1, 15) for _ in range(n)]
        budget = rng.randint(8, 60)
        locked = rng.sample(range(n), rng.randint(0, min(2, k)))
        best = brute_force(scores, salaries, budget, starters, bench, 0.4, locked)
        r = roster_lineup(scores, salaries, budget, starters, bench, 0.4,
                          scale=1, locked=locked)
        if best is None:
            assert r["feasible"] is False
        else:
            assert r["feasible"] and abs(r["weighted_score"] - best) < 1e-6
            assert all(l in r["selected"] for l in locked)