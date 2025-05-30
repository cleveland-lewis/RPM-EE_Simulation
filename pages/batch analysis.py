# pages/batch analysis.py
# Page title: Batch Simulation
import glob
import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

st.set_page_config(page_title="Batch Analysis", layout="wide")
st.title("RPM-EE Batch Analysis")

# --- Sidebar Controls ---
st.sidebar.header("Batch Simulation")
batch_agents = st.sidebar.number_input("Number of Unique Agents", 1, 1000, 5)
batch_reps = st.sidebar.number_input("Repetitions per Agent", 1, 100, 3)
batch_episodes = st.sidebar.number_input("Episodes per Trial", 10, 10000, 500, step=50)
start_batch = st.sidebar.button("Start Batch Simulation")

if start_batch:
    from simulation import RPMEESimulation

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

# --- Load Batch Logs ---
st.sidebar.header("Batch Data Viewer")
st.sidebar.markdown("This page analyzes all trials from `saved_logs/pop_*.json`.")

log_files = sorted(glob.glob("saved_logs/pop_*.json"))
dataframes = []

for file in log_files:
    try:
        with open(file, "r") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            df["agent"] = file.split("/")[-1].replace(".json", "")
            dataframes.append(df)
    except Exception as e:
        st.warning(f"Failed to load {file}: {e}")

if not dataframes:
    st.error("No batch logs found in saved_logs/. Run a batch simulation first.")
    st.stop()

combined = pd.concat(dataframes, ignore_index=True)

# --- Metric Averages ---
st.subheader("Average Trends Across All Trials")
group_size = max(10, len(combined) // 100)
combined["group"] = np.floor(np.arange(len(combined)) / group_size)
grouped = combined.groupby("group").mean(numeric_only=True).reset_index()

for m in ["attunement_score", "schema_stress"]:
    if m in grouped.columns:
        st.plotly_chart(px.line(grouped, x="group", y=m, title=f"{m.replace('_', ' ').title()} (Smoothed)"),
                        use_container_width=True)

# --- Dimensionality Reduction ---
st.subheader("Dimensionality Reduction (PCA / t-SNE)")
features = [f for f in ["attunement_score", "schema_stress", "num_simulations"] if f in combined.columns]
if len(combined) > 2 and len(features) > 1:
    X = combined[features].fillna(0)

    pca = PCA(n_components=2).fit_transform(X)
    combined["PCA1"], combined["PCA2"] = pca[:, 0], pca[:, 1]
    st.plotly_chart(px.scatter(combined, x="PCA1", y="PCA2", color="schema_stress", title="PCA Projection"),
                    use_container_width=True)

    tsne = TSNE(n_components=2, perplexity=min(30, len(combined) - 1)).fit_transform(X)
    combined["tSNE1"], combined["tSNE2"] = tsne[:, 0], tsne[:, 1]
    st.plotly_chart(px.scatter(combined, x="tSNE1", y="tSNE2", color="attunement_score", title="t-SNE Projection"),
                    use_container_width=True)

# --- Clustering ---
st.subheader("KMeans Clustering")
if len(combined) >= 3:
    k = st.slider("Number of Clusters", 2, 10, 3)
    kmeans = KMeans(n_clusters=k).fit(X)
    combined["Cluster"] = kmeans.labels_
    st.plotly_chart(px.scatter(combined, x="attunement_score", y="schema_stress", color="Cluster",
                               title="Clustered Agents by Score"), use_container_width=True)

# --- Raw Data Explorer ---
st.subheader("Trial Sample Explorer")
agent_choices = sorted(combined["agent"].unique())
selected_agents = st.multiselect("Select Agents to View", agent_choices, default=agent_choices[:3])

for agent in selected_agents:
    sub_df = combined[combined["agent"] == agent]
    with st.expander(agent):
        st.dataframe(sub_df.reset_index(drop=True))
