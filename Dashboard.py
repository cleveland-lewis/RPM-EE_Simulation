# Dashboard.py
# Page title: Homepage
import json
import os
import sys
from datetime import datetime

# Ensure src/ is in the import path for simulation modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans

from simulation import RPMEESimulation

# --- Constants ---
COUNTER_FILE = "trial_counter.json"


# --- Utilities ---
def load_trial_count():
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "r") as f:
                return json.load(f).get("trial_count", 1)
    except Exception:
        pass
    return 1


def save_trial_count(count):
    try:
        with open(COUNTER_FILE, "w") as f:
            json.dump({"trial_count": count}, f)
    except Exception as e:
        st.warning(f"Failed to save counter: {e}")


# --- Configuration ---
st.set_page_config(page_title="RPM-EE Research Dashboard", layout="wide")
st.title("RPM-EE Research Dashboard")


# --- Session Initialization ---
def init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


for key, default in [
    ("trial_count", load_trial_count()),
    ("log_data", None),
    ("cumulative_data", []),
    ("metadata", [])
]:
    init_state(key, default)

st.subheader(f"Current Trial: {st.session_state['trial_count'] - 1} | Next Trial: {st.session_state['trial_count']}")

# --- Sidebar Controls ---
st.sidebar.header("Simulation Controls")
with st.sidebar.expander("Parameters", expanded=False):
    # Core RPM-EE Parameters
    fatigue_threshold = st.number_input("Fatigue Threshold", 1, 20, 3)
    salience_decay = st.number_input("Salience Decay Rate", 0.0, 1.0, 0.01, step=0.01)
    weight_error_corr = st.number_input("Error-Correction Weight", 0.0, 2.0, 1.0, step=0.1)
    weight_soothing = st.number_input("Soothing Weight", 0.0, 2.0, 1.0, step=0.1)

    # Extended Parameters
    replay_weight_problem = st.number_input("Replay Weight: Problem Solving", 0.0, 5.0, 1.0, step=0.1)
    replay_weight_soothing = st.number_input("Replay Weight: Soothing", 0.0, 5.0, 1.0, step=0.1)
    replay_weight_search = st.number_input("Replay Weight: Pattern Search", 0.0, 5.0, 1.0, step=0.1)

    exploration_bias = st.number_input("Exploration Bias", 0.0, 1.0, 0.5, step=0.05)
    schema_stress_weight = st.number_input("Schema Stress Weight", 0.0, 5.0, 1.0, step=0.1)
    memory_decay = st.number_input("Memory Decay Rate", 0.0, 1.0, 0.05, step=0.01)
    input_noise = st.number_input("Input Noise Level", 0.0, 1.0, 0.0, step=0.01)

episodes = st.sidebar.number_input("Episodes", 10, 10000, 500, step=50)
repetitions = st.sidebar.number_input("Repetitions", 1, 100, 1, step=1)
run_sim = st.sidebar.button("Run Simulation")

