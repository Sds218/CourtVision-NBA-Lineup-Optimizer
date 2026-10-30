import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.scoring import composite_scores, min_max
from modules.ranking import merge_sort, rank_players, rank_key


def test_min_max():
    assert min_max([2, 4, 6]) == [0.0, 0.5, 1.0]
    assert min_max([5, 5]) == [0.0, 0.0]          # constant column -> all 0


def test_best_in_every_stat_scores_100():
    stats = {"Points": [10, 30], "Assists": [1, 9], "Rebounds": [2, 8]}
    assert composite_scores(stats) == [0.0, 100.0]


def test_ignores_columns_without_a_weight():
    stats = {"Points": [20, 25, 30], "Foo": [1, 2, 3]}   # Foo has no weight
    s = composite_scores(stats)
    assert all(0 <= x <= 100 for x in s)
    assert s[0] < s[1] < s[2]


def test_turnover_penalty():
    stats = {"Points": [20, 20], "Turnovers": [1, 5]}
    s = composite_scores(stats)
    assert s[0] > s[1]                            # fewer turnovers is better


def test_empty_input():
    assert composite_scores({}) == []
    assert composite_scores({"Points": []}) == []


def test_merge_sort_matches_builtin():
    rng = random.Random(1)
    for n in [0, 1, 2, 3, 10, 101]:
        data = [{"name": f"P{i}", "salary": rng.randint(1, 5),
                 "score": rng.randint(0, 5)} for i in range(n)]
        assert merge_sort(data) == sorted(data, key=rank_key)


def test_tie_break_order():
    data = [
        {"name": "B", "salary": 10, "score": 50},
        {"name": "A", "salary": 10, "score": 50},
        {"name": "C", "salary": 5, "score": 50},
        {"name": "D", "salary": 1, "score": 60},
    ]
    names = [p["name"] for p in rank_players(data)]
    assert names == ["D", "C", "A", "B"]   # score desc, salary asc, name A-Z


def test_input_not_modified():
    data = [{"name": "x", "salary": 1, "score": 1},
            {"name": "y", "salary": 1, "score": 9}]
    before = [dict(p) for p in data]
    merge_sort(data)
    assert data == before