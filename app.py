import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from modules.config import (
    LINEUP_SIZE, SALARY_CAP_M, DEFAULT_BUDGET_M, UNTOUCHABLE
)
from modules.scoring import add_performance
from modules.ranking import rank_players
from modules.lineup import optimize_with_locked, similar_players

# PAGE CONFIGURATION
st.set_page_config(
    page_title="CourtVision | NBA Lineup Optimizer",
    page_icon="🏀",
    layout="wide"
)

# DEMONSTRATION DATA
# Replaced by data/nba_players.csv once the team's verified dataset exists.
@st.cache_data
def load_players():
    data_file = Path("data/nba_players.csv")

    if data_file.exists():
        return pd.read_csv(data_file), False

    sample = {
        "Player": [
            "Demo Guard A", "Demo Guard B",
            "Demo Forward A", "Demo Forward B",
            "Demo Center A", "Demo Center B",
            "Demo Guard C", "Demo Forward C",
            "Jayson Tatum"
        ],
        "Position": [
            "PG", "SG", "SF", "PF",
            "C", "C", "PG", "SF",
            "F"
        ],
        "Salary": [32, 25, 38, 22, 35, 19, 16, 28, 58.4],
        "Points": [28, 23, 30, 18, 26, 15, 17, 24, 21.8],
        "Rebounds": [5, 4, 8, 9, 12, 10, 3, 7, 10.0],
        "Assists": [9, 6, 5, 3, 4, 2, 8, 4, 5.3]
    }

    return pd.DataFrame(sample), True


players, demo_mode = load_players()

# PLAYER PERFORMANCE SCORE
# Composite 0-100 score from modules/scoring.py
if "Performance" not in players.columns:
    players = add_performance(players)

# UNTOUCHABLE FLAG
# Franchise players are shown everywhere, marked with a lock.
players["Status"] = players["Player"].apply(
    lambda name: "🔒 Untouchable" if name in UNTOUCHABLE else ""
)

required_columns = [
    "Player", "Position", "Salary", "Points",
    "Rebounds", "Assists", "Performance"
]

missing = [c for c in required_columns
           if c not in players.columns]

if missing:
    st.error(f"Missing dataset columns: {missing}")
    st.stop()

# HEADER
st.title("🏀 CourtVision")
st.subheader("NBA Analytics & Lineup Optimizer")

st.write(
    "Explore basketball performance data and build "
    "lineups using 0/1 Knapsack Dynamic Programming."
)

if demo_mode:
    st.warning(
        "Demonstration mode: the Demo players are fictional. "
        "Jayson Tatum's line is real (2025-26, 16 games after injury)."
    )
else:
    st.info("Player dataset loaded from data/nba_players.csv")

st.divider()

# SIDEBAR CONTROLS
st.sidebar.title("⚙️ Lineup Settings")

budget = st.sidebar.slider(
    "Salary Budget ($ Millions)",
    min_value=20,
    max_value=200,
    value=DEFAULT_BUDGET_M,
    step=5
)
st.sidebar.caption(f"2026-27 NBA salary cap: ${SALARY_CAP_M}M")

lineup_size = LINEUP_SIZE
st.sidebar.write(f"**Lineup size:** {lineup_size} players (fixed)")

positions = st.sidebar.multiselect(
    "Filter by Position",
    options=sorted(players["Position"].unique()),
    default=sorted(players["Position"].unique())
)

search = st.sidebar.text_input(
    "Search Player",
    placeholder="Enter player name"
)

# FILTER DATA
filtered = players[
    players["Position"].isin(positions)
].copy()

if search:
    filtered = filtered[
        filtered["Player"].str.contains(
            search, case=False, na=False, regex=False
        )
    ]

# SUMMARY METRICS
col1, col2, col3, col4 = st.columns(4)

col1.metric("Salary Budget", f"${budget}M")
col2.metric("Requested Lineup", lineup_size)
col3.metric("Available Players", len(filtered))
col4.metric(
    "Average Performance",
    f"{filtered['Performance'].mean():.1f}"
    if not filtered.empty else "N/A"
)

st.divider()

# PLAYER STATISTICS
st.header("📊 Player Statistics")

untouchables_here = [
    name for name in filtered["Player"] if name in UNTOUCHABLE
]
if untouchables_here:
    st.warning(
        "🔒 Untouchable franchise player(s) in this pool: "
        + ", ".join(untouchables_here)
    )

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

# ANALYTICS CHARTS
st.header("📈 Player Analytics")

if not filtered.empty:
    left, right = st.columns(2)

    with left:
        fig_performance = px.bar(
            filtered.sort_values(
                "Performance", ascending=False
            ),
            x="Player",
            y="Performance",
            color="Position",
            title="Player Performance Comparison"
        )
        st.plotly_chart(
            fig_performance,
            use_container_width=True
        )

    with right:
        fig_salary = px.scatter(
            filtered,
            x="Salary",
            y="Performance",
            color="Position",
            size="Points",
            hover_name="Player",
            title="Salary vs Player Performance",
            labels={"Salary": "Salary ($ Millions)"}
        )
        st.plotly_chart(
            fig_salary,
            use_container_width=True
        )
