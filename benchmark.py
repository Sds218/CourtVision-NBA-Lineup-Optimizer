"""Timing for the report: DP vs greedy, and merge sort vs built-in sort."""
import random

from modules.knapsack import knapsack_lineup, greedy_lineup
from modules.ranking import benchmark_sort

K = 5
BUDGET = 100


def make_data(n):
    rng = random.Random(n)
    scores = [rng.uniform(10, 100) for _ in range(n)]
    salaries = [round(rng.uniform(1, 45), 1) for _ in range(n)]
    return scores, salaries


print("=== Knapsack DP vs Greedy (k=5, budget=$100M) ===")
print(f"{'n':>5} {'DP (s)':>9} {'Greedy (s)':>11} {'DP states':>10} "
      f"{'DP score':>9} {'Greedy score':>13}")
for n in [50, 100, 200, 450]:
    scores, salaries = make_data(n)
    dp = knapsack_lineup(scores, salaries, BUDGET, K)
    gr = greedy_lineup(scores, salaries, BUDGET, K)
    print(f"{n:>5} {dp['runtime_s']:>9.4f} {gr['runtime_s']:>11.6f} "
          f"{dp['dp_states']:>10} {dp['total_score']:>9.1f} "
          f"{gr['total_score']:>13.1f}")


def make_players(n):
    rng = random.Random(n)
    return [{"name": str(i), "salary": rng.randint(1, 40),
             "score": rng.random()} for i in range(n)]


print("\n=== Merge sort vs built-in sorted() ===")
print(f"{'n':>7} {'Merge (s)':>10} {'Built-in (s)':>13}")
for n, t_merge, t_builtin in benchmark_sort([1000, 10000, 100000], make_players, 3):
    print(f"{n:>7} {t_merge:>10.4f} {t_builtin:>13.4f}")