import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from modules.lineup import optimize_with_locked, similar_players


def make_df(rows):
    return pd.DataFrame(rows, columns=["Player", "Salary", "Performance",
                                       "Points", "Rebounds", "Assists"])


def test_locked_player_always_on_roster():
    # Star is a bad value, so a normal optimizer would skip him
    df = make_df([("Star", 50, 40, 20, 8, 5), ("A", 10, 30, 18, 7, 4),
                  ("B", 10, 30, 17, 6, 4), ("C", 10, 30, 16, 6, 3),
                  ("D", 10, 30, 15, 5, 3)])
    out = optimize_with_locked(df, 100, 3, ["Star"])
    names = out["dp"]["lineup"]["Player"].tolist()
    assert "Star" in names and len(names) == 3
    assert out["dp"]["constraints_ok"]
    assert out["dp"]["total_salary"] <= 100


def test_matches_brute_force_with_locked():
    rng = random.Random(11)
    for _ in range(100):
        n = rng.randint(3, 8)
        rows = [(f"P{i}", rng.randint(1, 20), rng.randint(0, 50),
                 1, 1, 1) for i in range(n)]
        df = make_df(rows)
        k = rng.randint(1, min(4, n))
        budget = rng.randint(5, 60)
        out = optimize_with_locked(df, budget, k, ["P0"])
        best = None
        for combo in itertools.combinations(range(n), k):
            if 0 not in combo:
                continue
            if sum(rows[i][1] for i in combo) <= budget:
                tot = sum(rows[i][2] for i in combo)
                best = tot if best is None else max(best, tot)
        if out["error"]:
            assert best is None
        elif best is None:
            assert out["dp"]["feasible"] is False
        else:
            assert out["dp"]["feasible"] and out["dp"]["total_score"] == best


def test_locked_over_budget_gives_error():
    df = make_df([("Star", 60, 40, 20, 8, 5), ("A", 10, 30, 18, 7, 4)])
    out = optimize_with_locked(df, 50, 2, ["Star"])
    assert out["error"]


def test_too_many_locked():
    df = make_df([("S1", 10, 40, 20, 8, 5), ("S2", 10, 40, 20, 8, 5),
                  ("A", 10, 30, 18, 7, 4)])
    out = optimize_with_locked(df, 100, 1, ["S1", "S2"])
    assert out["error"]


def test_no_locked_players_behaves_normally():
    df = make_df([("A", 5, 10, 1, 1, 1), ("B", 4, 7, 1, 1, 1),
                  ("C", 3, 6, 1, 1, 1)])
    out = optimize_with_locked(df, 7, 2, [])
    assert sorted(out["dp"]["lineup"]["Player"]) == ["B", "C"]
    assert out["dp"]["total_score"] == 13


def test_similar_players_closest_first_and_excludes():
    df = make_df([("Star", 50, 50, 20, 10, 5), ("Twin", 30, 45, 20, 10, 5),
                  ("Near", 20, 40, 18, 9, 5), ("Far", 10, 10, 5, 2, 1),
                  ("Other", 40, 48, 20, 10, 5)])
    sim = similar_players(df, "Star", exclude={"Star", "Other"}, top_n=2)
    assert sim["Player"].tolist() == ["Twin", "Near"]
    assert sim["Similarity %"].iloc[0] > sim["Similarity %"].iloc[1]


def test_similar_unknown_target():
    df = make_df([("A", 5, 10, 1, 1, 1)])
    try:
        similar_players(df, "Nobody")
    except ValueError:
        return
    assert False