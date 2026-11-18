import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

import unicodedata

from modules.search_filters import filter_players


from modules.config import (
    LINEUP_SIZE, SALARY_CAP_M, DEFAULT_BUDGET_M, UNTOUCHABLE
)
from modules.scoring import add_performance
from modules.ranking import rank_players
from modules.untouchable import find_untouchables
from modules.lineup import (
    optimize_with_locked, similar_players, build_roster, greedy_roster
)


def money(text):
    """Streamlit treats text between two $ signs as math, so escape them."""
    return text.replace("$", "\\$")


# PLAYER PHOTOS (official NBA headshots, looked up by name)
# Players that are not found simply get no picture.
def _norm(text):
    """Lowercase and drop accents so 'Jokić' matches 'Jokic'."""
    plain = "".join(
        c for c in unicodedata.normalize("NFKD", str(text))
        if not unicodedata.combining(c)
    )
    return plain.lower().strip()


@st.cache_resource
def headshot_lookup():
    """name -> NBA player id, only for names that are unique."""
    try:
        from nba_api.stats.static import players as nba_static
        rows = nba_static.get_players()
    except Exception:
        return {}
    ids, counts = {}, {}
    for p in rows:
        key = _norm(p["full_name"])
        ids[key] = p["id"]
        counts[key] = counts.get(key, 0) + 1
    return {k: v for k, v in ids.items() if counts[k] == 1}


def headshot(name):
    pid = headshot_lookup().get(_norm(name))
    if pid is None:
        return None
    return f"https://cdn.nba.com/headshots/nba/latest/260x190/{pid}.png"


PHOTO_CONFIG = {"Photo": st.column_config.ImageColumn("", width="small")}


def add_photos(df, name_col="Player"):
    """Copy of df with a small Photo column first (only if any photo)."""
    out = df.copy()
    urls = out[name_col].apply(headshot)
    if urls.notna().any():
        out.insert(0, "Photo", urls)
    return out


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
            "Jayson Tatum",
            "Demo Role A", "Demo Role B", "Demo Role C", "Demo Role D",
            "Demo Role E", "Demo Role F", "Demo Role G", "Demo Role H"
        ],
        "Position": [
            "PG", "SG", "SF", "PF",
            "C", "C", "PG", "SF",
            "F",
            "SG", "SF", "PF", "C",
            "PG", "SF", "PF", "C"
        ],
        "Salary": [32, 25, 38, 22, 35, 19, 16, 28, 58.4,
                   12, 8, 6, 5, 9, 4, 7, 3],
        "Points": [28, 23, 30, 18, 26, 15, 17, 24, 21.8,
                   12, 10, 9, 7, 11, 8, 9, 5],
        "Rebounds": [5, 4, 8, 9, 12, 10, 3, 7, 10.0,
                     3, 4, 6, 6, 2, 5, 7, 5],
        "Assists": [9, 6, 5, 3, 4, 2, 8, 4, 5.3,
                    3, 2, 1, 1, 4, 1, 1, 1]
    }

    return pd.DataFrame(sample), True


players, demo_mode = load_players()

# PLAYER PERFORMANCE SCORE
# Composite 0-100 score from modules/scoring.py
if "Performance" not in players.columns:
    players = add_performance(players)

# UNTOUCHABLE LABEL (caution only, nobody is forced onto a roster).
# Config names are manual overrides; the rest comes from the data
# (best player on a team and in the league's top 10%).
UNTOUCHABLE_RANKED = find_untouchables(players, manual=UNTOUCHABLE)
UNTOUCHABLE = set(UNTOUCHABLE_RANKED)

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
filtered = filter_players(players, positions, search)

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
        "🔒 Untouchable (franchise-level) player(s) in this pool: "
        + ", ".join(untouchables_here)
    )

