"""Sorting / ranking: merge sort, O(n log n), stable.

Tie-break: higher score first, then LOWER salary, then name A-Z.
"""
import time


def rank_key(player):
    """Sort key: smaller key = better rank."""
    return (-player["score"], player["salary"], str(player["name"]))


def merge_sort(items, key=rank_key):
    """Return a NEW list sorted ascending by key(item). Input is not changed."""
    n = len(items)
    if n <= 1:
        return list(items)
    mid = n // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left, right, key):
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        # <= takes from the left on ties, which makes the sort stable
        if key(left[i]) <= key(right[j]):
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def rank_players(players):
    """players: list of dicts with 'name', 'salary', 'score'.
    Returns a new list, best first, with a 'rank' field (1 = best)."""
    ordered = merge_sort(players)
    return [dict(p, rank=r) for r, p in enumerate(ordered, start=1)]


def benchmark_sort(sizes, make_players, repeats=5):
    """Time merge_sort vs Python's sorted() for growing sizes.
    Returns rows of (n, merge_seconds, builtin_seconds)."""
    rows = []
    for n in sizes:
        data = make_players(n)
        t_merge = t_builtin = 0.0
        for _ in range(repeats):
            t0 = time.perf_counter()
            merge_sort(data)
            t_merge += time.perf_counter() - t0
            t0 = time.perf_counter()
            sorted(data, key=rank_key)
            t_builtin += time.perf_counter() - t0
        rows.append((n, t_merge / repeats, t_builtin / repeats))
    return rows