else:
    st.info("No players match your filters.")

st.divider()

# PLAYER RANKINGS (merge sort from modules/ranking.py)
st.header("🏅 Player Rankings")

if not filtered.empty:
    ranked = rank_players([
        {"name": row.Player, "salary": row.Salary, "score": row.Performance}
        for row in filtered.itertuples()
    ])
    ranked_df = pd.DataFrame(ranked)[["rank", "name", "score", "salary"]]
    ranked_df["status"] = ranked_df["name"].apply(
        lambda name: "🔒 Untouchable" if name in UNTOUCHABLE else ""
    )
    st.dataframe(
        ranked_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No players match your filters.")

st.divider()

# LINEUP OPTIMIZER INTERFACE
st.header("🏆 NBA Lineup Optimizer")

st.write(
    "The optimizer selects players to maximize "
    "performance while respecting the salary budget. "
    "Untouchable players are always kept on the roster."
)

st.write("**Current settings:**")
st.write(f"Salary Budget: ${budget} Million")
st.write(f"Requested Players: {lineup_size}")

# The button only fires once, so remember that it was pressed. Otherwise
# using the menu below would rerun the page and hide the results.
if st.button("🚀 Optimize Lineup", type="primary"):
    st.session_state["run_optimizer"] = True

if st.session_state.get("run_optimizer"):
    pool = filtered.reset_index(drop=True)
    locked_names = [n for n in pool["Player"] if n in UNTOUCHABLE]

    if len(pool) < lineup_size:
        st.error(
            "Not enough players match your current filters."
        )
    else:
        out = optimize_with_locked(pool, budget, lineup_size, locked_names)

        if out["error"]:
            st.error(out["error"])
        elif not out["dp"]["feasible"]:
            st.error(
                "No lineup of that size fits the salary budget. "
                "Raise the budget or change the position filter."
            )
        else:
            dp, greedy = out["dp"], out["greedy"]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Score", f"{dp['total_score']:.1f}")
            m2.metric("Total Salary", f"${dp['total_salary']:.1f}M")
            m3.metric("Remaining Cap", f"${dp['remaining_cap']:.1f}M")
            m4.metric(
                "Constraints",
                "All passed" if dp["constraints_ok"] else "FAILED"
            )

            if locked_names:
                st.warning(
                    "🔒 UNTOUCHABLE on roster: "
                    + ", ".join(locked_names)
                    + ". Untouchable players are always kept; the optimizer "
                    "filled the remaining spots around them."
                )

            st.subheader("Selected Lineup")
            st.dataframe(
                dp["lineup"].sort_values("Performance", ascending=False),
                use_container_width=True,
                hide_index=True
            )

            # SIMILAR PLAYERS MENU
            if locked_names:
                st.subheader("🔍 Similar Players (not untouchable)")
                target = st.selectbox(
                    "View players with a profile similar to:",
                    locked_names,
                    key="similar_target"
                )
                similar = similar_players(
                    players, target, exclude=UNTOUCHABLE, top_n=3
                )
                similar["In lineup"] = similar["Player"].apply(
                    lambda n: "Yes" if n in set(dp["lineup"]["Player"])
                    else "No"
                )
                st.caption(
                    "Closest stat profile (points, rebounds, assists "
                    "and any other scoring stats in the data), "
                    "searching all players."
                )
                st.dataframe(
                    similar,
                    use_container_width=True,
                    hide_index=True
                )

            st.subheader("Knapsack DP vs Greedy Baseline")
            st.dataframe(
                pd.DataFrame([
                    {
                        "Method": "0/1 Knapsack DP",
                        "Total Score": dp["total_score"],
                        "Total Salary ($M)": dp["total_salary"],
                        "Players": dp["roster_size"],
                        "Valid": dp["constraints_ok"],
                        "Runtime (ms)": round(dp["runtime_s"] * 1000, 3),
                    },
                    {
                        "Method": "Greedy (score / salary)",
                        "Total Score": greedy["total_score"],
                        "Total Salary ($M)": greedy["total_salary"],
                        "Players": greedy["roster_size"],
                        "Valid": greedy["constraints_ok"],
                        "Runtime (ms)": round(greedy["runtime_s"] * 1000, 3),
                    },
                ]),
                use_container_width=True,
                hide_index=True
            )

            if not greedy["constraints_ok"]:
                st.warning(
                    "Greedy could not build a full valid lineup "
                    "under these constraints."
                )
            elif greedy["total_score"] < dp["total_score"]:
                st.info(
                    "Greedy found a worse lineup: "
                    f"{greedy['total_score']:.1f} vs "
                    f"{dp['total_score']:.1f} for the DP."
                )

st.divider()
st.caption(
    "CourtVision | CSCE 4110 Algorithms "
    "| NBA Analytics & Lineup Optimization"
)