st.dataframe(
    add_photos(filtered),
    column_config=PHOTO_CONFIG,
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
        add_photos(ranked_df, "name"),
        column_config=PHOTO_CONFIG,
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
    "Players marked 🔒 Untouchable only trigger a caution; "
    "they are never forced onto the lineup."
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

    if len(pool) < lineup_size:
        st.error(
            "Not enough players match your current filters."
        )
    else:
        out = optimize_with_locked(pool, budget, lineup_size, [])

        if out["error"]:
            st.error(money(out["error"]))
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

            st.subheader("Selected Lineup")
            lineup_df = dp["lineup"].copy()
            st.dataframe(

                add_photos(
                    lineup_df.sort_values("Performance", ascending=False)
                ),
                column_config=PHOTO_CONFIG,
                use_container_width=True,

                dp["lineup"].sort_values("Performance", ascending=False),
                width="stretch",     

                hide_index=True
            )

            # CAUTION + SIMILAR PLAYERS for untouchables the optimizer picked
            flagged = [n for n in lineup_df["Player"] if n in UNTOUCHABLE]
            if flagged:
                st.warning(
                    "🔒 Caution: " + ", ".join(flagged)
                    + (" is" if len(flagged) == 1 else " are")
                    + " flagged as untouchable (franchise-level), so a "
                    "real team is unlikely to trade for "
                    + ("him" if len(flagged) == 1 else "them")
                    + ". Similar players are shown below."
                )
                st.subheader("🔍 Similar Players (not untouchable)")
                target = st.selectbox(
                    "View players with a profile similar to:",
                    flagged,
                    key="similar_target"
                )
                similar = similar_players(
                    players, target, exclude=UNTOUCHABLE, top_n=3
                )
                similar["In lineup"] = similar["Player"].apply(
                    lambda n: "Yes" if n in set(lineup_df["Player"])
                    else "No"
                )
                st.dataframe(
                    add_photos(similar),
                    column_config=PHOTO_CONFIG,
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

            st.subheader("📉 Greedy Lineup (baseline, usually worse)")
            if greedy["lineup"].empty:
                st.info("Greedy could not pick any player under this budget.")
            else:
                st.dataframe(
                    add_photos(
                        greedy["lineup"].sort_values(
                            "Performance", ascending=False
                        )
                    ),
                    column_config=PHOTO_CONFIG,
                    use_container_width=True,
                    hide_index=True
                )
                gap = dp["total_score"] - greedy["total_score"]
                st.caption(money(
                    f"Greedy spends ${greedy['total_salary']:.1f}M for a "
                    f"score of {greedy['total_score']:.1f}. The DP lineup "
                    f"scores {gap:.1f} points more."
                ))

st.divider()

# FULL ROSTER BUILDER (starters + bench)
st.header("🏟️ Full Roster Builder")

st.write(
    "Enter the TOTAL team salary cap and get the best starters and bench. "
    "Players you already own are kept, and their salaries are subtracted "
    "from the cap automatically."
)

roster_cap = st.number_input(
    "Team salary cap ($ Millions, total for the whole roster)",
    min_value=10.0,
    max_value=400.0,
    value=float(SALARY_CAP_M),
    step=1.0
)

max_bench = max(0, len(players) - LINEUP_SIZE)
r1, r2 = st.columns(2)
bench_count = r1.number_input(
    "Bench players",
    min_value=0,
    max_value=max_bench,
    value=min(5, max_bench),
    step=1
)
bench_weight = r2.slider(
    "Bench importance (starters = 1.0)",
    min_value=0.0,
    max_value=1.0,
    value=0.4,
    step=0.05
)

owned = st.multiselect(
    "Players I already own (kept on the roster)",
    options=sorted(players["Player"]),
    default=[]
)

fill_positions = st.multiselect(
    "Fill open spots from these positions",
    options=sorted(players["Position"].unique()),
    default=sorted(players["Position"].unique())
)

# LIVE CHECK of the owned players against the cap
total_spots = LINEUP_SIZE + int(bench_count)
open_spots = total_spots - len(owned)
owned_cost = float(
    players.loc[players["Player"].isin(owned), "Salary"].sum()
)
others = players[
    ~players["Player"].isin(owned)
    & players["Position"].isin(fill_positions)
]
cheapest = sorted(others["Salary"].tolist())[:max(open_spots, 0)]
min_needed = owned_cost + sum(cheapest)

problem = None
if open_spots < 0:
    problem = (
        f"You own {len(owned)} players but the roster has only "
        f"{total_spots} spots. Add bench players or remove some "
        "owned players."
    )
elif owned_cost > roster_cap:
    problem = (
        f"Your {len(owned)} owned players cost ${owned_cost:.1f}M, "
        f"which is more than the ${roster_cap:.1f}M cap. The cap is the "
        "TOTAL for the whole roster, owned players included, so don't "
        "subtract anything yourself. For these players and "
        f"{open_spots} open spot(s) the cap must be at least about "
        f"${min_needed:.1f}M."
    )
elif len(cheapest) == open_spots and min_needed > roster_cap:
    problem = (
        f"Your owned players cost ${owned_cost:.1f}M, but even the "
        f"{open_spots} cheapest players for the open spots bring the "
        f"total to about ${min_needed:.1f}M, over the "
        f"${roster_cap:.1f}M cap. Raise the cap or change the positions."
    )

if problem:
    st.warning(money(problem))
elif owned:
    st.info(money(
        f"You own {len(owned)} player(s) costing ${owned_cost:.1f}M. "
        f"{open_spots} open spot(s) left, with "
        f"${roster_cap - owned_cost:.1f}M of the cap to spend."
    ))

if st.button("🏗️ Build Roster", type="primary"):
    st.session_state["run_roster"] = True

built = None
if st.session_state.get("run_roster"):
    if problem:
        st.error("Fix the warning above, then press Build Roster again.")
    else:
        built = build_roster(
            players, roster_cap, LINEUP_SIZE, int(bench_count),
            locked_names=owned, positions=fill_positions,
            bench_weight=bench_weight
        )

if built is not None:
    if built["error"]:
        st.error(money(built["error"]))
    else:
        rr = built["result"]

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Weighted Score", f"{rr['weighted_score']:.1f}")
        b2.metric("Total Salary", f"${rr['total_salary']:.1f}M")
        b3.metric("Cap Space Left", f"${rr['remaining_cap']:.1f}M")
        b4.metric("Roster Size", rr["roster_size"])

        def tag(row_name):
            parts = []
            if row_name in owned:
                parts.append("✅ Owned")
            if row_name in UNTOUCHABLE:
                parts.append("🔒 Untouchable")
            return " · ".join(parts)

        starters_df = built["starters"].copy()
        bench_df = built["bench"].copy()
        for frame in (starters_df, bench_df):
            frame["Status"] = frame["Player"].apply(tag)

        st.subheader("Starters")
        st.dataframe(
            add_photos(starters_df),
            column_config=PHOTO_CONFIG,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Bench")
        if bench_df.empty:
            st.info("No bench players requested.")
        else:
            st.dataframe(
                add_photos(bench_df),
                column_config=PHOTO_CONFIG,
                use_container_width=True,
                hide_index=True
            )

        # GREEDY ROSTER (baseline) with the same owned players
        greedy_built = greedy_roster(
            players, roster_cap, LINEUP_SIZE, int(bench_count),
            locked_names=owned, positions=fill_positions,
            bench_weight=bench_weight
        )

        st.subheader("📉 Greedy Roster (baseline, usually worse)")
        g1, g2, g3, g4 = st.columns(4)
        g1.metric(
            "Weighted Score",
            f"{greedy_built['weighted_score']:.1f}",
            delta=(
                f"{greedy_built['weighted_score'] - rr['weighted_score']:.1f}"
                " vs DP"
            )
        )
        g2.metric("Total Salary", f"${greedy_built['total_salary']:.1f}M")
        g3.metric("Cap Space Left", f"${greedy_built['remaining_cap']:.1f}M")
        g4.metric("Roster Size", greedy_built["roster_size"])

        if not greedy_built["full"]:
            st.warning(
                "Greedy could not fill every roster spot under this cap."
            )

        gs_df = greedy_built["starters"].copy()
        gb_df = greedy_built["bench"].copy()
        for frame in (gs_df, gb_df):
            frame["Status"] = frame["Player"].apply(tag)

        st.markdown("**Greedy starters**")
        st.dataframe(
            add_photos(gs_df),
            column_config=PHOTO_CONFIG,
            use_container_width=True,
            hide_index=True
        )
        st.markdown("**Greedy bench**")
        if gb_df.empty:
            st.info("No bench players requested.")
        else:
            st.dataframe(
                add_photos(gb_df),
                column_config=PHOTO_CONFIG,
                use_container_width=True,
                hide_index=True
            )

        # CAUTION + SIMILAR PLAYERS for untouchables the optimizer added
        roster_names = (
            list(starters_df["Player"]) + list(bench_df["Player"])
        )
        flagged_new = [
            n for n in roster_names
            if n in UNTOUCHABLE and n not in owned
        ]
        if flagged_new:
            st.warning(
                "🔒 Caution: " + ", ".join(flagged_new)
                + (" is" if len(flagged_new) == 1 else " are")
                + " flagged as untouchable (franchise-level), so a "
                "real team is unlikely to trade for "
                + ("him" if len(flagged_new) == 1 else "them")
                + ". Similar players are shown below."
            )
            st.subheader("🔍 Similar Players (not untouchable)")
            roster_target = st.selectbox(
                "View players with a profile similar to:",
                flagged_new,
                key="similar_roster_target"
            )
            similar_roster = similar_players(
                players, roster_target, exclude=UNTOUCHABLE, top_n=3
            )
            similar_roster["On roster"] = similar_roster["Player"].apply(
                lambda n: "Yes" if n in set(roster_names) else "No"
            )
            st.dataframe(
                add_photos(similar_roster),
                column_config=PHOTO_CONFIG,
                use_container_width=True,
                hide_index=True
            )

st.divider()

# PLAYER COMPARISON (side by side)
st.header("⚖️ Compare Players")

MAX_COMPARE = 4

compare_names = st.multiselect(
    f"Pick 2 to {MAX_COMPARE} players to compare",
    options=sorted(players["Player"]),
    default=[],
    max_selections=MAX_COMPARE,
    key="compare_names"
)

if len(compare_names) < 2:
    st.info("Select at least 2 players to compare them side by side.")
else:
    stat_options = [
        "Salary", "Performance", "Points", "Rebounds", "Assists",
        "Steals", "Blocks", "Minutes", "TS%", "Turnovers"
    ]
    stat_rows = [c for c in stat_options if c in players.columns]
    lower_is_better = {"Salary", "Turnovers"}

    chosen = (
        players[players["Player"].isin(compare_names)]
        .drop_duplicates("Player")
        .set_index("Player")
        .loc[compare_names]
    )

    # One card per player: photo, name, position, score, salary
    card_cols = st.columns(len(compare_names))
    for col, name in zip(card_cols, compare_names):
        row = chosen.loc[name]
        with col:
            pic = headshot(name)
            if pic:
                st.image(pic, width=130)
            st.subheader(name)
            lock_tag = " · 🔒 Untouchable" if name in UNTOUCHABLE else ""
            st.caption(f"{row['Position']}{lock_tag}")
            st.metric("Score", f"{row['Performance']:.1f}")
            st.metric("Salary", f"${row['Salary']:.1f}M")

    # Stat table: one column per player, best value highlighted per row
    table = chosen[stat_rows].T

    def highlight_best(row):
        best = row.min() if row.name in lower_is_better else row.max()
        return [
            "background-color: #1f6f3f; color: white"
            if v == best else ""
            for v in row
        ]

    st.dataframe(
        table.style.apply(highlight_best, axis=1).format("{:.2f}"),
        use_container_width=True
    )
    st.caption(
        "Green = best value in that row. For Salary and Turnovers, "
        "lower is better. Salary is in millions of dollars."
    )

    # Value check: score per $1M of salary
    value = (chosen["Performance"] / chosen["Salary"]).round(2)
    best_value = value.idxmax()
    st.info(
        f"Best value for the money: **{best_value}** "
        f"({value[best_value]} score points per $1M of salary)."
    )

st.divider()
st.caption(
    "CourtVision | CSCE 4110 Algorithms "
    "| NBA Analytics & Lineup Optimization"
)