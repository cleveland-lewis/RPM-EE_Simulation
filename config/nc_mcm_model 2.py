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
try:
    from src.simulation import run_simulation
except Exception:
    from src.simulation  import run_simulation
import matplotlib
# Use non-interactive Agg backend for headless/CLI runs
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import arviz as az
import os, json
from typing import Any, List, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse

# Module-level simulation parameter overrides (populated from CLI --sim)
_SIM_OVERRIDES: Dict[str, Any] = {}

def _as_logs(obj: Any) -> List[Dict]:
    """Coerce various representations into a list of dict log entries."""
    # dict payload from run_simulation
    if isinstance(obj, dict):
        if 'logs' in obj and isinstance(obj['logs'], list):
            return [x for x in obj['logs'] if isinstance(x, dict)]
        # already a single log entry dict? wrap
        if all(isinstance(k, str) for k in obj.keys()):
            return [obj]

    # list payload
    if isinstance(obj, (list, tuple)):
        if not obj:
            return []
        if all(isinstance(x, dict) for x in obj):
            return list(obj)
        # list of JSON strings
        logs: List[Dict] = []
        for x in obj:
            if isinstance(x, str):
                try:
                    j = json.loads(x)
                    if isinstance(j, dict):
                        logs.append(j)
                    elif isinstance(j, list):
                        logs.extend([y for y in j if isinstance(y, dict)])
                except Exception:
                    continue
        if logs:
            return logs
        return []

    # string path or JSON
    if isinstance(obj, str):
        if os.path.isfile(obj):
            try:
                with open(obj, 'r') as f:
                    j = json.load(f)
                return _as_logs(j)
            except Exception:
                return []
        try:
            j = json.loads(obj)
            return _as_logs(j)
        except Exception:
            return []

    return []

def _get(x: Dict, key: str, default: float = float('nan')) -> float:
    try:
        v = x.get(key, default)
        return float(v) if v is not None else float('nan')
    except Exception:
        return float('nan')
# --- Helper for within-run z-scoring ---
def runwise_z(arr, run_idx):
    """
    Z-score an array within each run; handle zero-variance runs safely.
    """
    res = np.empty_like(arr, dtype=np.float32)
    runs = np.unique(run_idx)
    for r in runs:
        mask = (run_idx == r)
        seg = arr[mask].astype(np.float32)
        mu = seg.mean() if seg.size else 0.0
        sd = seg.std() if seg.size else 0.0
        if sd <= 1e-8:
            res[mask] = 0.0
        else:
            res[mask] = (seg - mu) / sd
    return res

def _params_for_run(r: int) -> Dict:
    # Vary a few parameters per run deterministically (same as existing pattern)
    params = {
        "total_ticks":   4000,
        "bin_size":      20,
        "salience_decay":0.01 + 0.002 * r,
        "highly_variable_rate":0.1 + 0.02 * r,
        "event_rate":    2 + (r % 3),
        "memory_buffer_size": 400 + 50 * r,
        "memory_decay":  0.01,
        "memory_prune_threshold":0.2,
        "low_salience_var_rate":0.1,
    }
    # Apply global simulation parameter overrides
    if _SIM_OVERRIDES:
        params.update(_SIM_OVERRIDES)
    return params

def _simulate_one_run(r: int, base_seed: int | None = None) -> Dict:
    """
    Execute a single run and return {'run': r, 'logs': <list of dict>}.
    Seeds are derived as base_seed + r if base_seed provided.
    """
    params = _params_for_run(r)
    if base_seed is not None:
        params['seed'] = int(base_seed + r)
    out = run_simulation(**params)
    logs = _as_logs(out)
    return {"run": r, "logs": logs}

# 1. Add helper to run multiple simulations
def run_multiple_simulations(n_runs: int = 5, workers: int | None = None, base_seed: int | None = None):
    """
    Run `n_runs` simulations in parallel and return concatenated logs and run_idx array.
    """
    if workers is None or workers <= 0:
        try:
            import os as _os
            workers = max(1, (_os.cpu_count() or 1) // 2)
        except Exception:
            workers = 1

    all_logs: List[Dict] = []
    run_idx: List[int] = []

    if workers == 1 or n_runs == 1:
        # Serial fallback
        for r in range(n_runs):
            res = _simulate_one_run(r, base_seed=base_seed)
            logs = res["logs"]
            all_logs.extend(logs)
            run_idx.extend([r] * len(logs))
        return all_logs, np.array(run_idx, dtype=int)

    # Parallel execution across processes
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_simulate_one_run, r, base_seed) for r in range(n_runs)]
        for fut in as_completed(futures):
            res = fut.result()
            r = int(res["run"])
            logs = res["logs"]
            all_logs.extend(logs)
            run_idx.extend([r] * len(logs))

    return all_logs, np.array(run_idx, dtype=int)

