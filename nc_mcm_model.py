"""
nc_mcm_model.py  —  Enhanced NC-MCM with:
  • Z-scaling of neural (N) and network (G, L) variables
  • Non-linear term N²
  • Lagged dependence of G_t on G_{t−1}
  • Separate long-term size as an additional predictor of cognition
  • Posterior-predictive check
"""

import numpy as np
import pymc as pm
from src.simulation import run_simulation
import matplotlib.pyplot as plt
import arviz as az


# 1. Add helper to run multiple simulations
def run_multiple_simulations(n_runs: int = 5):
    """
    Run `n_runs` simulations with mildly different parameters to create
    a multi‑run dataset for hierarchical NC‑MCM.
    Returns concatenated log list and run_idx array.
    """
    all_logs = []
    run_idx  = []
    for r in range(n_runs):
        # Vary a few parameters per run
        params = {
            "total_ticks":   4000,
            "bin_size":      20,
            "salience_decay":0.01 + 0.002 * r,
            "highly_variable_rate":0.1 + 0.02 * r,
            "event_rate":    2 + r % 3,
            "memory_buffer_size": 400 + 50 * r,
            "memory_decay":  0.01,
            "memory_prune_threshold":0.2,
            "low_salience_var_rate":0.1
        }
        logs = run_simulation(**params)
        all_logs.extend(logs)
        run_idx.extend([r] * len(logs))
    return all_logs, np.array(run_idx, dtype=int)

# 2. Modify extract_data signature
def extract_data(logs, run_idx=None):
    """Pull arrays from log list and add a lagged G_{t−1} column."""
    N  = np.array([e["schema_stress"]                for e in logs], dtype=np.float32)
    G  = np.array([e["memory_stats"]["short_term_size"] for e in logs], dtype=np.float32)
    L  = np.array([e["memory_stats"]["long_term_size"]  for e in logs], dtype=np.float32)
    C  = np.array([e["attunement_score"]             for e in logs], dtype=np.float32)
    A  = np.array([e["avg_affect_feedback"]         for e in logs], dtype=np.float32)

    # periodic saw-tooth predictor: normalised phase of short-term cycle (0→1)
    P  = np.array([(i % 500) / 500 for i, _ in enumerate(logs)], dtype=np.float32)

    # Standardize & log-transform where sensible
    z = lambda x: (x - x.mean()) / x.std()
    N_z  = z(N)
    N2_z = z(N**2)
    G_z  = z(G)
    L_z  = z(np.log1p(L))          # log(1+L) stabilizes growth
    C_z  = z(C)
    A_z = z(A)
    P_z = z(P)

    # Lagged G (prepend 0 so array lengths match)
    G_prev_z = np.concatenate([[0.0], G_z[:-1]])

    # 6. In extract_data return dict, include run_idx:
    return dict(N_z=N_z, N2_z=N2_z, G_z=G_z, G_prev_z=G_prev_z,
                L_z=L_z, C_z=C_z, A_z=A_z, P_z=P_z,
                run_idx=run_idx if run_idx is not None else np.zeros(len(N_z), dtype=int))

# 3. Adjust build_nc_mcm to accept run_idx
def build_nc_mcm(data, n_runs, draws=1000, tune=1000):
    with pm.Model() as m:
        # Hyper-priors
        sigma_G = pm.HalfNormal("sigma_G", 1)
        sigma_C = pm.HalfNormal("sigma_C", 1)

        # ---------------- Level 2 ----------------
        # Hierarchical priors for α1, β1 varying by run
        mu_alpha = pm.Normal("mu_alpha", 0, 1)
        sigma_alpha = pm.HalfNormal("sigma_alpha", 1)
        alpha_run = pm.Normal("α1", mu=mu_alpha, sigma=sigma_alpha, shape=n_runs)

        α2 = pm.Normal("α2", 0, 1)           # quadratic N²
        δ  = pm.Normal("δ",  0, 1)           # lag term
        γ  = pm.Normal("gamma", 0, 1)        # periodic predictor

        G_hat = (alpha_run[data["run_idx"]] * data["N_z"] + α2*data["N2_z"] +
                 δ*data["G_prev_z"] + γ*data["P_z"])
        pm.Normal("G_obs", mu=G_hat, sigma=sigma_G, observed=data["G_z"])

        # ---------------- Level 3 ----------------
        mu_beta1 = pm.Normal("mu_beta1", 0, 1)
        sigma_beta1 = pm.HalfNormal("sigma_beta1", 1)
        beta1_run = pm.Normal("β1", mu=mu_beta1, sigma=sigma_beta1, shape=n_runs)
        # β1 = pm.Normal("β1", 0, 1)           # from short-term  # obsolete, now hierarchical
        β2 = pm.Normal("β2", 0, 1)           # from long-term
        β3 = pm.Normal("β3", 0, 1)           # affect feedback
        β4 = pm.Normal("β4", 0, 1)           # raw stress

        C_hat = (beta1_run[data["run_idx"]] * data["G_z"] + β2*data["L_z"] +
                 β3*data["A_z"] + β4*data["N_z"])
        pm.Normal("C_obs", mu=C_hat, sigma=sigma_C, observed=data["C_z"])

        trace = pm.sample(draws=draws, tune=tune, target_accept=0.9,
                          return_inferencedata=True)

        # Posterior-predictive
        ppc = pm.sample_posterior_predictive(trace, var_names=["G_obs","C_obs"])
    return m, trace, ppc

# 5. Modify main()
def main():
    all_logs, run_idx = run_multiple_simulations(n_runs=5)
    data = extract_data(all_logs, run_idx)
    n_runs = int(run_idx.max()) + 1
    model, trace, ppc = build_nc_mcm(data, n_runs=n_runs)

    print("\nPosterior summary (key parameters):")
    # 4. Update summary variable names later:
    print(pm.summary(trace, var_names=["mu_alpha","sigma_alpha","mu_beta1","sigma_beta1",
                                       "α2","δ","gamma","β2","β3","β4","sigma_G","sigma_C"]))

    # Basic posterior-predictive RMSE for C_z
    pred_C = ppc.posterior_predictive["C_obs"].mean(("chain","draw")).values
    rmse   = np.sqrt(np.mean((pred_C - data["C_z"])**2))
    print(f"\nPosterior-predictive RMSE on C_z: {rmse:.3f}")

    # Scatter plot actual vs posterior predictive mean for cognition
    plt.figure(figsize=(6, 6))
    # Scatter actual vs. predicted
    plt.scatter(data["C_z"], pred_C, alpha=0.4, label="Bin means")
    # Reference line y = x
    plt.plot([-3, 3], [-3, 3], color='red', linestyle='--', label="y = x (perfect fit)")
    plt.xlabel("Actual C_z")
    plt.ylabel("Predicted C_z")
    plt.title("Posterior Predictive Check: Attunement (z)")
    plt.legend(loc="upper left", frameon=False)
    plt.tight_layout()
    plt.savefig("ppc_cognition.png", dpi=150)
    print("Saved posterior predictive plot to ppc_cognition.png")
    plt.show(block=True)

if __name__ == "__main__":
    main()