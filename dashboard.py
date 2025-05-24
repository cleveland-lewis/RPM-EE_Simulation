COUNTER_FILE = "trial_counter.json"

def load_trial_count():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            return json.load(f).get("trial_count", 1)
    return 1

def save_trial_count(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"trial_count": count}, f)
import streamlit as st
import pandas as pd
import altair as alt
import json
import time
import os
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from simulation import RPMEESimulation

# Set page config
st.set_page_config(page_title="RPM-EE Dashboard", layout="wide")

if "log_data" not in st.session_state:
    st.session_state["log_data"] = None
if "filename" not in st.session_state:
    st.session_state["filename"] = None
if "trial_count" not in st.session_state:
    st.session_state["trial_count"] = load_trial_count()


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

# Ensure log folders exist
os.makedirs("saved_logs", exist_ok=True)
os.makedirs("unused_logs", exist_ok=True)

# Interactive simulation execution
st.sidebar.header("Run New Simulation")
episodes = st.sidebar.number_input("Number of Episodes", min_value=10, max_value=10000, value=500, step=10)
run_simulation = st.sidebar.button("Run Simulation")

log_data = None
filename = None
if run_simulation:
    sim = RPMEESimulation()
    sim.run(episodes=episodes)
    log_data = sim.logs

    # Generate filename with padded trial number
    trial_number = st.session_state["trial_count"]
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"{timestamp}-trial-{trial_number:03}.json"

    # Save to session state
    st.session_state["log_data"] = log_data
    st.session_state["filename"] = filename

    # Increment for next run
    st.session_state["trial_count"] += 1
    save_trial_count(st.session_state["trial_count"])
    st.success(f"Simulation completed with {episodes} episodes. Trial #{trial_number}")

if st.session_state["log_data"]:
    df = pd.DataFrame(st.session_state["log_data"])
else:
    df = pd.DataFrame()

# Export and Save Options
st.subheader("Post-Simulation Options")
col_export, col_save = st.columns([1, 1])

with col_export:
    if not df.empty:
        export_name = st.session_state.get("filename", "simulation_log.json").replace(".json", ".csv")
        export_csv = st.download_button(
            label="Export as CSV",
            file_name=export_name,
            mime="text/csv",
            data=df.to_csv(index=False)
        )

with col_save:
    if st.button("Save"):
        log_data = st.session_state.get("log_data")
        filename = st.session_state.get("filename")
        if log_data and filename:
            save_path = os.path.join("saved_logs", filename)
            with open(save_path, "w") as f:
                json.dump(log_data, f, indent=2)
            st.success(f"Saved to {save_path}")
        else:
            st.error("No simulation data to save. Run a simulation first.")

# Sidebar filter
st.sidebar.header("Filters")
selected_mode = st.sidebar.multiselect("Replay Modes", options=df["replay_mode"].unique() if not df.empty else [], default=df["replay_mode"].unique() if not df.empty else [])
df_filtered = df[df["replay_mode"].isin(selected_mode)] if not df.empty else df

if not df_filtered.empty:
    # Aggregated Attunement Score Graph
    st.subheader("Average Attunement Score by Trial")
    attunement_avg = df_filtered.groupby("clock")["attunement_score"].mean().reset_index()
    avg_chart = alt.Chart(attunement_avg).mark_line().encode(
        x=alt.X("clock", title="Trial"),
        y=alt.Y("attunement_score", title="Avg Attunement Score")
    ).properties(height=300).interactive()
    st.altair_chart(avg_chart, use_container_width=True)

    # Schema Stress Over Time
    st.subheader("Schema Stress Over Time")
    stress_chart = alt.Chart(df_filtered).mark_line(color="orange", opacity=0.5).encode(
        x=alt.X("clock", title="Trial"),
        y=alt.Y("schema_stress", title="Schema Stress")
    ).properties(height=300).interactive()
    st.altair_chart(stress_chart, use_container_width=True)

    # Replay Mode Type Chart (count over time)
    st.subheader("Replay Mode Frequency by Trial")
    replay_chart = alt.Chart(df_filtered).mark_bar().encode(
        x=alt.X("clock:O", title="Trial"),
        y=alt.Y("count()", title="Count"),
        color="replay_mode:N"
    ).properties(height=300).interactive()
    st.altair_chart(replay_chart, use_container_width=True)

    # Replay Mode Counts Summary
    st.subheader("Replay Mode Counts")
    mode_counts = df_filtered["replay_mode"].value_counts().reset_index()
    mode_counts.columns = ["Replay Mode", "Count"]
    st.bar_chart(mode_counts.set_index("Replay Mode"))

    # Raw Log Table
    with st.expander("Raw Log Data"):
        st.dataframe(df_filtered, use_container_width=True)

# Display recent saved logs
st.sidebar.subheader("Recent Tests")
saved_dir = "saved_logs"
if os.path.exists(saved_dir):
    json_files = [f for f in os.listdir(saved_dir) if f.endswith(".json")]
    json_files = sorted(
        json_files,
        key=lambda x: os.path.getctime(os.path.join(saved_dir, x)),
        reverse=True
    )[:2]  # Limit to most recent 2

    if json_files:
        selected_saved = st.sidebar.selectbox("View recent log", json_files, key="recent_logs_view")
        if selected_saved:
            try:
                with open(os.path.join(saved_dir, selected_saved)) as f:
                    saved_data = json.load(f)
                    st.subheader(f"Recent Log: {selected_saved}")
                    st.dataframe(pd.DataFrame(saved_data))
            except Exception as e:
                st.error(f"Error loading recent log: {e}")
    else:
        st.sidebar.write("No recent logs found.")
else:
    st.sidebar.write("Saved logs directory not found.")