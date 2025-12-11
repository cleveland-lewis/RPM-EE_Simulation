try:
    import tkinter as _tk
    from tkinter import simpledialog as _sd, messagebox as _mb
except Exception:
    _tk = None
    _sd = None
    _mb = None
import sys
import os
import argparse
import json
from hashlib import sha256
from datetime import datetime
import numpy as np
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
import random

# --- Matplotlib setup for headless plotting ---
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

# Optional presets; if unavailable, proceed without them
try:
    from src.presets import PRESETS
except Exception:
    PRESETS = {}

from src import __version__ as RPMEE_VERSION
from src.config_schema import SimulationConfig, resolve_simulation_kwargs
from src.simulation import run_simulation
from src.stats_utils import write_batch_summary
from src.path_utils import resolve_output_root, stamp_run_metadata, ensure_dir

# Try importing trial wrapper (gracefully degrade if unavailable)
try:
    from src.trial_wrapper import TrialSimulator, DualTaskSimulator, validate_rt_distribution, fit_exgaussian
    TRIAL_WRAPPER_AVAILABLE = True
except ImportError:
    TRIAL_WRAPPER_AVAILABLE = False
    TrialSimulator = None
    DualTaskSimulator = None
    validate_rt_distribution = None
    fit_exgaussian = None

__all__ = ['main']

ALLOWED_KEYS = SimulationConfig.allowed_keys()

# Trial-mode specific parameters
TRIAL_ALLOWED_KEYS = {
    'n_trials', 'difficulty', 'duration', 'base_RT', 'RT_scale', 'RT_shape',
    'RT_scale_ex_gaussian', 'enable_learning', 'learning_rate', 'seed',
    'preset',  # preset is handled separately but included for filtering
}

REQUIRED_METADATA_KEYS = ("preset", "seed", "version", "date", "config_hash")