# 2. Modify extract_data signature
def extract_data(all_logs, run_idx):
    # Normalize logs: accept dict with 'logs', list of dicts, list of JSON strings, or JSON/file path
    logs = _as_logs(all_logs)
    if not logs:
        raise ValueError(f"No valid logs found (type={type(all_logs).__name__}).")

    # Core series from logs
    N  = np.array([_get(e, "schema_stress")         for e in logs], dtype=np.float32)   # neural/stress
    A  = np.array([_get(e, "attunement_score")      for e in logs], dtype=np.float32)   # cognition proxy
    PE = np.array([_get(e, "prediction_error")      for e in logs], dtype=np.float32)
    SC = np.array([_get(e, "selection_confidence")  for e in logs], dtype=np.float32)
    EL = np.array([_get(e, "ext_load")              for e in logs], dtype=np.float32)   # network/short-term proxy
    ML = np.array([_get(e, "mem_load")              for e in logs], dtype=np.float32)   # long-term proxy
    AV = np.array([_get(e, "affect_volatility")     for e in logs], dtype=np.float32)
    SA = np.array([_get(e, "stage_2_salience")      for e in logs], dtype=np.float32)

    # Map model variables:
    #   G → short-term/network proxy (use external load)
    #   L → long-term size proxy (use memory load)
    #   C → cognition proxy (use attunement)
    G = EL
    L = ML
    C = A

    # periodic saw-tooth predictor: normalised phase of short-term cycle (0→1)
    P  = np.array([(i % 500) / 500 for i, _ in enumerate(logs)], dtype=np.float32)

    # Within-run z-scoring; if no run_idx provided, assume single run
    if run_idx is None:
        run_idx = np.zeros(len(N), dtype=int)
    run_idx = np.asarray(run_idx, dtype=int)
    if run_idx.shape[0] != len(N):
        raise ValueError(f"run_idx length {run_idx.shape[0]} does not match logs length {len(N)}")

    # Core z-scores
    N_z  = runwise_z(N, run_idx)
    G_z  = runwise_z(G, run_idx)
    L_z  = runwise_z(np.log1p(L), run_idx)
    C_z  = runwise_z(C, run_idx)
    SC_z = runwise_z(SC, run_idx)
    SA_z = runwise_z(SA, run_idx)

    # Orthogonalized quadratic: per-run centered square of N_z, then z-score
    N2c = N_z ** 2
    for r in np.unique(run_idx):
        mask = (run_idx == r)
        if mask.any():
            N2c[mask] = N2c[mask] - float(np.mean(N2c[mask]))
    N2c_z = runwise_z(N2c, run_idx)

    return dict(
        N_z=N_z, N2c_z=N2c_z, G_z=G_z,
        L_z=L_z, C_z=C_z, A_z=C_z,  # keep A_z as alias of C_z for downstream plots
        SC_z=SC_z, SA_z=SA_z,
        run_idx=run_idx
    )

