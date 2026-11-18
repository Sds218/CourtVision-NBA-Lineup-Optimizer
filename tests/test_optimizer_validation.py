
import pandas as pd

from modules.lineup import optimize_with_locked, build_roster


def sample_players():
    return pd.DataFrame({
        "Player": ["A", "B", "C", "D", "E", "F"],
        "Position": [
            "Guard", "Guard", "Forward",
            "Forward", "Center", "Center"
        ],
        "Performance": [80, 90, 70, 95, 60, 75],
        "Salary": [20, 25, 15, 30, 10, 18],
    })


def test_lineup_respects_salary_cap():
    result = optimize_with_locked(sample_players(), 100, 5, [])

    assert result["error"] is None
    assert result["dp"]["constraints_ok"]
    assert result["dp"]["total_salary"] <= 100
    assert result["dp"]["roster_size"] == 5


def test_locked_player_is_retained():
    result = optimize_with_locked(sample_players(), 120, 5, ["A"])

    assert result["error"] is None
    assert "A" in result["dp"]["lineup"]["Player"].tolist()
    assert result["dp"]["constraints_ok"]


def test_locked_player_exceeds_budget():
    result = optimize_with_locked(sample_players(), 10, 5, ["A"])

    assert result["error"] is not None
    assert "over" in result["error"].lower()


def test_too_many_locked_players():
    result = optimize_with_locked(
        sample_players(), 120, 2, ["A", "B", "C"]
    )

    assert result["error"] is not None
    assert "spots" in result["error"].lower()


def test_roster_has_correct_size_and_no_duplicates():
    result = build_roster(
        sample_players(), cap=120,
        starters=4, bench=2, locked_names=["A"]
    )

    assert result["error"] is None
    assert len(result["starters"]) == 4
    assert len(result["bench"]) == 2

    names = pd.concat([
        result["starters"]["Player"],
        result["bench"]["Player"],
    ]).tolist()

    assert len(names) == len(set(names))
    assert "A" in names


def test_roster_rejects_insufficient_players():
    result = build_roster(
        sample_players(), cap=120,
        starters=5, bench=3
    )

    assert result["error"] is not None
    assert "available" in result["error"].lower()
