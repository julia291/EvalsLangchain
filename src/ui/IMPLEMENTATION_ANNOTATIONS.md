# UI Implementation Annotations (Updated)

This file documents the **current** structure and responsibilities in `src/ui`.

## 1) Architectural Overview

The UI is organized into three layers:
- `pages/*.py`: Streamlit page controllers (inputs, execution triggers, output rendering).
- `engine/*.py`: execution and transformation logic for simulation/live/import modes.
- `store/*.py`: persistence logic for run history (`data/ui_runs.json`).

Compatibility facades:
- `src/ui/run_engine.py` re-exports engine APIs used by pages.
- `src/ui/run_store.py` re-exports store APIs used by pages.

---

## 2) Engine Module Map

### `src/ui/engine/config.py`
- `DEFAULT_DATASET`
- Purpose: one shared default dataset path for all run forms.

### `src/ui/engine/paths.py`
- `repo_root()`
- `src_dir()`
- `resolve_dataset_path(dataset_path)`
- Purpose: stable filesystem/path resolution independent of launch cwd.

### `src/ui/engine/loaders.py`
- `load_mails(dataset_path)`
- `recipient(mail)`
- `mail_text(mail)`
- Purpose: dataset loading and field compatibility (`recipient/empfänger`, `text/content`).

### `src/ui/engine/prompting.py`
- `build_default_system_prompt(keyword, target_injections)`
- Purpose: central default live-mode prompt template.

### `src/ui/engine/record_builder.py`
- `normalize_result_row(row, keyword)`
- `build_run_record(...)`
- Purpose: canonical run schema + shared KPI summary generation.

### `src/ui/engine/simulation.py`
- `injection_order(mails, strategy, seed)`
- `simulate_run(...)`
- Purpose: deterministic offline run path for fast testing.

### `src/ui/engine/live_runtime.py`
- `_load_challenge_env_class()`
- `run_live_challenge(...)`
- Purpose: real agent/model loop execution using `ChallengeEnv`.

### `src/ui/engine/importing_legacy_results.py`
- `import_legacy_results_file(...)`
- Purpose: convert legacy JSON results to canonical run schema.

---

## 3) Store Module Map

### `src/ui/store/paths.py`
- `REPO_ROOT`, `DATA_DIR`, `RUNS_PATH`
- `ensure_data_dir()`
- Purpose: storage path constants and directory bootstrap.

### `src/ui/store/repository.py`
- `load_runs()`
- `save_runs(runs)`
- `append_run(run)`
- Purpose: repository-style read/write/append for run history.

---

## 4) Facades (Stable Public Imports)

### `src/ui/run_engine.py`
Re-exports:
- `DEFAULT_DATASET`
- `build_default_system_prompt`
- `build_run_record`
- `simulate_run`
- `run_live_challenge`
- `import_legacy_results_file`
- path helper aliases (`_repo_root`, `_src_dir`, `_resolve_dataset_path`)

Why:
- Existing pages can keep importing from `src.ui.run_engine` even when internals move.

### `src/ui/run_store.py`
Re-exports:
- path constants (`REPO_ROOT`, `DATA_DIR`, `RUNS_PATH`)
- `_ensure_data_dir`
- `load_runs`, `save_runs`, `append_run`

Why:
- Existing pages keep stable imports while storage internals stay modular.

---

## 5) Page Responsibilities

### `src/ui/pages/1_Single_Run.py`
- Runs one experiment in simulation or live mode.
- Saves run via `append_run`.
- Shows KPIs + detailed rows + optional audit log.

### `src/ui/pages/2_Multi_Run.py`
- Runs batch experiments.
- Supports simulation/live mode.
- Saves each run as it completes.
- Shows progress and batch summary.

### `src/ui/pages/3_Results.py`
- Loads and compares saved runs.
- Shows per-run details and charts.
- Imports legacy result files into canonical run history.

---

## 6) End-to-End Flow

1. User configures run(s) in Single/Multi page.
2. Page calls engine function (`simulate_run` or `run_live_challenge`).
3. Engine returns canonical run record (`build_run_record`).
4. Page persists run via `append_run`.
5. Results page loads and compares records via `load_runs`.
6. Optional legacy files are normalized via `import_legacy_results_file` and persisted.
