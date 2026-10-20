
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# PAGE CONFIGURATION
st.set_page_config(
    page_title="CourtVision | NBA Lineup Optimizer",
    page_icon="🏀",
    layout="wide"
)

# DEMONSTRATION DATA
# Member 1 will replace this with verified NBA data.
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
            "Demo Guard C", "Demo Forward C"
        ],
        "Position": [
            "PG", "SG", "SF", "PF",
            "C", "C", "PG", "SF"
        ],
        "Salary": [32, 25, 38, 22, 35, 19, 16, 28],
        "Points": [28, 23, 30, 18, 26, 15, 17, 24],
        "Rebounds": [5, 4, 8, 9, 12, 10, 3, 7],
        "Assists": [9, 6, 5, 3, 4, 2, 8, 4]
    }

    return pd.DataFrame(sample), True


players, demo_mode = load_players()

# PLAYER PERFORMANCE SCORE
# Temporary scoring formula until Member 1 provides theirs.
if "Performance" not in players.columns:
    players["Performance"] = (
        players["Points"]
        + 1.2 * players["Rebounds"]
        + 1.5 * players["Assists"]
    ).round(2)

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
        "Demonstration mode: player names, salaries "
        "and statistics are fictional."
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
    value=100,
    step=5
)

lineup_size = st.sidebar.slider(
    "Number of Players",
    min_value=1,
    max_value=min(15, len(players)),
    value=min(5, len(players))
)

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

# LINEUP OPTIMIZER INTERFACE
st.header("🏆 NBA Lineup Optimizer")

st.write(
    "The optimizer will select players to maximize "
    "performance while respecting the salary budget."
)

st.write("**Current settings:**")
st.write(f"Salary Budget: ${budget} Million")
st.write(f"Requested Players: {lineup_size}")

if st.button("🚀 Optimize Lineup", type="primary"):
    if len(filtered) < lineup_size:
        st.error(
            "Not enough players match your current filters."
        )
    else:
        st.info(
            "Optimizer integration is pending. "
            "Member 2's 0/1 Knapsack module will "
            "calculate and display the optimal lineup."
        )

st.divider()
st.caption(
    "CourtVision | CSCE 4110 Algorithms "
    "| NBA Analytics & Lineup Optimization"
)