# --- Presets ---
with st.sidebar.expander("Personality Presets", expanded=False):
    preset = st.selectbox("Choose Preset", ["None", "Anxious Analyst", "Detached Observer", "Overstimulated Idealist",
                                            "Avoidant Minimalist", "Hyper-Adaptive Pleaser"])

    preset_values = {
        "Anxious Analyst": {
            "fatigue_threshold": 2,
            "salience_decay": 0.02,
            "weight_error_corr": 1.8,
            "weight_soothing": 0.6,
            "replay_weight_problem": 1.5,
            "replay_weight_soothing": 0.7,
            "replay_weight_search": 0.9,
            "exploration_bias": 0.2,
            "schema_stress_weight": 2.0,
            "memory_decay": 0.1,
            "input_noise": 0.05
        },
        "Detached Observer": {
            "fatigue_threshold": 4,
            "salience_decay": 0.005,
            "weight_error_corr": 1.0,
            "weight_soothing": 1.3,
            "replay_weight_problem": 1.0,
            "replay_weight_soothing": 1.5,
            "replay_weight_search": 1.2,
            "exploration_bias": 0.4,
            "schema_stress_weight": 0.8,
            "memory_decay": 0.02,
            "input_noise": 0.1
        },
        "Overstimulated Idealist": {
            "fatigue_threshold": 1,
            "salience_decay": 0.03,
            "weight_error_corr": 0.7,
            "weight_soothing": 1.6,
            "replay_weight_problem": 1.2,
            "replay_weight_soothing": 1.7,
            "replay_weight_search": 2.5,
            "exploration_bias": 0.6,
            "schema_stress_weight": 3.0,
            "memory_decay": 0.15,
            "input_noise": 0.2
        },
        "Avoidant Minimalist": {
            "fatigue_threshold": 5,
            "salience_decay": 0.01,
            "weight_error_corr": 0.9,
            "weight_soothing": 0.8,
            "replay_weight_problem": 0.5,
            "replay_weight_soothing": 1.0,
            "replay_weight_search": 0.7,
            "exploration_bias": 0.1,
            "schema_stress_weight": 1.5,
            "memory_decay": 0.03,
            "input_noise": 0.05
        },
        "Hyper-Adaptive Pleaser": {
            "fatigue_threshold": 2,
            "salience_decay": 0.015,
            "weight_error_corr": 1.2,
            "weight_soothing": 1.8,
            "replay_weight_problem": 1.3,
            "replay_weight_soothing": 2.0,
            "replay_weight_search": 1.0,
            "exploration_bias": 0.9,
            "schema_stress_weight": 2.5,
            "memory_decay": 0.08,
            "input_noise": 0.12
        }
    }

    if preset != "None":
        for k, v in preset_values[preset].items():
            st.session_state[k] = v
        st.success(f"Preset '{preset}' applied. Parameters updated.")

# Reset preset flag on rerun
if preset == "None" and "_preset_applied" in st.session_state:
    del st.session_state["_preset_applied"]

# Reset preset flag on rerun
if preset == "None" and "_preset_applied" in st.session_state:
    del st.session_state["_preset_applied"]

# --- Export ---
st.sidebar.header("Data Control")
export_format = st.sidebar.selectbox("Select format", ["CSV", "JSON"])
if st.sidebar.button("Download Latest") and st.session_state["log_data"] is not None:
    filename = f"rpm_trial_export.{export_format.lower()}"
    if export_format == "CSV":
        csv_data = pd.DataFrame(st.session_state["log_data"]).to_csv(index=False)
        st.sidebar.download_button("Download CSV", csv_data, file_name=filename)
    else:
        json_data = json.dumps(st.session_state["log_data"], indent=2)
        st.sidebar.download_button("Download JSON", json_data, file_name=filename)

# --- Clear & Upload ---
if st.sidebar.button("Clear All Data"):
    for key in ["log_data", "cumulative_data", "metadata"]:
        st.session_state[key] = [] if isinstance(st.session_state[key], list) else None
    st.session_state["trial_count"] = 1
    save_trial_count(1)
    st.sidebar.success("All data cleared.")

uploaded_file = st.sidebar.file_uploader("Upload Logs", type="json")
if uploaded_file:
    try:
        st.session_state["log_data"] = json.load(uploaded_file)
        st.success(f"Loaded log: {uploaded_file.name}")
    except Exception as e:
        st.error(f"Failed to load file: {e}")

