"""Facade for run-engine functionality used by the Multi Automatic Run page."""

from __future__ import annotations

try:
    from src.ui.engine.config import DEFAULT_DATASET
    from src.ui.engine.live_runtime import run_live_challenge
    from src.ui.engine.prompting import (
        build_default_system_prompt,
        build_default_system_prompt_template,
        render_system_prompt,
    )
    from src.ui.engine.surveillance import (
        DEFAULT_SURVEILLANCE_RELATIVE_SIZE,
        SURVEILLANCE_FIELD_OPTIONS,
        SURVEILLANCE_RANDOMIZATION_OPTIONS,
        build_surveillance_config,
    )
    from src.ui.engine.sweep import build_sweep_plan, parse_int_spec
except ModuleNotFoundError:
    from engine.config import DEFAULT_DATASET
    from engine.live_runtime import run_live_challenge
    from engine.prompting import (
        build_default_system_prompt,
        build_default_system_prompt_template,
        render_system_prompt,
    )
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
    "run_live_challenge",
]
