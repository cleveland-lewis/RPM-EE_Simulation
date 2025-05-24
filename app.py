import streamlit as st
import pandas as pd
import altair as alt
import json
import time
import os
from datetime import datetime
from simulation import RPMEESimulation

# Set page config
st.set_page_config(page_title="RPM-EE Dashboard", layout="wide")

# Title
st.title("RPM-EE Simulation Dashboard")
st.markdown("""
<style>
    .main {
        font-family: "Segoe UI", sans-serif;
    }
    .stApp {
        background-color: #f9f9f9;
        color: #222;
    }
</style>
""", unsafe_allow_html=True)

# Interactive simulation execution
st.sidebar.header("Run New Simulation")
episodes = st.sidebar.number_input("Number of Episodes", min_value=10, max_value=10000, value=500, step=10)
run_simulation = st.sidebar.button("Run Simulation")

log_data = None
if run_simulation:
    sim = RPMEESimulation()
    sim.run(episodes=episodes)
    log_data = sim.logs
    st.success(f"Simulation completed with {episodes} episodes.")

if log_data:
    df = pd.DataFrame(log_data)

    # Export and Save Options
    st.subheader("Post-Simulation Options")
    col_export, col_save = st.columns([1, 2])

    with col_export:
        export_json = st.download_button(
            label="Export as JSON",
            file_name="simulation_log.json",
            mime="application/json",
            data=json.dumps(log_data, indent=2)
        )

    with col_save:
        st.write("Save this test?")
        save_yes = st.button("Yes")
        save_no = st.button("No")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if save_yes:
            os.makedirs("saved_logs", exist_ok=True)
            with open(f"saved_logs/sim_log_{timestamp}.json", "w") as f:
                json.dump(log_data, f, indent=2)
            st.success(f"Saved to saved_logs/sim_log_{timestamp}.json")

        elif save_no:
            reason = st.text_input("Why is this data unused?")
            if reason:
                os.makedirs("unused_logs", exist_ok=True)
                with open(f"unused_logs/sim_log_{timestamp}.json", "w") as f:
                    json.dump({"reason": reason, "log": log_data}, f, indent=2)
                st.warning(f"Saved to unused_logs/sim_log_{timestamp}.json")

    # Sidebar filter
    st.sidebar.header("Filters")
    selected_mode = st.sidebar.multiselect("Replay Modes", options=df["replay_mode"].unique(), default=df["replay_mode"].unique())
    df_filtered = df[df["replay_mode"].isin(selected_mode)]

    # Layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Attunement Score Over Time")
        line_chart = alt.Chart(df_filtered).mark_line(opacity=0.5).encode(
            x=alt.X("clock", title="Trial"),
            y=alt.Y("attunement_score", title="Attunement Score"),
            color=alt.Color("replay_mode", title="Replay Mode")
        ).properties(height=300).interactive()
        st.altair_chart(line_chart, use_container_width=True)

    with col2:
        st.subheader("Schema Stress Over Time")
        stress_chart = alt.Chart(df_filtered).mark_line(color="orange", opacity=0.5).encode(
            x=alt.X("clock", title="Trial"),
            y=alt.Y("schema_stress", title="Schema Stress")
        ).properties(height=300).interactive()
        st.altair_chart(stress_chart, use_container_width=True)

    st.subheader("Replay Mode Counts")
    mode_counts = df_filtered["replay_mode"].value_counts().reset_index()
    mode_counts.columns = ["Replay Mode", "Count"]
    st.bar_chart(mode_counts.set_index("Replay Mode"))

    with st.expander("Raw Log Data"):
        st.dataframe(df_filtered, use_container_width=True)

# Display past logs
st.sidebar.subheader("Saved Logs")
saved_files = os.listdir("saved_logs") if os.path.exists("saved_logs") else []
if saved_files:
    selected_saved = st.sidebar.selectbox("View a saved log", saved_files)
    if selected_saved:
        with open(f"saved_logs/{selected_saved}") as f:
            saved_data = json.load(f)
            st.subheader(f"Saved Log: {selected_saved}")
            st.dataframe(pd.DataFrame(saved_data))

st.sidebar.subheader("Unused Logs")
unused_files = os.listdir("unused_logs") if os.path.exists("unused_logs") else []
if unused_files:
    selected_unused = st.sidebar.selectbox("View an unused log", unused_files)
    if selected_unused:
        with open(f"unused_logs/{selected_unused}") as f:
            unused_data = json.load(f)
            st.subheader(f"Unused Log: {selected_unused}")
            st.text(f"Reason: {unused_data.get('reason', 'No reason provided')}")
            st.dataframe(pd.DataFrame(unused_data.get("log", [])))

if not log_data:
    st.info("Run a simulation to view data.")