# --- Simulation Execution ---
if run_sim:
    from src.simulation import RPMEESimulation

    st.subheader("Trial Progress")
    progress_bar = st.progress(0)
    progress_placeholder = st.empty()

    config = {
        "fatigue_threshold": fatigue_threshold,
        "salience_decay": salience_decay,
        "weight_error_corr": weight_error_corr,
        "weight_soothing": weight_soothing,
        "replay_weight_problem": replay_weight_problem,
        "replay_weight_soothing": replay_weight_soothing,
        "replay_weight_search": replay_weight_search,
        "exploration_bias": exploration_bias,
        "schema_stress_weight": schema_stress_weight,
        "memory_decay": memory_decay,
        "input_noise": input_noise
    }

    for rep in range(repetitions):
        progress_placeholder.metric("Running Trial", f"{rep + 1} of {repetitions}")
        progress_bar.progress((rep + 1) / repetitions)
        try:
            sim = RPMEESimulation()
            for k, v in config.items():
                setattr(sim, k, v)
            sim.run(episodes=episodes)
            logs = sim.logs

            filename = f"saved_logs/{datetime.now():%Y-%m-%d}-trial-{st.session_state['trial_count']:03}.json"
            with open(filename, "w") as f:
                json.dump(logs, f)

            st.session_state["log_data"] = logs
            st.session_state["cumulative_data"].append(logs)
            st.session_state["metadata"].append(
                {"trial": st.session_state["trial_count"], "episodes": episodes, "timestamp": str(datetime.now()),
                 "config": config})
            st.session_state["trial_count"] += 1
            save_trial_count(st.session_state["trial_count"])
            st.toast(f"Trial {rep + 1}/{repetitions} complete. Saved as {filename}", icon="✅")
        except Exception as err:
            st.error(f"Simulation {rep + 1} failed: {err}")

    st.toast("All simulations complete!", icon="🎉")

# --- Batch Simulation ---
with st.sidebar.expander("Batch Simulation", expanded=False):
    st.markdown("Run multiple synthetic agents with randomized parameters.")
    batch_agents = st.number_input("Number of Unique Agents", 1, 1000, 5)
    batch_reps = st.number_input("Repetitions per Agent", 1, 100, 3)
    batch_episodes = st.number_input("Episodes per Trial", 10, 10000, 500, step=50)
    start_batch = st.button("Start Batch Simulation")

    if start_batch:
        from src.simulation import RPMEESimulation
        import glob

        st.subheader("Batch Progress")
        total_jobs = batch_agents * batch_reps
        progress_bar = st.progress(0)
        progress_placeholder = st.empty()


        def random_config():
            return {
                "fatigue_threshold": np.random.randint(1, 6),
                "salience_decay": round(np.random.uniform(0.005, 0.05), 3),
                "weight_error_corr": round(np.random.uniform(0.5, 2.0), 2),
                "weight_soothing": round(np.random.uniform(0.5, 2.0), 2),
                "replay_weight_problem": round(np.random.uniform(0.5, 2.5), 2),
                "replay_weight_soothing": round(np.random.uniform(0.5, 2.5), 2),
                "replay_weight_search": round(np.random.uniform(0.5, 2.5), 2),
                "exploration_bias": round(np.random.uniform(0.0, 1.0), 2),
                "schema_stress_weight": round(np.random.uniform(0.5, 3.0), 2),
                "memory_decay": round(np.random.uniform(0.01, 0.2), 3),
                "input_noise": round(np.random.uniform(0.0, 0.2), 3)
            }


        job = 0
        for agent_idx in range(batch_agents):
            config = random_config()
            for rep in range(batch_reps):
                try:
                    sim = RPMEESimulation()
                    for k, v in config.items():
                        setattr(sim, k, v)
                    sim.run(episodes=batch_episodes)
                    logs = sim.logs

                    filename = f"saved_logs/pop_agent{agent_idx:03}_rep{rep:02}.json"
                    with open(filename, "w") as f:
                        json.dump(logs, f)

                    job += 1
                    progress_placeholder.text(f"Completed {job}/{total_jobs}")
                    progress_bar.progress(job / total_jobs)
                except Exception as e:
                    st.error(f"Failed agent {agent_idx} rep {rep}: {e}")

        # Automatically load batch logs into memory
        st.session_state["cumulative_data"] = []
        batch_files = sorted(glob.glob("saved_logs/pop_*.json"))
        for file in batch_files:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    st.session_state["cumulative_data"].append(data)
            except Exception as e:
                st.warning(f"Failed to load {file}: {e}")

        st.success(f"Batch simulation complete. Loaded {len(batch_files)} trials.")

