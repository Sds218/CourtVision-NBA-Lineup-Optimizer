
import pandas as pd
from modules.lineup import optimize_with_locked, build_roster


def sample_players():
    return pd.DataFrame({
        "Player": ["A", "B", "C", "D", "E", "F"],
        "Position": ["PG", "SG", "SF", "PF", "C", "PG"],
        "Salary": [20, 25, 15, 30, 10, 18],
        "Performance": [80, 90, 70, 95, 60, 75]
    })


def test_lineup_size_and_budget():
    result = optimize_with_locked(sample_players(), 120, 5, [])

    assert result["error"] is None
    assert result["dp"]["feasible"]
    assert result["dp"]["roster_size"] == 5
    assert result["dp"]["total_salary"] <= 120


def test_locked_player_is_selected():
    result = optimize_with_locked(sample_players(), 120, 5, ["A"])

    assert result["error"] is None
    assert "A" in result["dp"]["lineup"]["Player"].tolist()


def test_insufficient_budget():
    result = optimize_with_locked(sample_players(), 20, 5, [])

    assert result["error"] is None
    assert result["dp"]["feasible"] is False


def test_full_roster_integration():
    result = build_roster(
        sample_players(),
        cap=120,
        starters=5,
        bench=1,
        locked_names=["A"]
    )

    assert result["error"] is None
    assert len(result["starters"]) == 5
    assert len(result["bench"]) == 1
    assert "A" in pd.concat([
        result["starters"], result["bench"]
    ])["Player"].tolist()
    assert result["result"]["total_salary"] <= 120
