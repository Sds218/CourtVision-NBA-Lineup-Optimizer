import itertools
import os
import random
import sys

# lets the tests import the modules/ folder from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.knapsack import knapsack_lineup, greedy_lineup


def brute_force(scores, salaries, budget, k):
    """Try every group of k players. Slow but obviously correct."""
    best = None
    for combo in itertools.combinations(range(len(scores)), k):
        if sum(salaries[i] for i in combo) <= budget:
            total = sum(scores[i] for i in combo)
            if best is None or total > best:
                best = total
    return best


def raises(exc, fn, *args):
    try:
        fn(*args)
    except exc:
        return True
    return False


# ---- hand-checkable examples ----
def test_hand_example():
    # only players 1 and 2 fit together (4 + 3 = 7); score 7 + 6 = 13
    r = knapsack_lineup([10, 7, 6], [5, 4, 3], 7, 2, scale=1)
    assert r["selected"] == [1, 2]
    assert r["total_score"] == 13
    assert r["total_salary"] == 7 and r["remaining_cap"] == 0


def test_greedy_fails_to_fill_roster():
    scores, salaries = [19, 12, 12], [10, 8, 8]
    dp = knapsack_lineup(scores, salaries, 16, 2, scale=1)
    gr = greedy_lineup(scores, salaries, 16, 2)
    assert dp["selected"] == [1, 2] and dp["total_score"] == 24
    assert gr["feasible"] is False


def test_greedy_valid_but_worse():
    scores, salaries = [6, 9, 8], [2, 5, 5]
    dp = knapsack_lineup(scores, salaries, 10, 2, scale=1)
    gr = greedy_lineup(scores, salaries, 10, 2)
    assert dp["total_score"] == 17
    assert gr["total_score"] == 15


# ---- random check against brute force ----
def test_matches_brute_force():
    rng = random.Random(4110)
    for _ in range(300):
        n = rng.randint(1, 9)
        k = rng.randint(0, n)
        scores = [rng.randint(0, 50) for _ in range(n)]
        salaries = [rng.randint(0, 20) for _ in range(n)]
        budget = rng.randint(0, 60)
        expected = brute_force(scores, salaries, budget, k)
        r = knapsack_lineup(scores, salaries, budget, k, scale=1)
        if expected is None:
            assert r["feasible"] is False
        else:
            assert r["feasible"] is True
            assert r["total_score"] == expected
            assert r["constraints_ok"]


# ---- constraints hold with decimal salaries ----
def test_never_exceeds_cap_and_no_duplicates():
    rng = random.Random(7)
    for _ in range(100):
        n = rng.randint(5, 12)
        k = rng.randint(1, 5)
        scores = [rng.uniform(0, 100) for _ in range(n)]
        salaries = [round(rng.uniform(1, 40), 2) for _ in range(n)]
        budget = rng.uniform(20, 150)
        r = knapsack_lineup(scores, salaries, budget, k)
        if r["feasible"]:
            assert r["total_salary"] <= budget
            assert len(set(r["selected"])) == k == r["roster_size"]


# ---- edge cases ----
def test_empty_pool():
    r = knapsack_lineup([], [], 100, 3)
    assert r["feasible"] is False and r["selected"] == []


def test_k_zero():
    r = knapsack_lineup([5, 6], [1, 2], 10, 0)
    assert r["feasible"] is True and r["selected"] == []


def test_cap_too_low():
    r = knapsack_lineup([5, 6], [10, 20], 5, 1, scale=1)
    assert r["feasible"] is False and r["selected"] == []


def test_cap_very_high_takes_top_scores():
    r = knapsack_lineup([3, 9, 1, 7, 5], [1, 1, 1, 1, 1], 10_000, 2, scale=1)
    assert r["selected"] == [1, 3] and r["total_score"] == 16


def test_k_larger_than_pool():
    r = knapsack_lineup([1, 2], [1, 1], 100, 5)
    assert r["feasible"] is False


def test_equal_scores():
    r = knapsack_lineup([5, 5, 5], [3, 2, 4], 6, 2, scale=1)
    assert r["feasible"] and r["total_score"] == 10
    assert r["total_salary"] <= 6


def test_salary_exactly_at_cap():
    r = knapsack_lineup([10, 10], [3, 4], 7, 2, scale=1)
    assert r["feasible"] and r["remaining_cap"] == 0


def test_zero_salary_player():
    r = knapsack_lineup([4, 8], [0, 5], 5, 2, scale=1)
    assert r["feasible"] and r["total_score"] == 12


def test_bad_input():
    assert raises(ValueError, knapsack_lineup, [1], [-3], 10, 1)
    assert raises(ValueError, knapsack_lineup, [1, 2], [1], 10, 1)
    assert raises(ValueError, knapsack_lineup, [1], [1], -5, 1)
    assert raises(ValueError, knapsack_lineup, [1], [1], 5, -1)
    assert raises(ValueError, knapsack_lineup, [1], [float("nan")], 5, 1)