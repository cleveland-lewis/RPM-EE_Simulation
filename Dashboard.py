import gc
import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from simulation import RPMEESimulation
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from config import DEFAULT_CONFIG, PRESETS, save_trial_count

st.set_page_config(page_title="RPM-EE Simulation Dashboard", layout="wide")
st.title("RPM-EE Simulation Interface")

# --- Sidebar Controls ---
st.sidebar.header("Controls")

init_state = lambda k, v: st.session_state.setdefault(k, v)

init_state("timing_center", DEFAULT_CONFIG["timing_center"])
st.slider("Timing Sigmoid Center", 0, 1000, value=st.session_state["timing_center"], key="timing_center")

if st.button("\U0001F504 Reset to Default"):
    for k, v in DEFAULT_CONFIG.items():
        st.session_state[k] = v
    st.experimental_rerun()

with st.expander("Personality Presets"):
    preset = st.selectbox("Choose Preset", ["None"] + list(PRESETS.keys()))
    if preset != "None" and preset in PRESETS:
        for k, v in PRESETS[preset].items():
            st.session_state[k] = v
        st.success(f"Preset '{preset}' applied.")
        st.experimental_rerun()

episodes = st.number_input("Episodes", 10, 10000, 500, step=50)
repetitions = st.number_input("Repetitions", 1, 100, 1)
run_sim = st.button("Run Simulation")

with st.expander("Batch Simulation"):
    batch_agents = st.number_input("Unique Agents", 1, 1000, 5)
    batch_reps = st.number_input("Repetitions per Agent", 1, 100, 3)
    batch_episodes = st.number_input("Episodes per Trial", 10, 10000, 500)
    start_batch = st.button("Start Batch Simulation")

# --- Simulation Execution ---
if run_sim:
    config = {k: st.session_state[k] for k in DEFAULT_CONFIG}
    with st.spinner("Running Simulation..."):
        progress_bar = st.progress(0)
        for rep in range(repetitions):
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
            st.session_state["metadata"].append({"trial": st.session_state["trial_count"], "episodes": episodes, "timestamp": str(datetime.now()), "config": config})

            st.session_state["trial_count"] += 1
            save_trial_count(st.session_state["trial_count"])
            progress_bar.progress((rep + 1) / repetitions)

        st.success("All simulations complete!")

# --- Batch Simulation ---
if 'start_batch' in locals() and start_batch:
    with st.spinner("Running Batch Simulation..."):
        total_jobs = batch_agents * batch_reps
        progress_bar = st.progress(0)
        job = 0

        def random_config():
            return {k: np.random.uniform(0.5, 2.0) if isinstance(DEFAULT_CONFIG[k], float) else np.random.randint(1, 6)
                    for k in DEFAULT_CONFIG}

        for agent in range(batch_agents):
            config = random_config()
            for rep in range(batch_reps):
                sim = RPMEESimulation()
                for k, v in config.items():
                    setattr(sim, k, v)
                sim.run(episodes=batch_episodes)
                logs = sim.logs
                filename = f"saved_logs/pop_agent{agent:03}_rep{rep:02}.json"
                with open(filename, "w") as f:
                    json.dump(logs, f)
                job += 1
                progress_bar.progress(job / total_jobs)

                st.session_state["cumulative_data"].append(logs)
                del sim
                gc.collect()

        st.success("Batch simulation complete!")

# --- Results ---
if st.session_state.get("log_data"):
    st.subheader("Trial Metrics")
    df = pd.DataFrame(st.session_state["log_data"])
    cols = st.columns(3)
    for i, m in enumerate(["attunement_score", "schema_stress", "avg_affect_feedback"]):
        if m in df.columns:
            cols[i].metric(m.replace("_", " ").title(), round(df[m].mean(), 3))

    st.subheader("Affective Dynamics")
    if {"avg_valence", "avg_arousal"}.issubset(df.columns):
        st.plotly_chart(px.scatter(df, x="avg_valence", y="avg_arousal", color="schema_stress"))

    features = [f for f in ["avg_valence", "avg_arousal", "schema_stress"] if f in df.columns]
    if len(df) > 2 and len(features) > 1:
        X = df[features].fillna(0)
        pca = PCA(n_components=2).fit_transform(X)
        df["PCA1"], df["PCA2"] = pca[:, 0], pca[:, 1]
        st.plotly_chart(px.scatter(df, x="PCA1", y="PCA2", color="schema_stress", title="PCA Projection"))

        tsne = TSNE(n_components=2, perplexity=min(30, len(df) - 1)).fit_transform(X)
        df["tSNE1"], df["tSNE2"] = tsne[:, 0], tsne[:, 1]
        st.plotly_chart(px.scatter(df, x="tSNE1", y="tSNE2", color="schema_stress", title="t-SNE Projection"))

if st.session_state.get("cumulative_data"):
    st.subheader("Clustered Trial Summary")
    combined = pd.concat([pd.DataFrame(log) for log in st.session_state["cumulative_data"]])
    grouped = combined.groupby(np.arange(len(combined)) // episodes).mean().reset_index()
    st.plotly_chart(px.line(grouped, y=["attunement_score", "schema_stress"], title="Trial Averages"))

    if len(grouped) > 2:
        clusters = KMeans(3).fit_predict(grouped[["attunement_score", "schema_stress"]].fillna(0))
        grouped["Cluster"] = clusters
        st.plotly_chart(px.scatter(grouped, x="attunement_score", y="schema_stress", color="Cluster", title="Clustered Trials"))
