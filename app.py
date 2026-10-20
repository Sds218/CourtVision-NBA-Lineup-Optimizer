
import streamlit as st

# Configure the dashboard
st.set_page_config(
    page_title="CourtVision | NBA Lineup Optimizer",
    page_icon="🏀",
    layout="wide"
)

# Dashboard heading
st.title("🏀 CourtVision")
st.subheader("NBA Analytics & Lineup Optimizer")

st.write(
    "Build smarter basketball lineups using "
    "0/1 Knapsack Dynamic Programming."
)

st.divider()

# Sidebar controls
st.sidebar.header("⚙️ Lineup Settings")

budget = st.sidebar.slider(
    "Salary Budget ($ Millions)",
    min_value=20,
    max_value=200,
    value=100
)

lineup_size = st.sidebar.slider(
    "Number of Players",
    min_value=1,
    max_value=15,
    value=5
)

# Dashboard metrics
col1, col2, col3 = st.columns(3)

col1.metric("Salary Budget", f"${budget}M")
col2.metric("Lineup Size", lineup_size)
col3.metric("Algorithm", "0/1 Knapsack")

st.divider()

st.header("🏀 NBA Lineup Optimizer")

if st.button("🚀 Optimize Lineup", type="primary"):
    st.success("CourtVision dashboard is working!")
    st.info("We will connect the 0/1 Knapsack algorithm next.")