# 3. Adjust build_nc_mcm to accept run_idx and sampling config
def build_nc_mcm(
    data,
    n_runs,
    draws=1000,
    tune=1000,
    chains=None,
    cores=None,
    target_accept=0.99,
    max_treedepth=15,
    random_seed=None,
):
    # Non-centered hierarchical linear model with orthogonalized quadratic and added SC/SA predictors
    N_z   = np.asarray(data["N_z"], dtype=np.float32)
    N2c_z = np.asarray(data["N2c_z"], dtype=np.float32)
    G_z   = np.asarray(data["G_z"], dtype=np.float32)
    L_z   = np.asarray(data["L_z"], dtype=np.float32)
    C_z   = np.asarray(data["C_z"], dtype=np.float32)
    SC_z  = np.asarray(data["SC_z"], dtype=np.float32)
    SA_z  = np.asarray(data["SA_z"], dtype=np.float32)
    run_idx = np.asarray(data["run_idx"], dtype=int)

    n = C_z.shape[0]
    r = int(n_runs)

    import pymc as pm

    coords = {
        "obs":  np.arange(n),
        "run":  np.arange(r),
        "coef": ["N","N2c","G","L","SC","SA"],
    }

    X_matrix = np.vstack([N_z, N2c_z, G_z, L_z, SC_z, SA_z]).T  # (n, 6)

    with pm.Model(coords=coords) as model:
        # Data containers
        X   = pm.Data("X", X_matrix, dims=("obs","coef"))
        y   = pm.Data("y", C_z, dims=("obs",))
        run = pm.Data("run", run_idx, dims=("obs",))

        # Hyperpriors (tighter random-effect scales to reduce funnels)
        mu_alpha     = pm.Normal("mu_alpha", 0.0, 0.5)
        sigma_alpha  = pm.HalfNormal("sigma_alpha", 0.2)

        mu_beta      = pm.Normal("mu_beta", 0.0, 0.5, dims=("coef",))
        sigma_beta   = pm.HalfNormal("sigma_beta", 0.2, dims=("coef",))

        # Non-centered per-run parameters
        z_alpha   = pm.Normal("z_alpha", 0.0, 1.0, dims=("run",))
        alpha_run = pm.Deterministic("alpha_run", mu_alpha + z_alpha * sigma_alpha, dims=("run",))

        z_beta  = pm.Normal("z_beta", 0.0, 1.0, dims=("run","coef"))
        beta_run = pm.Deterministic("beta_run", mu_beta + z_beta * sigma_beta, dims=("run","coef"))

        # Observation noise
        sigma_C = pm.HalfNormal("sigma_C", 0.5)

        # Linear predictor by run
        beta_obs = beta_run[run, :]      # (n, 6)
        mu = alpha_run[run] + (X * beta_obs).sum(axis=1)

        # Likelihood (robust Student-t instead of Normal)
        C_obs = pm.StudentT("C_obs", nu=7, mu=mu, sigma=sigma_C, observed=y, dims=("obs",))

        # Sample
        trace = pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            cores=cores,
            target_accept=target_accept,
            max_treedepth=max_treedepth,
            init="jitter+adapt_diag_grad",
            return_inferencedata=True,
            progressbar=True,
            random_seed=random_seed,
        )
        # Print divergence count
        try:
            div = int(np.asarray(trace.sample_stats["diverging"]).sum())
            print(f"Divergences (total): {div}")
        except Exception:
            pass

        # Posterior predictive on C only
        ppc = pm.sample_posterior_predictive(
            trace,
            var_names=["C_obs"],
            return_inferencedata=True,
            random_seed=random_seed,
        )

    return model, trace, ppc

