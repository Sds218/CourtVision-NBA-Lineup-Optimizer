
"""Member 3: DP vs Greedy benchmarking and validation."""

import csv
import random
from pathlib import Path

from modules.knapsack import knapsack_lineup, greedy_lineup


def make_data(n):
    rng = random.Random(n)
    scores = [rng.uniform(10, 100) for _ in range(n)]
    salaries = [round(rng.uniform(1, 45), 1) for _ in range(n)]
    return scores, salaries


def run_benchmarks():
    results = []
    lineup_size = 5

    for n in [50, 100, 200]:
        scores, salaries = make_data(n)

        for budget in [100, 150, 200]:
            dp = knapsack_lineup(scores, salaries, budget, lineup_size)
            greedy = greedy_lineup(scores, salaries, budget, lineup_size)

            for name, result in [("DP", dp), ("Greedy", greedy)]:
                valid = (
                    result["feasible"]
                    and result["roster_size"] == lineup_size
                    and result["total_salary"] <= budget + 1e-9
                )

                results.append({
                    "Players": n,
                    "Budget": budget,
                    "Algorithm": name,
                    "Score": result["total_score"],
                    "Salary": result["total_salary"],
                    "Runtime_Seconds": result["runtime_s"],
                    "Feasible": result["feasible"],
                    "Valid": valid,
                })

                print(
                    f"n={n}, budget=${budget}M, "
                    f"{name}: score={result['total_score']:.2f}, "
                    f"salary=${result['total_salary']:.2f}M, "
                    f"time={result['runtime_s']:.6f}s, "
                    f"valid={valid}"
                )

    output = Path("evidence/benchmark_results.csv")
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved {len(results)} results to {output}")


if __name__ == "__main__":
    run_benchmarks()