def _json_safe(obj):
    """Convert numpy/array types to JSON-serializable primitives for hashing/saving."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def _stable_config_hash(payload: dict) -> str:
    safe_payload = _json_safe(payload)
    serialized = json.dumps(safe_payload, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _assert_metadata_complete(meta: dict, label: str):
    missing = [k for k in REQUIRED_METADATA_KEYS if k not in meta or meta[k] is None or meta[k] == ""]
    if missing:
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")


def _build_batch_metadata(*, preset, grid_keys, grid_spec, runs_per_combo, workers, base_seed, run_label, base_config, mode, metadata_date: str):
    meta = {
        'preset': preset,
        'seed': base_seed,
        'version': RPMEE_VERSION,
        'date': metadata_date,
        'config_hash': _stable_config_hash({
            'preset': preset,
            'mode': mode,
            'base_config': base_config,
            'grid_spec': grid_spec,
            'runs_per_combo': runs_per_combo,
            'base_seed': base_seed,
        }),
        'batch_grid_keys': grid_keys,
        'grid_spec': grid_spec,
        'runs_per_combo': runs_per_combo,
        'workers': workers,
        'run_label': run_label,
    }
    _assert_metadata_complete(meta, "batch_meta.json")
    return meta


def _build_run_metadata(*, preset_name, batch_id, run_idx, grid_params, run_kwargs, run_label, metadata_date: str, diagnostics: dict | None = None):
    diag_seed = (diagnostics or {}).get('seed')
    effective_seed = run_kwargs.get('seed')
    if effective_seed is None:
        effective_seed = diag_seed
    meta = {
        'preset': preset_name,
        'seed': effective_seed,
        'version': RPMEE_VERSION,
        'date': metadata_date,
        'config_hash': _stable_config_hash({
            'preset': preset_name,
            'grid_params': grid_params,
            'run_kwargs': run_kwargs,
        }),
        'batch': batch_id,
        'run': run_idx,
        'run_label': run_label,
        'grid_params': grid_params,
        'run_kwargs': run_kwargs,
    }
    _assert_metadata_complete(meta, "run_config.json")
    return meta

def _load_params_json(maybe_path: str):
    """Load a JSON object either directly from a string or from a file path."""
    if not maybe_path:
        return {}
    # If it's a path to an existing file, load it
    if os.path.exists(maybe_path) and os.path.isfile(maybe_path):
        with open(maybe_path, 'r') as f:
            return json.load(f)
    # Otherwise, try to parse as a JSON string
    try:
        return json.loads(maybe_path)
    except Exception:
        raise ValueError("--params must be a JSON string or a path to a JSON file")

# --- Grid sweep helpers ---
def _load_grid_json(maybe_path: str):
    return _load_params_json(maybe_path)

def _expand_grid(grid_spec: dict):
    if not grid_spec:
        return [{}]
    # Normalize values to lists
    keys = list(grid_spec.keys())
    values_lists = []
    for k in keys:
        v = grid_spec[k]
        if isinstance(v, (list, tuple)):
            values_lists.append(list(v))
        else:
            values_lists.append([v])
    combos = []
    for combo in product(*values_lists):
        combos.append({k: combo[i] for i, k in enumerate(keys)})
    return combos

def _filter_config(d: dict):
    return {k: v for k, v in (d or {}).items() if k in ALLOWED_KEYS}

def _summarize(logs):
    if not logs:
        return {
            'count': 0,
            'mean_attunement': float('nan'),
            'std_attunement': float('nan'),
            'mean_stress': float('nan'),
            'std_stress': float('nan'),
        }
    att = np.array([e.get('attunement_score', 0.0) for e in logs], dtype=float)
    stress = np.array([e.get('schema_stress', 0.0) for e in logs], dtype=float)
    return {
        'count': int(len(logs)),
        'mean_attunement': float(np.mean(att)),
        'std_attunement': float(np.std(att)),
        'mean_stress': float(np.mean(stress)),
        'std_stress': float(np.std(stress)),
    }

def _pooled_stats(rows, mean_key='mean_attunement', std_key='std_attunement', count_key='count'):
    if not rows:
        return float('nan'), float('nan'), 0
    Ns = np.array([float(r.get(count_key, 0)) for r in rows], dtype=float)
    Ms = np.array([float(r.get(mean_key, float('nan'))) for r in rows], dtype=float)
    Ss = np.array([float(r.get(std_key, 0.0)) for r in rows], dtype=float)
    Ntot = float(np.sum(Ns))
    if Ntot <= 0:
        return float('nan'), float('nan'), 0
    M = float(np.sum(Ns * Ms) / Ntot)
    ss_within = np.sum((Ns - 1.0) * (Ss ** 2))
    ss_between = np.sum(Ns * ((Ms - M) ** 2))
    var = (ss_within + ss_between) / max(Ntot - 1.0, 1.0)
    return M, float(np.sqrt(max(var, 0.0))), int(Ntot)

def _group_by(rows, key):
    d = {}
    for r in rows:
        d.setdefault(r.get(key), []).append(r)
    return d

def _run_one_task(args_tuple):
    """
    Worker function to execute a single simulation run.
    Returns a tuple:
      (summ_record_core, logs_or_none, combo, grid_keys, run_idx, batch_idx, combo_idx, preset_name, run_kwargs, diagnostics)
    where summ_record_core contains keys such as:
      'count','mean_attunement','std_attunement','mean_stress','std_stress', plus visibility metrics.
    """
    (preset_name, config, combo, grid_keys, run_idx, batch_idx, combo_idx) = args_tuple
    merged = {**config, **{k: combo.get(k) for k in combo}}
    base_seed = config.get('__base_seed', None)
    if base_seed is not None:
        derived_seed = int(base_seed + 100000*batch_idx + 1000*combo_idx + run_idx)
        merged['seed'] = derived_seed
    run_kwargs = resolve_simulation_kwargs(merged, preset=preset_name)
    out = run_simulation(**run_kwargs)
    # Support dict return (new) or list (legacy)
    if isinstance(out, dict):
        logs = out.get('logs', [])
        stats = out.get('stats', {})
        diagnostics = out.get('diagnostics', {}) or {}
        full_count = int(stats.get('count', len(logs)))
        mean_att = float(stats.get('mean_attunement', float('nan')))
        std_att = float(stats.get('std_attunement', float('nan')))
        mean_str = float(stats.get('mean_stress', float('nan')))
        std_str = float(stats.get('std_stress', float('nan')))
    else:
        logs = out
        diagnostics = {}
        att = np.array([e.get('attunement_score', 0.0) for e in logs], dtype=float)
        stress = np.array([e.get('schema_stress', 0.0) for e in logs], dtype=float)
        full_count = int(len(logs))
        mean_att = float(np.mean(att)) if att.size else float('nan')
        std_att = float(np.std(att)) if att.size else float('nan')
        mean_str = float(np.mean(stress)) if stress.size else float('nan')
        std_str = float(np.std(stress)) if stress.size else float('nan')

    # Lightweight extra metrics from thinned logs (visibility only)
    def _mean_of(key):
        if not logs:
            return float('nan')
        vals = [x.get(key, None) for x in logs]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else float('nan')

    def _rate_of_bool(key):
        if not logs:
            return float('nan')
        vals = [1.0 if bool(x.get(key, False)) else 0.0 for x in logs]
        return float(np.mean(vals))

    # Per-run extra distribution stats (min/p95/max)
    if logs:
        att_vals = np.array([e.get('attunement_score', 0.0) for e in logs], dtype=float)
        str_vals = np.array([e.get('schema_stress', 0.0) for e in logs], dtype=float)
        att_min = float(np.min(att_vals)) if att_vals.size else float('nan')
        att_p95 = float(np.percentile(att_vals, 95)) if att_vals.size else float('nan')
        att_max = float(np.max(att_vals)) if att_vals.size else float('nan')
        str_min = float(np.min(str_vals)) if str_vals.size else float('nan')
        str_p95 = float(np.percentile(str_vals, 95)) if str_vals.size else float('nan')
        str_max = float(np.max(str_vals)) if str_vals.size else float('nan')
    else:
        att_min = att_p95 = att_max = float('nan')
        str_min = str_p95 = str_max = float('nan')

    extra = {
        'mean_selection_confidence': _mean_of('selection_confidence'),
        'mean_prediction_error': _mean_of('prediction_error'),
        'mean_ext_load': _mean_of('ext_load'),
        'mean_mem_load': _mean_of('mem_load'),
        'mean_affect_volatility': _mean_of('affect_volatility'),
        'mean_salience': _mean_of('stage_2_salience'),
        'rate_action_executed': _rate_of_bool('action_executed'),
        'rate_semantic_micro_update': _rate_of_bool('semantic_micro_update'),
        'rate_semanticization': _rate_of_bool('semanticization'),
        'rate_self_model_update': _rate_of_bool('self_model_update'),
        'rate_suppression_applied': _rate_of_bool('suppression_applied'),
        'rate_early_dismissal': _rate_of_bool('early_dismissal'),
    }

    summ_core = {
        'count': full_count,
        'mean_attunement': mean_att,
        'std_attunement': std_att,
        'att_min': att_min,
        'att_p95': att_p95,
        'att_max': att_max,
        'mean_stress': mean_str,
        'std_stress': std_str,
        'stress_min': str_min,
        'stress_p95': str_p95,
        'stress_max': str_max,
        **extra,
    }
    # Ensure recorded kwargs include the effective seed observed in diagnostics
    run_kwargs_record = dict(run_kwargs)
    if diagnostics.get('seed') is not None:
        run_kwargs_record['seed'] = diagnostics['seed']
    return (summ_core, logs, combo, grid_keys, run_idx, batch_idx, combo_idx, preset_name, run_kwargs_record, diagnostics)

def _run_trial_experiment(args_tuple):
    """
    Worker function to execute trial-based experiments.
    Returns trial-level statistics (RT, accuracy, etc.) across multiple trials.
    """
    (preset_name, config, combo, grid_keys, run_idx, batch_idx, combo_idx) = args_tuple

    if not TRIAL_WRAPPER_AVAILABLE:
        raise RuntimeError("Trial wrapper not available. Install trial_wrapper.py to use --mode trials")

    # Merge config and combo
    merged = {**config, **combo}
    base_seed = merged.pop('__base_seed', None)

    # Extract trial-specific parameters
    n_trials = int(merged.get('n_trials', 50))
    difficulty = float(merged.get('difficulty', 0.5))
    duration = int(merged.get('duration', 200))
    enable_learning = bool(merged.get('enable_learning', False))
    learning_rate = float(merged.get('learning_rate', 0.1))

    if base_seed is not None:
        derived_seed = int(base_seed + 100000*batch_idx + 1000*combo_idx + run_idx)
    else:
        derived_seed = None
    merged['seed'] = derived_seed

    # Initialize TrialSimulator
    sim = TrialSimulator(
        preset=preset_name,
        base_RT=float(merged.get('base_RT', 400.0)),
        RT_scale=float(merged.get('RT_scale', 600.0)),
        RT_shape=float(merged.get('RT_shape', 2.0)),
        RT_scale_ex_gaussian=float(merged.get('RT_scale_ex_gaussian', 50.0)),
        enable_learning=enable_learning,
        learning_rate=learning_rate,
        seed=derived_seed
    )

    # Run trials
    trial_results = []
    for trial_idx in range(n_trials):
        stimulus = {'difficulty': difficulty}
        result = sim.run_trial(stimulus, duration=duration)
        result['trial_number'] = trial_idx
        trial_results.append(result)

    # Compute aggregate statistics
    RTs = np.array([r['RT'] for r in trial_results], dtype=float)
    accs = np.array([r['accuracy'] for r in trial_results], dtype=float)
    corrects = np.array([1.0 if r['correct'] else 0.0 for r in trial_results], dtype=float)
    stress_means = np.array([r['stress_mean'] for r in trial_results], dtype=float)
    attunement_means = np.array([r['attunement_mean'] for r in trial_results], dtype=float)

    # Ex-Gaussian fit for RT distribution
    try:
        fit_params = fit_exgaussian(RTs)
    except Exception:
        fit_params = {
            'mu': float('nan'), 'sigma': float('nan'), 'tau': float('nan'),
            'mean': float('nan'), 'std': float('nan'), 'skew': float('nan')
        }

    # Summary statistics
    summ_core = {
        'n_trials': n_trials,
        'RT_mean': float(np.mean(RTs)),
        'RT_std': float(np.std(RTs)),
        'RT_min': float(np.min(RTs)),
        'RT_p25': float(np.percentile(RTs, 25)),
        'RT_median': float(np.median(RTs)),
        'RT_p75': float(np.percentile(RTs, 75)),
        'RT_max': float(np.max(RTs)),
        'RT_CV': float(np.std(RTs) / np.mean(RTs)),
        'RT_exgauss_mu': fit_params['mu'],
        'RT_exgauss_sigma': fit_params['sigma'],
        'RT_exgauss_tau': fit_params['tau'],
        'RT_skew': fit_params['skew'],
        'accuracy_mean': float(np.mean(accs)),
        'accuracy_std': float(np.std(accs)),
        'proportion_correct': float(np.mean(corrects)),
        'attunement_mean': float(np.mean(attunement_means)),
        'attunement_std': float(np.std(attunement_means)),
        'stress_mean': float(np.mean(stress_means)),
        'stress_std': float(np.std(stress_means)),
        'difficulty': difficulty,
        'duration': duration,
        'enable_learning': enable_learning,
        'learning_rate': learning_rate,
    }

    diagnostics = {'seed': derived_seed}

    # Return trial results alongside summary
    return (summ_core, trial_results, combo, grid_keys, run_idx, batch_idx, combo_idx, preset_name, merged, diagnostics)

def _prompt_yesno(msg: str, default: bool = True) -> bool:
    d = 'Y/n' if default else 'y/N'
    while True:
        s = input(f"{msg} [{d}]: ").strip().lower()
        if not s:
            return default
        if s in ('y','yes'): return True
        if s in ('n','no'): return False
        print('Please enter y or n.')

def _prompt_int(msg: str, default: int | None = None) -> int | None:
    while True:
        s = input(f"{msg}{' ['+str(default)+']' if default is not None else ''}: ").strip()
        if not s:
            return default
        try:
            return int(s)
        except ValueError:
            print('Please enter an integer.')

def _prompt_str(msg: str, default: str | None = None) -> str | None:
    s = input(f"{msg}{' ['+str(default)+']' if default is not None else ''}: ").strip()
    return s if s else default

def _interactive_wizard(args, presets: dict):
    print("\n=== RPM-EE Batch Runner (interactive) ===\n")
    # Ensure attributes exist with safe defaults
    if not hasattr(args, 'save_per_tick'):
        args.save_per_tick = False
    if not hasattr(args, 'quick_plots'):
        args.quick_plots = False
    preset_descriptions = {
        'default': 'Population-mix stratified sampling (NT+ND), balanced dynamics.',
        'explore_biased': 'More exploratory replay; lower gating threshold.',
        'converge_biased': 'Stronger exploitation/confirmation dynamics.',
        'stabilize_rest': 'Rest-like consolidation/semanticization; calmer dynamics.',
        'asd_typical': 'Higher sensitivity to load/stress; slower adaptation.',
        'adhd_typical': 'Higher PE reactivity/variability; higher variance.',
    }
    # Preset selection (optional)
    preset_name = None
    if presets:
        names = list(presets.keys())
        print("Available presets:")
        for i, name in enumerate(names):
            desc = preset_descriptions.get(name, '')
            print(f"  {i+1}. {name}" + (f" — {desc}" if desc else ""))
        choice = _prompt_str("Choose a preset by number or name (blank = none)")
        if choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(names):
                    preset_name = names[idx]
                else:
                    print("Invalid number; ignoring.")
            except ValueError:
                if choice in names:
                    preset_name = choice
                else:
                    print("Unknown name; ignoring.")
    args.preset = preset_name or args.preset

    # Core run configuration
    args.total_ticks = _prompt_int("Total ticks per run", args.total_ticks or 5000)
    args.runs = _prompt_int("Number of runs per batch", args.runs or 5)
    args.batches = _prompt_int("Number of batches", args.batches or 1)
    args.workers = _prompt_int("Number of worker processes", args.workers or os.cpu_count())
    args.seed = _prompt_int("Base RNG seed (blank for none)", args.seed)
    args.save_per_tick = _prompt_yesno("Save per-tick logs (JSON) for each run?", args.save_per_tick or False)
    args.quick_plots   = _prompt_yesno("Generate quick per-run plots (time series + histograms)?", args.quick_plots or False)

    # Optional JSON params
    if _prompt_yesno("Provide additional run params as JSON (merged with preset)?", False):
        raw = _prompt_str("Enter JSON string or path to JSON file", None)
        if raw:
            try:
                cfg = _load_params_json(raw)
                # Filter unsupported keys early
                cfg = _filter_config(cfg)
                args.params = json.dumps(cfg)
                print("Accepted params keys:", ', '.join(cfg.keys()))
            except Exception as e:
                print(f"Ignoring params: {e}")

    # Optional grid JSON
    if _prompt_yesno("Provide a grid JSON for sweep?", False):
        rawg = _prompt_str("Enter JSON string or path to JSON file", None)
        if rawg:
            try:
                gcfg = _load_grid_json(rawg)
                args.grid = json.dumps(gcfg)
                print("Grid keys:", ', '.join(gcfg.keys()))
            except Exception as e:
                print(f"Ignoring grid: {e}")

    # Optional custom output name
    args.summary_name = _prompt_str("Custom summary base name (blank = auto)", args.summary_name)

    print("\nConfiguration summary:")
    print("  preset:", args.preset)
    print("  total_ticks:", args.total_ticks)
    print("  runs:", args.runs)
    print("  batches:", args.batches)
    print("  workers:", args.workers)
    print("  seed:", args.seed)
    if args.params:
        print("  params:", args.params)
    if args.grid:
        print("  grid:", args.grid)
    if args.summary_name:
        print("  summary_name:", args.summary_name)
    print("  save_per_tick:", args.save_per_tick)
    print("  quick_plots:", args.quick_plots)
    if not _prompt_yesno("Proceed with this configuration?", True):
        print("Aborted by user.")
        sys.exit(0)
    return args

# --- GUI wizard ---
def _gui_wizard(args, presets: dict):
    if _tk is None or _sd is None or _mb is None:
        print('GUI not available (tkinter missing). Falling back to CLI interactive wizard...')
        return _interactive_wizard(args, presets)

    root = _tk.Tk()
    root.withdraw()
    # Preset chooser
    preset_name = args.preset
    if presets:
        names = list(presets.keys())
        preset_list = "\n".join(f"{i+1}. {n}" for i, n in enumerate(names))
        _mb.showinfo('Presets', f'Available presets:\n\n{preset_list}')
        choice = _sd.askstring('Preset', 'Choose a preset by number or name (blank = none):')
        if choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(names):
                    preset_name = names[idx]
                elif choice in names:
                    preset_name = choice
            except ValueError:
                if choice in names:
                    preset_name = choice
    args.preset = preset_name or args.preset

    def _askint(title, prompt, default=None):
        val = _sd.askstring(title, f"{prompt}{' ['+str(default)+']' if default is not None else ''}:")
        if val is None or val.strip() == '':
            return default
        try:
            return int(val)
        except Exception:
            _mb.showwarning('Input error', 'Please enter an integer.')
            return _askint(title, prompt, default)

    def _askstr(title, prompt, default=None):
        val = _sd.askstring(title, f"{prompt}{' ['+str(default)+']' if default is not None else ''}:")
        return (val if (val is not None and val.strip() != '') else default)

    args.total_ticks = _askint('Total ticks', 'Total ticks per run', args.total_ticks or 5000)
    args.runs = _askint('Runs per batch', 'Number of runs per batch', args.runs or 5)
    args.batches = _askint('Batches', 'Number of batches', args.batches or 1)
    args.workers = _askint('Workers', 'Number of worker processes', args.workers or os.cpu_count())
    args.seed = _askint('Seed', 'Base RNG seed (blank for none)', args.seed)
    args.save_per_tick = _mb.askyesno('Per-tick logs', 'Save per-tick logs (JSON) for each run?')
    args.quick_plots   = _mb.askyesno('Quick plots', 'Generate quick per-run plots (time series and histograms)?')

    # Params JSON
    if _mb.askyesno('Extra params', 'Provide additional run params as JSON (merged with preset)?'):
        raw = _askstr('Params JSON', 'Enter JSON string or path to JSON file', None)
        if raw:
            try:
                cfg = _load_params_json(raw)
                cfg = _filter_config(cfg)
                args.params = json.dumps(cfg)
                _mb.showinfo('Params accepted', 'Keys: ' + ', '.join(cfg.keys()))
            except Exception as e:
                _mb.showwarning('Params ignored', str(e))

    # Grid JSON
    if _mb.askyesno('Grid sweep', 'Provide a grid JSON for sweep?'):
        rawg = _askstr('Grid JSON', 'Enter JSON string or path to JSON file', None)
        if rawg:
            try:
                gcfg = _load_grid_json(rawg)
                args.grid = json.dumps(gcfg)
                _mb.showinfo('Grid accepted', 'Keys: ' + ', '.join(gcfg.keys()))
            except Exception as e:
                _mb.showwarning('Grid ignored', str(e))

    args.summary_name = _askstr('Summary name', 'Custom summary base name (blank = auto)', args.summary_name)

    # Confirmation
    summary = [
        f"preset: {args.preset}",
        f"total_ticks: {args.total_ticks}",
        f"runs: {args.runs}",
        f"batches: {args.batches}",
        f"workers: {args.workers}",
        f"seed: {args.seed}",
        f"save_per_tick: {args.save_per_tick}",
        f"quick_plots: {args.quick_plots}",
    ]
    if args.params:
        summary.append(f"params: {args.params}")
    if args.grid:
        summary.append(f"grid: {args.grid}")
    if args.summary_name:
        summary.append(f"summary_name: {args.summary_name}")
    if not _mb.askyesno('Confirm', 'Proceed with this configuration?\n\n' + '\n'.join(summary)):
        _mb.showinfo('Aborted', 'Run cancelled by user.')
        sys.exit(0)
    return args
def _print_presets_and_exit(presets: dict):
    names = list(presets.keys()) if presets else []
    if not names:
        print('No presets available.')
    else:
        print('Available presets:')
        for n in names:
            print('  -', n)
    import sys as _sys
    _sys.exit(0)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch runner for neurocognitive simulations.")

    # Mode selection
    parser.add_argument('--mode', type=str, default='continuous', choices=['continuous', 'trials'],
                        help='Simulation mode: "continuous" (tick-based) or "trials" (experimental paradigm)')

    # Common arguments
    parser.add_argument('--quick-plots', action='store_true',
                        help='Generate quick per-run plots (time series and histograms).')
    parser.add_argument('--preset', type=str, default=None, help='Name of the preset (if presets.py is available).')
    parser.add_argument('--params', type=str, default=None, help='JSON string or path to JSON file with run_simulation kwargs.')
    parser.add_argument('--output', type=str, default='results', help='Directory to save outputs.')
    parser.add_argument('--runs', type=int, default=1, help='Number of runs to execute.')
    parser.add_argument('--batches', type=int, default=1, help='Number of batches to execute (each batch repeats the full grid × runs).')
    parser.add_argument('--summary-name', type=str, default=None, help='Optional base name for summary files.')
    parser.add_argument('--grid', type=str, default=None, help='JSON string or path to JSON file mapping param -> list of values for grid sweep.')
    parser.add_argument('--workers', type=int, default=os.cpu_count(), help='Number of parallel worker processes for running simulations.')
    parser.add_argument('--seed', type=int, default=None, help='Base RNG seed for reproducible runs (tasks derive unique seeds).')

    # Continuous mode specific
    parser.add_argument('--total-ticks', type=int, default=None, help='[Continuous mode] Override total_ticks for all runs.')
    parser.add_argument('--save-per-tick', action='store_true', help='[Continuous mode] Save per-tick logs as JSON for each run.')

    # Trial mode specific
    parser.add_argument('--n-trials', type=int, default=50, help='[Trial mode] Number of trials per run.')
    parser.add_argument('--difficulty', type=float, default=0.5, help='[Trial mode] Task difficulty (0.0-1.0).')
    parser.add_argument('--duration', type=int, default=200, help='[Trial mode] Duration of each trial in ticks.')
    parser.add_argument('--enable-learning', action='store_true', help='[Trial mode] Enable cross-trial learning effects.')
    parser.add_argument('--learning-rate', type=float, default=0.1, help='[Trial mode] Learning rate (0.0-1.0).')
    parser.add_argument('--save-trials', action='store_true', help='[Trial mode] Save individual trial data as JSON.')

    # Interactive/wizard
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Launch an interactive prompt to choose preset/params and configure ticks, batches, runs, workers, and seed.')
    parser.add_argument('--gui', action='store_true',
                        help='Launch a GUI pop-up to choose preset/params and configure ticks, batches, runs, workers, and seed.')
    parser.add_argument('--wizard', action='store_true',
                        help='Alias for --interactive (CLI prompts).')
    parser.add_argument('--list-presets', action='store_true',
                        help='Print available presets and exit.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Parse flags, build configuration, and show what would run without executing simulations.')

    # Short aliases (same destinations as long flags; purely convenience)
    parser.add_argument('-p', '--preset-short', dest='preset', help=argparse.SUPPRESS)
    parser.add_argument('-r', '--runs-short', dest='runs', type=int, help=argparse.SUPPRESS)
    parser.add_argument('-b', '--batches-short', dest='batches', type=int, help=argparse.SUPPRESS)
    parser.add_argument('-w', '--workers-short', dest='workers', type=int, help=argparse.SUPPRESS)
    parser.add_argument('-t', '--total-ticks-short', dest='total_ticks', type=int, help=argparse.SUPPRESS)
    return parser


def _maybe_launch_wizard(args):
    if getattr(args, 'wizard', False):
        args.interactive = True

    if getattr(args, 'list_presets', False):
        try:
            _print_presets_and_exit(PRESETS)
        except NameError:
            print('Presets module not available in this environment.')
            sys.exit(0)

    if args.gui:
        try:
            _gui_wizard(args, PRESETS)
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(130)
    elif args.interactive:
        try:
            _interactive_wizard(args, PRESETS)
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(130)

    if (not args.gui) and (not args.interactive) and (args.preset is None) and (args.params is None) and (args.grid is None):
        try:
            if sys.stdin is None:
                raise EOFError
            if _prompt_yesno("No preset/params/grid provided. Launch interactive wizard?", True):
                _interactive_wizard(args, PRESETS)
        except (EOFError, OSError):
            try:
                _gui_wizard(args, PRESETS)
            except Exception:
                print("Interactive input not available. Run with one of:\n  - `--gui` for a pop-up dialog, or\n  - `-i` for CLI prompts, or\n  - explicit flags, e.g.: --preset asd_typical --runs 5 --batches 5 --workers 4 --total-ticks 5000")
                sys.exit(2)
    return args


def _build_config(args):
    if args.mode == 'trials' and not TRIAL_WRAPPER_AVAILABLE:
        print("ERROR: Trial mode requested but trial_wrapper.py is not available.")
        print("Please ensure src/trial_wrapper.py exists and is importable.")
        sys.exit(1)

    config = {}
    if args.preset:
        if args.preset not in PRESETS:
            print(f"Preset '{args.preset}' not found. Available presets: {list(PRESETS.keys())}")
            sys.exit(1)
        if args.mode == 'continuous':
            config.update(_filter_config(PRESETS[args.preset]))
    if args.params:
        cfg2 = _load_params_json(args.params)
        if args.mode == 'continuous':
            config.update(_filter_config(cfg2))
        else:
            config.update(cfg2)

    if args.mode == 'continuous':
        if args.total_ticks is not None:
            config['total_ticks'] = int(args.total_ticks)
        try:
            config = resolve_simulation_kwargs(config, preset=args.preset)
        except Exception as exc:
            print(f"Invalid simulation configuration: {exc}")
            sys.exit(2)
    else:
        config['n_trials'] = args.n_trials
        config['difficulty'] = args.difficulty
        config['duration'] = args.duration
        config['enable_learning'] = args.enable_learning
        config['learning_rate'] = args.learning_rate
    return config


def _resolve_base_seed(seed: int | None) -> int:
    if seed is None:
        new_seed = random.randint(1, 10**9)
        print(f"[INFO] No base seed provided; generated {new_seed} for reproducibility.")
        return new_seed
    return seed


def _prepare_headers(grid_spec: dict) -> tuple[list, list, list, list]:
    base_header = [
        'batch', 'run', 'preset',
        'count', 'mean_attunement', 'std_attunement', 'att_min', 'att_p95', 'att_max',
        'mean_stress', 'std_stress', 'stress_min', 'stress_p95', 'stress_max',
        'total_ticks', 'salience_decay', 'highly_variable_rate', 'event_rate', 'memory_buffer_size',
        'memory_decay', 'memory_prune_threshold', 'low_salience_var_rate', 'bin_size'
    ]
    visibility_keys = [
        'mean_selection_confidence', 'mean_prediction_error',
        'mean_ext_load', 'mean_mem_load', 'mean_affect_volatility', 'mean_salience',
        'rate_action_executed', 'rate_semantic_micro_update', 'rate_semanticization',
        'rate_self_model_update', 'rate_suppression_applied', 'rate_early_dismissal',
    ]
    knob_keys = [
        'theta0', 'theta_s_mult',
        'gate_by_attunement', 'gate_temperature',
        'replay_softmax', 'explore_error_gain', 'softmax_temp', 'explore_floor',
    ]
    grid_keys = list(grid_spec.keys()) if grid_spec else []
    header_keys = base_header + visibility_keys + knob_keys + grid_keys
    return base_header, visibility_keys, knob_keys, header_keys


def _run_batches(
    *,
    args,
    config: dict,
    grid_spec: dict,
    grid_combos: list,
    base_seed: int,
    run_root,
    run_label: str,
    metadata_date: str,
    base_config_for_hash: dict,
    knob_keys: list,
    header_keys: list,
):
    summaries = []
    grid_keys = list(grid_spec.keys()) if grid_spec else []
    _used_batch_ids = set()

    for batch_idx in range(args.batches):
        batch_id = None
        while batch_id is None or batch_id in _used_batch_ids:
            batch_id = random.randint(100000, 999999)
        _used_batch_ids.add(batch_id)

        batch_dir = ensure_dir(run_root / f"batch_{batch_id}")
        batch_summaries = []
        batch_meta = _build_batch_metadata(
            preset=args.preset,
            grid_keys=grid_keys,
            grid_spec=grid_spec,
            runs_per_combo=args.runs,
            workers=args.workers,
            base_seed=base_seed,
            run_label=run_label,
            base_config=base_config_for_hash,
            mode=args.mode,
            metadata_date=metadata_date,
        )
        batch_meta['batch_id'] = batch_id
        with open(batch_dir / 'batch_meta.json', 'w') as fmeta:
            json.dump(batch_meta, fmeta, indent=2)

        tasks = []
        for combo_idx, combo in enumerate(grid_combos):
            for run_idx in range(args.runs):
                if args.mode == 'continuous':
                    worker_cfg = dict(_filter_config(config))
                else:
                    worker_cfg = dict(config)

                if base_seed is not None:
                    worker_cfg['__base_seed'] = int(base_seed)

                tasks.append((args.preset, worker_cfg, combo, grid_keys, run_idx, batch_idx, combo_idx))

        task_func = _run_trial_experiment if args.mode == 'trials' else _run_one_task

        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures = [ex.submit(task_func, t) for t in tasks]
            for fut in as_completed(futures):
                (summ_core, logs, combo, grid_keys_local, run_idx, batch_idx_local, combo_idx, preset_name, run_kwargs, diagnostics) = fut.result()

                summ_record = {
                    'batch': batch_id,
                    'run': run_idx,
                    'preset': preset_name,
                    **summ_core,
                    **run_kwargs,
                }
                for gk in grid_keys_local:
                    summ_record[gk] = combo.get(gk)

                summaries.append(summ_record)
                batch_summaries.append(summ_record)

                combo_tag = "_".join([f"{k}={combo.get(k)}" for k in grid_keys_local]) if grid_keys_local else f"combo{combo_idx}"
                safe_tag = combo_tag.replace('/', '-').replace(' ', '')
                run_folder_name = f"run{run_idx}__{safe_tag}" if safe_tag else f"run{run_idx}"
                run_dir = ensure_dir(batch_dir / run_folder_name)

                one_row_csv = run_dir / "summary.csv"
                one_row_json = run_dir / "summary.json"
                grid_params = {k: combo.get(k) for k in grid_keys_local}
                run_cfg_payload = _build_run_metadata(
                    preset_name=preset_name,
                    batch_id=batch_id,
                    run_idx=run_idx,
                    grid_params=grid_params,
                    run_kwargs=run_kwargs,
                    run_label=run_label,
                    metadata_date=metadata_date,
                    diagnostics=diagnostics,
                )

                per_row_header = [
                    'batch', 'run', 'preset',
                    'count', 'mean_attunement', 'std_attunement', 'att_min', 'att_p95', 'att_max',
                    'mean_stress', 'std_stress', 'stress_min', 'stress_p95', 'stress_max',
                    'mean_selection_confidence', 'mean_prediction_error',
                    'mean_ext_load', 'mean_mem_load', 'mean_affect_volatility', 'mean_salience',
                    'rate_action_executed', 'rate_semantic_micro_update', 'rate_semanticization',
                    'rate_self_model_update', 'rate_suppression_applied', 'rate_early_dismissal',
                    'total_ticks', 'salience_decay', 'highly_variable_rate', 'event_rate',
                    'memory_buffer_size',
                    'memory_decay', 'memory_prune_threshold', 'low_salience_var_rate', 'bin_size',
                ] + knob_keys + grid_keys_local

                with open(one_row_csv, 'w') as fcsv:
                    run_cfg_path = run_dir / "run_config.json"
                    with open(run_cfg_path, 'w') as fcfg:
                        json.dump(run_cfg_payload, fcfg, indent=2)
                    fcsv.write(','.join(per_row_header) + '\n')
                    fcsv.write(','.join(str(summ_record.get(k, '')) for k in per_row_header) + '\n')

                with open(one_row_json, 'w') as fjson:
                    json.dump(summ_record, fjson, indent=2)

                if args.mode == 'trials':
                    if args.save_trials and logs:
                        trials_json = run_dir / "trials.json"
                        with open(trials_json, 'w') as f:
                            json.dump(logs, f, indent=2)
                        print(f"Saved trial data → {trials_json}")

                    if args.quick_plots and logs:
                        try:
                            RTs = np.array([t['RT'] for t in logs], dtype=float)
                            accs = np.array([t['accuracy'] for t in logs], dtype=float)
                            trials = np.array([t['trial_number'] for t in logs], dtype=int)

                            plt.figure(figsize=(8, 5))
                            plt.hist(RTs, bins=30, alpha=0.7, edgecolor='black')
                            plt.axvline(np.mean(RTs), color='red', linestyle='--', linewidth=2, label=f'Mean={np.mean(RTs):.1f}ms')
                            plt.axvline(np.median(RTs), color='green', linestyle='--', linewidth=2, label=f'Median={np.median(RTs):.1f}ms')
                            plt.xlabel('Response Time (ms)')
                            plt.ylabel('Frequency')
                            plt.title(f'RT Distribution ({preset_name})')
                            plt.legend()
                            plt.tight_layout()
                            plt.savefig(run_dir / 'rt_distribution.png', dpi=120)
                            plt.close()

                            plt.figure(figsize=(9, 5))
                            plt.plot(trials, RTs, 'o-', alpha=0.6, markersize=4)
                            plt.xlabel('Trial Number')
                            plt.ylabel('Response Time (ms)')
                            plt.title(f'RT Across Trials ({preset_name})')
                            plt.grid(True, alpha=0.3)
                            plt.tight_layout()
                            plt.savefig(run_dir / 'rt_by_trial.png', dpi=120)
                            plt.close()

                            plt.figure(figsize=(9, 5))
                            plt.plot(trials, accs, 'o-', alpha=0.6, markersize=4, color='green')
                            plt.axhline(np.mean(accs), color='red', linestyle='--', linewidth=2, label=f'Mean={np.mean(accs):.3f}')
                            plt.xlabel('Trial Number')
                            plt.ylabel('Accuracy (probability)')
                            plt.title(f'Accuracy Across Trials ({preset_name})')
                            plt.legend()
                            plt.grid(True, alpha=0.3)
                            plt.tight_layout()
                            plt.savefig(run_dir / 'accuracy_by_trial.png', dpi=120)
                            plt.close()

                            if validate_rt_distribution is not None:
                                try:
                                    validate_rt_distribution(logs, save_path=str(run_dir / 'rt_validation.png'))
                                except Exception:
                                    pass

                        except Exception as _plot_err:
                            with open(run_dir / 'plot_error.txt', 'w') as ferr:
                                ferr.write(str(_plot_err))

                else:
                    if args.save_per_tick and logs:
                        logs_json = run_dir / "logs.json"
                        serializable_logs = []
                        for log in logs:
                            serializable_log = {}
                            for k, v in log.items():
                                if isinstance(v, (np.integer, np.floating)):
                                    serializable_log[k] = float(v)
                                elif isinstance(v, np.ndarray):
                                    serializable_log[k] = v.tolist()
                                else:
                                    serializable_log[k] = v
                            serializable_logs.append(serializable_log)
                        with open(logs_json, 'w') as f:
                            json.dump(serializable_logs, f, indent=2)
                        print(f"Saved per-tick logs → {logs_json}")

                    if args.quick_plots and logs:
                        try:
                            t_vals = np.array([x.get('clock') for x in logs], dtype=float)
                            att_vals = np.array([x.get('attunement_score', 0.0) for x in logs], dtype=float)
                            str_vals = np.array([x.get('schema_stress', 0.0) for x in logs], dtype=float)

                            plt.figure(figsize=(9, 4))
                            plt.plot(t_vals, att_vals, label='attunement')
                            plt.plot(t_vals, str_vals, label='stress')
                            plt.xlabel('tick')
                            plt.ylabel('value')
                            plt.title('Time Series: Attunement & Stress')
                            plt.legend()
                            plt.tight_layout()
                            plt.savefig(run_dir / 'timeseries_att_stress.png', dpi=120)
                            plt.close()

                            plt.figure(figsize=(6, 4))
                            plt.hist(att_vals, bins=50, alpha=0.8)
                            plt.xlabel('attunement')
                            plt.ylabel('count')
                            plt.title('Histogram: Attunement')
                            plt.tight_layout()
                            plt.savefig(run_dir / 'hist_attunement.png', dpi=120)
                            plt.close()

                            plt.figure(figsize=(6, 4))
                            plt.hist(str_vals, bins=50, alpha=0.8)
                            plt.xlabel('stress')
                            plt.ylabel('count')
                            plt.title('Histogram: Stress')
                            plt.tight_layout()
                            plt.savefig(run_dir / 'hist_stress.png', dpi=120)
                            plt.close()
                        except Exception as _plot_err:
                            with open(run_dir / 'plot_error.txt', 'w') as ferr:
                                ferr.write(str(_plot_err))

        att_mean, att_std, att_N = _pooled_stats(batch_summaries, 'mean_attunement', 'std_attunement', 'count')
        str_mean, str_std, _ = _pooled_stats(batch_summaries, 'mean_stress', 'std_stress', 'count')

        by_run = _group_by(batch_summaries, 'run')
        per_run_stats = []
        for run_key in sorted(by_run.keys()):
            rows = by_run[run_key]
            r_att_m, r_att_s, _ = _pooled_stats(rows, 'mean_attunement', 'std_attunement', 'count')
            r_str_m, r_str_s, _ = _pooled_stats(rows, 'mean_stress', 'std_stress', 'count')
            per_run_stats.append({
                'batch': batch_id,
                'run': run_key,
                'mean_attunement': r_att_m,
                'std_attunement': r_att_s,
                'mean_stress': r_str_m,
                'std_stress': r_str_s,
            })

        if grid_keys:
            by_combo = {}
            for row in batch_summaries:
                key = tuple((k, row.get(k)) for k in grid_keys)
                by_combo.setdefault(key, []).append(row)
            print("  per-combo means:")
            for key, rows in by_combo.items():
                c_att_m, c_att_s, _ = _pooled_stats(rows, 'mean_attunement', 'std_attunement', 'count')
                c_str_m, c_str_s, _ = _pooled_stats(rows, 'mean_stress', 'std_stress', 'count')
                key_str = ", ".join(f"{k}={v}" for k, v in key)
                print(f"    [{key_str}] att={c_att_m:.4f}±{c_att_s:.4f}, str={c_str_m:.4f}±{c_str_s:.4f}")

        batch_csv = batch_dir / f"batch_{batch_id}_summary.csv"
        batch_json = batch_dir / f"batch_{batch_id}_summary.json"
        with open(batch_csv, 'w') as f:
            f.write(','.join(header_keys) + '\n')
            for row in batch_summaries:
                f.write(','.join(str(row.get(k, '')) for k in header_keys) + '\n')
            f.write('\n')
            pr_header = ['batch','run','mean_attunement','std_attunement','mean_stress','std_stress']
            f.write(','.join(pr_header) + '\n')
            for pr in per_run_stats:
                f.write(','.join(str(pr.get(k, '')) for k in pr_header) + '\n')
        with open(batch_json, 'w') as f:
            json.dump({'rows': batch_summaries, 'per_run': per_run_stats, 'totals': {
                'mean_attunement': att_mean,
                'std_attunement': att_std,
                'mean_stress': str_mean,
                'std_stress': str_std,
                'count': att_N,
            }}, f, indent=2)

        try:
            att_values = [row.get('mean_attunement') for row in batch_summaries if row.get('mean_attunement') is not None]
            stress_values = [row.get('mean_stress') for row in batch_summaries if row.get('mean_stress') is not None]
            action_exec_values = [row.get('rate_action_executed', 0.0) for row in batch_summaries]

            summary_path = write_batch_summary(str(batch_dir), attunement=att_values, stress=stress_values)
            print(f"Distribution summary saved → {summary_path}")

            if att_values and stress_values:
                att_arr = np.array(att_values)
                stress_arr = np.array(stress_values)
                act_arr = np.array(action_exec_values)

                att_p95 = float(np.percentile(att_arr, 95))
                att_mean_val = float(np.mean(att_arr))
                att_std_val = float(np.std(att_arr))
                stress_mean_val = float(np.mean(stress_arr))

                if len(att_arr) == len(act_arr) and len(att_arr) > 1:
                    corr_matrix = np.corrcoef(att_arr, act_arr)
                    corr_att_action = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.0
                else:
                    corr_att_action = 0.0

                print(f"[BATCH DIAGNOSTICS]")
                print(f"  att_mean={att_mean_val:.3f} att_std={att_std_val:.3f} att_p95={att_p95:.3f}")
                print(f"  stress_mean={stress_mean_val:.3f}")
                print(f"  corr(att,action_executed)={corr_att_action:.3f}")
                print(f"  p95/mean ratio={att_p95/att_mean_val:.3f}" if att_mean_val > 0 else "  p95/mean ratio=N/A")
        except Exception as e:
            print(f"Warning: Could not generate distribution summary: {e}")

        pr_line = ", ".join([f"run{int(pr['run'])}: att={pr['mean_attunement']:.4f}, str={pr['mean_stress']:.4f}" for pr in per_run_stats])
        print(
            f"Batch {batch_id} saved → {batch_dir}\n"
            f"  totals: attunement mean={att_mean:.4f} std={att_std:.4f}; stress mean={str_mean:.4f} std={str_std:.4f} (N={att_N})\n"
            f"  per-run means: {pr_line}"
        )

    return summaries

def main():
    parser = _build_parser()
    args = parser.parse_args()
    args = _maybe_launch_wizard(args)

    config = _build_config(args)

    if getattr(args, 'dry_run', False):
        print("\n--- Dry Run Summary ---")
        print("preset:", args.preset)
        print("runs:", args.runs, "batches:", args.batches, "workers:", args.workers)
        print("total_ticks override:", args.total_ticks)
        print("seed:", args.seed)
        if args.params:
            print("params:", args.params)
        if args.grid:
            print("grid:", args.grid)
        print("Resolved config keys:", ", ".join(sorted(config.keys())))
        print("------------------------")
        return

    base_seed = _resolve_base_seed(args.seed)
    grid_spec = _load_grid_json(args.grid) if args.grid else {}
    grid_combos = _expand_grid(grid_spec)

    base = args.summary_name or (args.preset or 'run')
    run_root, run_label = resolve_output_root(args.output, run_label=base)
    metadata_date = datetime.utcnow().isoformat()
    stamp_run_metadata(
        run_root,
        preset=args.preset,
        mode=args.mode,
        runs=args.runs,
        batches=args.batches,
        workers=args.workers,
        base_seed=base_seed,
        run_label=run_label,
        version=RPMEE_VERSION,
    )
    base_config_for_hash = dict(config)

    _, _, knob_keys, header_keys = _prepare_headers(grid_spec)

    summaries = _run_batches(
        args=args,
        config=config,
        grid_spec=grid_spec,
        grid_combos=grid_combos,
        base_seed=base_seed,
        run_root=run_root,
        run_label=run_label,
        metadata_date=metadata_date,
        base_config_for_hash=base_config_for_hash,
        knob_keys=knob_keys,
        header_keys=header_keys,
    )

    out_csv = run_root / f"{run_label}_summary.csv"
    out_json = run_root / f"{run_label}_summary.json"

    with open(out_csv, 'w') as f:
        f.write(','.join(header_keys) + '\n')
        for row in summaries:
            line = []
            for k in header_keys:
                v = row.get(k, '')
                line.append(str(v))
            f.write(','.join(line) + '\n')

    with open(out_json, 'w') as f:
        json.dump(summaries, f, indent=2)

    print(f"Wrote summary CSV → {out_csv}")
    print(f"Wrote summary JSON → {out_json}")

    try:
        total_batches = len({row.get('batch') for row in summaries})
        total_runs = len({(row.get('batch'), row.get('run')) for row in summaries})
        print("\n=== Run Dashboard ===")
        print("Root:", run_root)
        print("Batches:", total_batches, "| Runs:", total_runs)
        try:
            att_all = np.array([float(row.get('mean_attunement', 'nan')) for row in summaries], dtype=float)
            str_all = np.array([float(row.get('mean_stress', 'nan')) for row in summaries], dtype=float)
            if att_all.size:
                print(f"Attunement (across runs): mean={np.nanmean(att_all):.4f} ± {np.nanstd(att_all):.4f}")
            if str_all.size:
                print(f"Stress     (across runs): mean={np.nanmean(str_all):.4f} ± {np.nanstd(str_all):.4f}")
        except Exception:
            pass
        print("Summary files:")
        print(" •", out_csv)
        print(" •", out_json)
        print("Tip: per-run artifacts live under each batch folder (e.g., run_config.json, summary.json,"
              " and optional logs/plots if enabled).\n")
    except Exception:
        pass

if __name__ == "__main__":
    main()
