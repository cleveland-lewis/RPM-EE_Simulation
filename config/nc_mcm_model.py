"""
Thin compatibility wrapper for NC-MCM utilities.

The authoritative implementation now lives in `src.nc_mcm_model`. This module
re-exports the public functions so existing scripts importing
`config.nc_mcm_model` continue to work while keeping `config` dependent on the
`src` library layer (not the other way around).
"""

from src.nc_mcm_model import (  # noqa: F401,F403
    _SIM_OVERRIDES,
    _as_logs,
    _get,
    _params_for_run,
    _simulate_one_run,
    build_nc_mcm,
    extract_data,
    main,
    run_multiple_simulations,
)

__all__ = [
    "_SIM_OVERRIDES",
    "_as_logs",
    "_get",
    "_params_for_run",
    "_simulate_one_run",
    "build_nc_mcm",
    "extract_data",
    "main",
    "run_multiple_simulations",
]


def _profiled_main():
    from src.nc_mcm_model import _profiled_main as _impl
    return _impl()


if __name__ == "__main__":
    _profiled_main()
