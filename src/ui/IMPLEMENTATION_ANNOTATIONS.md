# UI Implementation Annotations

This document describes the current UI architecture in `src/ui`, including runtime flow, module responsibilities, and stable import surfaces.

## 1) Quick Architecture Map

- `src/ui/pages/*.py`
  - Streamlit page controllers.
  - Own user input, validation, orchestration, and rendering.
- `src/ui/engine/*.py`
  - Reusable execution and transformation logic.
  - No page-specific Streamlit UI responsibilities.
- `src/ui/store/*.py`
  - Persistence for run history (`data/ui_runs.json`).

Compatibility facades:
- `src/ui/run_engine.py`: stable public imports for engine functionality.
- `src/ui/run_store.py`: stable public imports for storage functionality.

## 2) End-to-End Runtime Flow

1. User configures one or more runs in a page.
2. Page validates and normalizes parameters.
3. Page calls engine execution (`simulate_run` or `run_live_challenge`).
4. Engine returns a canonical run record (`build_run_record`).
5. Page persists with `append_run`.
6. Results page reads history via `load_runs`.
7. Optional legacy files are normalized with `import_legacy_results_file`.

## 3) Prompt Handling (Current Design)

Prompt handling is intentionally template-first.

Core functions (`src/ui/engine/prompting.py`):
- `build_default_system_prompt(keyword, target_injections, max_flags=None)`
  - Builds a fully rendered default prompt string.
- `build_default_system_prompt_template()`
  - Returns default prompt with unresolved placeholders:
    - `{keyword}`
    - `{target_injections}`
    - `{max_flags}`
- `render_system_prompt(prompt_template, keyword, target_injections, max_flags)`
  - Renders placeholders for each run.
  - Falls back to `build_default_system_prompt(...)` when template is empty.

Usage by pages:
- `1_Single_Run.py`
  - UI shows template text area.
  - Calls `render_system_prompt(...)` right before `run_live_challenge(...)`.
- `2_Multi_Manual_Run.py`
  - One template shared across manually configured runs.
  - Renders per run config before execution.
- `3_Multi_Auto_Run.py`
  - Template required for sweep combinations.
  - Renders per combination and repetition.

## 4) Sweep Handling (Current Design)

Sweep helpers live in `src/ui/engine/sweep.py`:
- `parse_int_spec(raw, minimum, label)`
  - Parses specs like `6,9,12`, `4-10`, `4-12:2`, and mixed forms.
  - Removes duplicates while preserving first-seen order.
  - Provides user-friendly `ValueError` messages.
- `build_sweep_plan(target_values, max_flag_values, runs_per_combination)`
  - Builds cartesian combinations.
  - Returns `(combinations, total_runs, preview_rows)`.
  - `preview_rows` currently includes:
    - `target_injections`
    - `max_flags`
    - `runs_per_combination`
    - `total_planned_runs`

Primary consumer:
- `src/ui/pages/3_Multi_Auto_Run.py`

## 5) Engine Module Responsibilities

### `src/ui/engine/config.py`
- `DEFAULT_DATASET`
- Shared default dataset path for all pages.

### `src/ui/engine/paths.py`
- `repo_root()`, `src_dir()`, `resolve_dataset_path(dataset_path)`
- Stable path resolution independent of launch directory.

### `src/ui/engine/loaders.py`
- `load_mails(dataset_path)`, `recipient(mail)`, `mail_text(mail)`
- Dataset loading and compatibility mapping (`recipient`/`empfänger`, `text`/`content`).

### `src/ui/engine/prompting.py`
- `build_default_system_prompt(...)`
- `build_default_system_prompt_template()`
- `render_system_prompt(...)`
- Template and render pipeline for live runs.

### `src/ui/engine/sweep.py`
- `parse_int_spec(...)`
- `build_sweep_plan(...)`
- Sweep input parsing and planning.

### `src/ui/engine/record_builder.py`
- `normalize_result_row(row, keyword)`
- `build_run_record(...)`
- Canonical result schema and shared KPI computation.

### `src/ui/engine/simulation.py`
- `injection_order(mails, strategy, seed)`
- `simulate_run(...)`
- Deterministic offline execution path.

### `src/ui/engine/live_runtime.py`
- `_load_challenge_env_class()`
- `run_live_challenge(...)`
- Real model/tool-loop execution using `ChallengeEnv`.

### `src/ui/engine/importing_legacy_results.py`
- `import_legacy_results_file(...)`
- Converts legacy result JSON into canonical run records.

## 6) Store Module Responsibilities

### `src/ui/store/paths.py`
- `REPO_ROOT`, `DATA_DIR`, `RUNS_PATH`
- `ensure_data_dir()`

### `src/ui/store/repository.py`
- `load_runs()`, `save_runs(runs)`, `append_run(run)`

## 7) Stable Facade Exports

### `src/ui/run_engine.py`
Current public exports:
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

### `src/ui/run_store.py`
Current public exports:
- `REPO_ROOT`, `DATA_DIR`, `RUNS_PATH`
- `_ensure_data_dir`
- `load_runs`, `save_runs`, `append_run`

## 8) Page Responsibilities

### `src/ui/pages/1_Single_Run.py`
- Runs one simulation or one live run.
- In live mode, renders prompt from template just-in-time.
- Persists and displays KPIs, table, and optional audit log.

### `src/ui/pages/2_Multi_Manual_Run.py`
- User defines multiple run configs manually.
- Supports simulation and live mode.
- In live mode, renders shared template per run config.

### `src/ui/pages/3_Multi_Auto_Run.py`
- Live-only parameter sweep.
- Parses sweep specs with `parse_int_spec(...)`.
- Builds execution matrix with `build_sweep_plan(...)`.
- Renders prompt template per combination and repetition.
- Persists each successful run immediately.

### `src/ui/pages/4_Results.py`
- Aggregates and compares saved runs.
- Supports import of legacy JSON outputs.

## 9) Notes for Future Changes

- If prompt placeholders change, update:
  - `build_default_system_prompt_template()`
  - `render_system_prompt(...)`
  - page captions that mention required placeholders.
- If sweep preview schema changes, update both:
  - `build_sweep_plan(...)`
  - the auto-run page table assumptions/documentation.
- Keep pages orchestration-focused; move reusable logic into `engine/`.
