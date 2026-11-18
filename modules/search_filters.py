
import unicodedata


def normalize_name(name):
    text = unicodedata.normalize("NFKD", str(name))
    return "".join(
        char for char in text
        if not unicodedata.combining(char)
    ).casefold()


def filter_players(players, positions, search=""):
    filtered = players[
        players["Position"].isin(positions)
    ].copy()

    if search:
        normalized_search = normalize_name(search)

        filtered = filtered[
            filtered["Player"].apply(
                lambda name: normalized_search in normalize_name(name)
            )
        ]

    return filtered
