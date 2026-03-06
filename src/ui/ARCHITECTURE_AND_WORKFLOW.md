# UI Implementation Annotations

This file is both:
- a user-friendly overview of how the UI works, and
- a fast working index for implementing changes efficiently.

## 1) Fast Task Index (Use This First)

Use this section to jump directly to the likely files for a task.

### Prompt template issues
- Files:
  - `src/ui/engine/prompting.py`
  - `src/ui/pages/1_Single_Run.py`
  - `src/ui/pages/2_Multi_Manual_Run.py`
  - `src/ui/pages/3_Multi_Auto_Run.py`
- Search hints:
  - `build_default_system_prompt_template`
  - `render_system_prompt`
  - `{keyword}` / `{target_injections}` / `{max_flags}`

### Parameter-combination parsing/planning
- Files:
  - `src/ui/engine/sweep.py`
  - `src/ui/pages/3_Multi_Auto_Run.py`
- Search hints:
  - `parse_int_spec`
  - `build_sweep_plan`
  - `target_spec` / `max_flags_spec`

### Live runtime behavior
- Files:
  - `src/ui/engine/live_runtime.py`
  - `src/agent.py`
- Search hints:
  - `run_live_challenge`
  - `ChallengeEnv`
  - `audit_log`

### Simulation behavior
- Files:
  - `src/ui/engine/simulation.py`
  - `src/ui/pages/1_Single_Run.py`
  - `src/ui/pages/2_Multi_Manual_Run.py`
- Search hints:
  - `simulate_run`
  - `injection_order`

### Result schema / KPI changes
- Files:
  - `src/ui/engine/record_builder.py`
  - `src/ui/pages/4_Results.py`
  - `src/ui/engine/live_runtime.py`
  - `src/ui/engine/simulation.py`
- Search hints:
  - `build_run_record`
  - `summary`
  - `results`

### Persistence / run history
- Files:
  - `src/ui/store/repository.py`
  - `src/ui/store/paths.py`
  - `src/ui/run_store.py`
- Search hints:
  - `load_runs`
  - `append_run`
  - `RUNS_PATH`

## 2) Core Invariants (Do Not Break)

- Prompt placeholders supported in templates:
  - `{keyword}`, `{target_injections}`, `{max_flags}`
- Live pages should render prompts just-in-time with `render_system_prompt(...)`.
- Canonical run records come from `build_run_record(...)`.
- `run_engine.py` and `run_store.py` are stable facade layers used by pages.
- UI wording prefers "parameter combinations" while function name `build_sweep_plan` stays for compatibility.

## 3) High-Level Architecture

- `src/ui/pages/*.py`
  - Streamlit controllers (input, orchestration, rendering).
- `src/ui/engine/*.py`
  - Reusable runtime/business logic.
- `src/ui/store/*.py`
  - Run persistence (`data/ui_runs.json`).

Facade modules:
- `src/ui/run_engine.py` (engine exports)
- `src/ui/run_store.py` (store exports)

## 4) End-to-End Data Flow

1. User configures run parameters in a page.
2. Page validates/parses inputs.
3. Page executes `simulate_run(...)` or `run_live_challenge(...)`.
4. Engine builds canonical record via `build_run_record(...)`.
5. Page persists using `append_run(...)`.
6. Results page loads records with `load_runs(...)`.

## 5) Prompt Flow (User + Implementation View)

### What users see
- A prompt template text area in live pages.
- Guidance that placeholders should be included.

### What implementation does
- Default template comes from `build_default_system_prompt_template()`.
- Right before each live run, template is rendered using:
  - `render_system_prompt(prompt_template, keyword, target_injections, max_flags)`
- If template is empty, render falls back to `build_default_system_prompt(...)`.

## 6) Parameter Combination Flow

### Input
- `3_Multi_Auto_Run.py` accepts range/list specs for targets and max flags.

### Parsing and planning
- `parse_int_spec(...)` converts text specs to validated integer lists.
- `build_sweep_plan(...)` builds:
  - `combinations`
  - `total_runs`
  - `preview_rows` (`target_injections`, `max_flags`, `runs_per_combination`, `total_planned_runs`)

### Execution
- Auto page iterates over combinations and repetitions.
- Prompt template is rendered per run.
- Successful runs are persisted immediately.

## 7) Module Responsibilities

### Engine
- `src/ui/engine/config.py`: shared constants (`DEFAULT_DATASET`)
- `src/ui/engine/paths.py`: path resolution utilities
- `src/ui/engine/loaders.py`: dataset loading and compatibility fields
- `src/ui/engine/prompting.py`: prompt template/render helpers
- `src/ui/engine/sweep.py`: parameter parsing and combination planning
- `src/ui/engine/record_builder.py`: canonical row/result schema
- `src/ui/engine/simulation.py`: deterministic offline execution
- `src/ui/engine/live_runtime.py`: live model/tool-loop execution
- `src/ui/engine/importing_legacy_results.py`: legacy JSON import/normalization

### Store
- `src/ui/store/paths.py`: storage paths and bootstrap
- `src/ui/store/repository.py`: load/save/append operations

## 8) Stable Facade API

### `src/ui/run_engine.py` exports
- `DEFAULT_DATASET`
- `build_default_system_prompt`
- `build_default_system_prompt_template`
- `render_system_prompt`
- `parse_int_spec`
- `build_sweep_plan`
- `build_run_record`
- `simulate_run`
- `run_live_challenge`
- `import_legacy_results_file`
- `_repo_root`, `_src_dir`, `_resolve_dataset_path`

### `src/ui/run_store.py` exports
- `REPO_ROOT`, `DATA_DIR`, `RUNS_PATH`
- `_ensure_data_dir`
- `load_runs`, `save_runs`, `append_run`

## 9) Page Responsibilities

- `src/ui/pages/1_Single_Run.py`
  - Single simulation/live run.
  - Live mode renders prompt from template per run.

- `src/ui/pages/2_Multi_Manual_Run.py`
  - Manually configured multi-run execution.
  - Live mode renders shared template per run config.

- `src/ui/pages/3_Multi_Auto_Run.py`
  - Live-only parameter-combination execution.
  - Uses `parse_int_spec(...)` and `build_sweep_plan(...)`.

- `src/ui/pages/4_Results.py`
  - Run comparison and legacy import UI.

## 10) Change Playbooks (Practical)

### If placeholder names change
Update all of:
- `src/ui/engine/prompting.py`
- page captions in live pages (`1_`, `2_`, `3_`)
- this annotations file

### If preview row schema changes
Update all of:
- `src/ui/engine/sweep.py`
- table expectations in `src/ui/pages/3_Multi_Auto_Run.py`
- this annotations file

### If run schema/KPIs change
Update all of:
- `src/ui/engine/record_builder.py`
- pages displaying KPIs/results (`1_`, `2_`, `3_`, `4_` as needed)
- legacy import mapping if affected

## 11) Useful Search Patterns

- Prompt pipeline:
  - `rg -n "build_default_system_prompt_template|render_system_prompt|\{keyword\}" src/ui`
- Combination planning:
  - `rg -n "parse_int_spec|build_sweep_plan|target_spec|max_flags_spec" src/ui`
- Persistence:
  - `rg -n "append_run|load_runs|save_runs|RUNS_PATH" src/ui`
- Live runtime:
  - `rg -n "run_live_challenge|ChallengeEnv|audit_log" src/ui src/agent.py`