# --- Data Display ---
if st.session_state["log_data"]:
    df = pd.DataFrame(st.session_state["log_data"])

    st.subheader("Recent Trial Metrics")
    cols = st.columns(3)
    metrics = ["attunement_score", "schema_stress", "avg_affect_feedback"]
    for i, m in enumerate(metrics):
        if m in df.columns:
            avg_val = df[m].mean()
            cols[i].metric(m.replace("_", " ").title(), round(avg_val, 3))

    st.subheader("Time-Series Overview: Average Every 10 Episodes")
    group_size = max(10, len(df) // 100)  # dynamic bin size for readability
    df["group"] = np.floor(np.arange(len(df)) / group_size)
    grouped_df = df.groupby("group").mean(numeric_only=True).reset_index()

    for m in metrics:
        if m in grouped_df.columns:
            st.plotly_chart(px.line(grouped_df, x="group", y=m, title=f"{m.replace('_', ' ').title()} (Smoothed)"),
                            use_container_width=True)

    if {"avg_valence", "avg_arousal"}.issubset(df.columns):
        st.subheader("Emotion Space (Valence vs Arousal)")
        st.plotly_chart(px.scatter(df, x="avg_valence", y="avg_arousal", color="schema_stress"),
                        use_container_width=True)

    features = [f for f in ["avg_valence", "avg_arousal", "schema_stress"] if f in df.columns]
    if len(df) > 2 and len(features) > 1:
        st.subheader("Dimensionality Reduction")
        X = df[features].fillna(0)
        pca = PCA(n_components=2).fit_transform(X)
        df["PCA1"], df["PCA2"] = pca[:, 0], pca[:, 1]
        st.plotly_chart(px.scatter(df, x="PCA1", y="PCA2", color="schema_stress", title="PCA Projection"),
                        use_container_width=True)

        tsne = TSNE(n_components=2, perplexity=min(30, len(df) - 1)).fit_transform(X)
        df["tSNE1"], df["tSNE2"] = tsne[:, 0], tsne[:, 1]
        st.plotly_chart(px.scatter(df, x="tSNE1", y="tSNE2", color="schema_stress", title="t-SNE Projection"),
                        use_container_width=True)

    if st.session_state["cumulative_data"]:
        st.subheader("Cumulative Analysis")
        combined = pd.concat([pd.DataFrame(log) for log in st.session_state["cumulative_data"]])
        summary = combined.select_dtypes(include=[np.number]).groupby(
            np.arange(len(combined)) // episodes).mean().reset_index()
        st.plotly_chart(px.line(summary, y=["attunement_score", "schema_stress"], title="Trial Averages"),
                        use_container_width=True)

        if len(summary) > 2:
            clusters = KMeans(3).fit_predict(summary[["attunement_score", "schema_stress"]].fillna(0))
            summary["Cluster"] = clusters
            st.plotly_chart(
                px.scatter(summary, x="attunement_score", y="schema_stress", color="Cluster", title="Clustered Trials"),
                use_container_width=True)
else:
    st.info("Run a simulation or upload logs to view data.")

if st.session_state["cumulative_data"]:
    st.subheader("Compare Multiple Trials")
    all_trials_df = pd.concat([
        pd.DataFrame(trial).assign(Trial=f"Trial {i + 1}")
        for i, trial in enumerate(st.session_state["cumulative_data"])
    ])

    selected_trials = st.multiselect(
        "Select Trials to Compare",
        options=sorted(all_trials_df["Trial"].unique()),
        default=sorted(all_trials_df["Trial"].unique())[-2:] if len(
            all_trials_df["Trial"].unique()) >= 2 else sorted(all_trials_df["Trial"].unique())
    )

    if selected_trials:
        filtered = all_trials_df[all_trials_df["Trial"].isin(selected_trials)]
        for m in ["attunement_score", "schema_stress", "avg_affect_feedback"]:
            if m in filtered.columns:
                st.plotly_chart(
                    px.line(filtered, x="clock", y=m, color="Trial",
                            title=f"{m.replace('_', ' ').title()} by Trial"),
                    use_container_width=True
                )

# --- Raw Data Viewer ---
if st.session_state["cumulative_data"]:
    if st.button("Show Raw Data for Last 5 Trials"):
        st.subheader("Raw Logs: Last 5 Trials")
        last_five = st.session_state["cumulative_data"][-5:]
        for i, trial_data in enumerate(last_five[::-1], 1):
            st.expander(f"Trial {st.session_state['trial_count'] - i}").write(pd.DataFrame(trial_data))
