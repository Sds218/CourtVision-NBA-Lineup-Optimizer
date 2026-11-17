
import pandas as pd

from modules.search_filters import filter_players, normalize_name


def sample_players():
    return pd.DataFrame({
        "Player": [
            "Nikola Jokić",
            "Jayson Tatum",
            "Stephen Curry",
            "Victor Wembanyama",
        ],
        "Position": [
            "Center",
            "Forward-Guard",
            "Guard",
            "Center",
        ],
        "Performance": [91.3, 85.0, 80.0, 88.0],
    })


def test_search_ignores_accents():
    players = sample_players()
    result = filter_players(
        players, players["Position"].unique(), "Jokic"
    )
    assert result["Player"].tolist() == ["Nikola Jokić"]


def test_search_is_case_insensitive():
    players = sample_players()
    result = filter_players(
        players, players["Position"].unique(), "tAtUm"
    )
    assert result["Player"].tolist() == ["Jayson Tatum"]


def test_search_partial_name():
    players = sample_players()
    result = filter_players(
        players, players["Position"].unique(), "Steph"
    )
    assert result["Player"].tolist() == ["Stephen Curry"]


def test_filter_by_position():
    players = sample_players()
    result = filter_players(players, ["Center"])
    assert result["Player"].tolist() == [
        "Nikola Jokić",
        "Victor Wembanyama",
    ]


def test_search_with_no_matches():
    players = sample_players()
    result = filter_players(
        players, players["Position"].unique(), "NotAPlayer"
    )
    assert result.empty


def test_normalize_name():
    assert normalize_name("JOKIĆ") == "jokic"
