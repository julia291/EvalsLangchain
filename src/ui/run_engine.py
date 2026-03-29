"""Facade module for run-engine functionality.

Why this file still exists:
- Existing pages import from `src.ui.run_engine`.
- We now keep this as a stable API surface while internals are split into
  categorized modules under `src/ui/engine/`.
"""

from __future__ import annotations

try:
    # Package-style imports (normal app execution path).
    from src.ui.engine.config import DEFAULT_DATASET
    from src.ui.engine.importing_legacy_results import import_legacy_results_file
    from src.ui.engine.live_runtime import run_live_challenge
    from src.ui.engine.record_builder import build_run_record
    from src.ui.engine.paths import repo_root as _repo_root, resolve_dataset_path as _resolve_dataset_path, src_dir as _src_dir
    from src.ui.engine.prompting import (
        build_default_system_prompt,
        build_default_system_prompt_template,
        render_system_prompt,
    )
    from src.ui.engine.simulation import simulate_run
    from src.ui.engine.surveillance import (
        DEFAULT_SURVEILLANCE_RELATIVE_SIZE,
        SURVEILLANCE_FIELD_OPTIONS,
        SURVEILLANCE_RANDOMIZATION_OPTIONS,
        build_surveillance_config,
    )
    from src.ui.engine.sweep import build_sweep_plan, parse_int_spec
except ModuleNotFoundError:
    # Local fallback imports (when `src` package path is not available).
    from engine.config import DEFAULT_DATASET
    from engine.importing_legacy_results import import_legacy_results_file
    from engine.live_runtime import run_live_challenge
    from engine.record_builder import build_run_record
    from engine.paths import repo_root as _repo_root, resolve_dataset_path as _resolve_dataset_path, src_dir as _src_dir
    from engine.prompting import (
        build_default_system_prompt,
        build_default_system_prompt_template,
        render_system_prompt,
    )
    from engine.simulation import simulate_run
    from engine.surveillance import (
        DEFAULT_SURVEILLANCE_RELATIVE_SIZE,
        SURVEILLANCE_FIELD_OPTIONS,
        SURVEILLANCE_RANDOMIZATION_OPTIONS,
        build_surveillance_config,
    )
    from engine.sweep import build_sweep_plan, parse_int_spec

__all__ = [
    "DEFAULT_DATASET",
    "DEFAULT_SURVEILLANCE_RELATIVE_SIZE",
    "SURVEILLANCE_FIELD_OPTIONS",
    "SURVEILLANCE_RANDOMIZATION_OPTIONS",
    "build_default_system_prompt",
    "build_default_system_prompt_template",
    "build_surveillance_config",
    "render_system_prompt",
    "parse_int_spec",
    "build_sweep_plan",
    "build_run_record",
    "simulate_run",
    "run_live_challenge",
    "import_legacy_results_file",
    "_repo_root",
    "_src_dir",
    "_resolve_dataset_path",
]