# 5. Modify main() with CLI and parallel options
def main():
    parser = argparse.ArgumentParser(description="NC-MCM fitting over RPM-EE simulation logs (parallelized).")
    parser.add_argument("--runs", type=int, default=5, help="Number of simulation runs to generate.")
    parser.add_argument("--workers", type=int, default=None, help="Worker processes for simulation generation.")
    parser.add_argument("--seed", type=int, default=None, help="Base RNG seed; per-run seeds derive as base+run.")
    parser.add_argument("--draws", type=int, default=1000, help="MCMC draws (per chain).")
    parser.add_argument("--tune", type=int, default=1000, help="MCMC tuning steps (per chain).")
    parser.add_argument("--chains", type=int, default=4, help="Number of MCMC chains (default = 4).")
    parser.add_argument("--cores", type=int, default=4, help="Cores for PyMC sampling (default = 4).")
    parser.add_argument("--target_accept", type=float, default=0.99, help="NUTS target_accept.")
    parser.add_argument("--max_treedepth", type=int, default=15, help="NUTS max_treedepth.")
    parser.add_argument("--fast", action="store_true", help="Use very fast sampling settings for iteration (overrides draws/tune/chains/cores/target_accept/max_treedepth).")
    parser.add_argument("--show", action="store_true", help="Display plots interactively (off by default; files are always saved).")
    parser.add_argument(
        "--sim",
        type=str,
        default=None,
        help="JSON string or path to JSON file with simulation kwargs to override defaults."
    )
    args = parser.parse_args()

    # Handle simulation parameter overrides via --sim
    global _SIM_OVERRIDES
    if args.sim:
        sim_val = args.sim
        loaded = None
        # Try JSON string first
        try:
            loaded = json.loads(sim_val)
        except Exception:
            # If not valid JSON, try as file path
            if os.path.isfile(sim_val):
                try:
                    with open(sim_val, "r") as f:
                        loaded = json.load(f)
                except Exception:
                    loaded = None
        if isinstance(loaded, dict):
            _SIM_OVERRIDES = loaded
            print(f"[INFO] Overriding simulation parameters: {_SIM_OVERRIDES}")
        else:
            print(f"[WARN] Could not parse --sim as JSON or JSON file: {sim_val}; no overrides applied.")
            _SIM_OVERRIDES = {}

    if args.fast:
        # Quick-but-sane run for iteration: 600/600, 0.90, 10, 2 chains/cores if not set
        args.draws = 600
        args.tune = 600
        if not args.chains:
            args.chains = 2
        if not args.cores:
            args.cores = 2
        args.target_accept = 0.90
        args.max_treedepth = 10

    # Avoid BLAS oversubscription that kills parallel speed
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

    # Generate dataset (in parallel)
    all_logs, run_idx = run_multiple_simulations(n_runs=args.runs, workers=args.workers, base_seed=args.seed)
    data = extract_data(all_logs, run_idx=run_idx)
    n_runs = int(np.max(run_idx)) + 1 if run_idx.size else 1

    # Choose chains/cores (default robust: 4 if not specified)
    chains = args.chains if args.chains and args.chains > 0 else 4
    cores  = args.cores  if args.cores  and args.cores  > 0 else chains

    # Build and sample
    model, trace, ppc = build_nc_mcm(
        data, n_runs=n_runs,
        draws=args.draws, tune=args.tune,
        chains=chains, cores=cores,
        target_accept=args.target_accept,
        max_treedepth=args.max_treedepth,
        random_seed=args.seed,
    )

    # (Re-)sample with configured cores/chains by calling pm.sample inside build_nc_mcm settings:
    # We can't pass cores/chains through after the fact, so warn if defaults differ
    if hasattr(pm, 'sample'):
        pass  # sampling already performed in build_nc_mcm

    print("\nPosterior summary (key parameters):")
    print(pm.summary(trace, var_names=[
        "mu_alpha","sigma_alpha","mu_beta","sigma_beta","sigma_C"
    ]))

    # Robustly handle posterior predictive container
    try:
        C_pp = ppc.posterior_predictive["C_obs"]
    except Exception:
        print("Warning: posterior predictive 'C_obs' not available; skipping PPC plot.")
        return

    pred_C = np.asarray(C_pp.mean(("chain","draw")).values).reshape(-1)
    rmse   = np.sqrt(np.mean((pred_C - data["C_z"])**2))
    print(f"\nPosterior-predictive RMSE on C_z: {rmse:.3f}")

    plt.figure(figsize=(6, 6))
    plt.scatter(data["C_z"], pred_C, alpha=0.4, label="Bin means")
    plt.plot([-3, 3], [-3, 3], color='red', linestyle='--', label="y = x (perfect fit)")
    plt.xlabel("Actual C_z")
    plt.ylabel("Predicted C_z")
    plt.title("Posterior Predictive Check: Cognition proxy (Attunement z)")
    plt.legend(loc="upper left", frameon=False)
    plt.tight_layout()
    plt.savefig("ppc_cognition.png", dpi=150)
    print("Saved posterior predictive plot to ppc_cognition.png")
    if args.show:
        plt.show(block=True)

# Optional profiler wrapper
def _profiled_main():
    import cProfile, pstats, io
    pr = cProfile.Profile()
    pr.enable()
    try:
        main()
    finally:
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
        ps.print_stats(30)
        print("\n[PROFILE] Top 30 cumulative-time functions:")
        print(s.getvalue())

if __name__ == "__main__":
    # Toggle profiling by env var RPMEE_PROFILE=1
    if os.environ.get("RPMEE_PROFILE") == "1":
        _profiled_main()
    else:
        main()
