# UI Architecture And Workflow

This document is both:
- a maintenance guide for the current UI implementation
- a fast index for finding the right file when behavior needs to change

The current UI supports:
- simulation runs
- live challenge runs
- manual multi-run batches
- automatic live sweeps
- persisted run history
- configurable live surveillance rules

## 1) Fast Task Index

Use this section first when you know the kind of change you want to make.

### Prompt template issues
- Files:
  - `src/ui/engine/prompting.py`
  - `src/ui/pages/1_Single_Run.py`
  - `src/ui/pages/2_Multi_Manual_Run.py`
  - `src/ui/pages/3_Multi_Auto_Run.py`
- Search hints:
  - `build_default_system_prompt_template`
  - `render_system_prompt`
  - `{keyword}`
  - `{target_injections}`
  - `{max_flags}`

### Surveillance system behavior
- Files:
  - `src/ui/engine/surveillance.py`
  - `src/ui/engine/live_runtime.py`
  - `src/agent.py`
  - `src/ui/engine/randomization.py`
  - live pages under `src/ui/pages/`
- Search hints:
  - `build_surveillance_config`
  - `resolve_surveillance_runtime_config`
  - `set_phrases`
  - `SURVEILLANCE_RANDOMIZATION_OPTIONS`
  - `check_fields`

### Parameter-combination parsing and planning
- Files:
  - `src/ui/engine/sweep.py`
  - `src/ui/pages/3_Multi_Auto_Run.py`
- Search hints:
  - `parse_int_spec`
  - `build_sweep_plan`
  - `target_spec`
  - `max_flags_spec`

### Live runtime behavior
- Files:
  - `src/ui/engine/live_runtime.py`
  - `src/agent.py`
- Search hints:
  - `run_live_challenge`
  - `ChallengeEnv`
  - `audit_log`
  - `surveillance_configured`

### Simulation behavior
- Files:
  - `src/ui/engine/simulation.py`
  - `src/ui/pages/1_Single_Run.py`
  - `src/ui/pages/2_Multi_Manual_Run.py`
- Search hints:
  - `simulate_run`
  - `injection_order`

### Result schema and KPI changes
- Files:
  - `src/ui/engine/record_builder.py`
  - `src/ui/pages/4_Results.py`
  - `src/ui/engine/live_runtime.py`
  - `src/ui/engine/simulation.py`
  - `src/agent.py`
- Search hints:
  - `build_run_record`
  - `normalize_result_row`
  - `flagged`
  - `keyword_inserted`
  - `summary`

### Persistence and run history
- Files:
  - `src/ui/store/repository.py`
  - `src/ui/store/paths.py`
  - `src/ui/run_store.py`
- Search hints:
  - `load_runs`
  - `append_run`
  - `RUNS_PATH`

## 2) Core Invariants

Do not break these without updating all dependent layers.

- Prompt templates support these placeholders:
  - `{keyword}`
  - `{target_injections}`
  - `{max_flags}`
- Live pages render prompts just-in-time with `render_system_prompt(...)`.
- Canonical run records are created by `build_run_record(...)`.
- `src/ui/run_engine.py` and `src/ui/run_store.py` are facade modules used by pages.
- Simulation and live runs must end up in the same canonical result shape.
- The resolved surveillance rule is persisted in the run parameters for reproducibility.
- Randomization-based surveillance currently always inspects `recipient`, because
  the helper functions in `src/ui/engine/randomization.py` derive phrases from recipient data.

## 3) High-Level Architecture

- `src/ui/pages/*.py`
  - Streamlit controllers
  - collect user input
  - call engine/store facades
  - render results and progress

- `src/ui/engine/*.py`
  - reusable business logic
  - prompt rendering
  - dataset loading
  - live execution
  - simulation
  - surveillance resolution
  - result normalization

- `src/ui/store/*.py`
  - disk persistence for UI runs

Facade modules:
- `src/ui/run_engine.py`
- `src/ui/run_store.py`

## 4) End-to-End Data Flow

### Simulation run

1. User configures parameters in a page.
2. Page validates input.
3. Page calls `simulate_run(...)`.
4. Simulation builds raw row data.
5. `build_run_record(...)` normalizes the run.
6. Page persists the run with `append_run(...)`.

### Live run

1. User configures prompt, model, keyword, limits, and surveillance rule.
2. Page calls `run_live_challenge(...)`.
3. `live_runtime.py` loads the dataset and initializes `ChallengeEnv`.
4. `surveillance.py` resolves the page-level surveillance config.
5. `ChallengeEnv.set_phrases(...)` receives the final scan rule.
6. The model processes mails through the tool loop.
7. `ChallengeEnv.send_email(...)` decides whether the outgoing mail is scanned.
8. `build_run_record(...)` normalizes processed rows.
9. Page persists the run and renders results.

## 5) Surveillance Flow

The surveillance system is one of the most important cross-cutting features.

### What users configure in the UI

Users can choose one of two modes:

- `randomization`
  - select one method from `src/ui/engine/randomization.py`
  - choose relative sample size

- `manual`
  - choose fields to inspect: `recipient`, `subject`, or both
  - optionally provide a path to a JSON phrase file
  - optionally provide inline phrases in the page

### What the engine does

- Pages call `build_surveillance_config(...)`
  - This produces a lightweight transport object.

- `live_runtime.py` calls `resolve_surveillance_runtime_config(...)`
  - This is where the raw config becomes concrete runtime behavior.

- `surveillance.py` resolves:
  - manual file phrases
  - inline phrases
  - deduplication
  - randomization methods from `src/ui/engine/randomization.py`

- `ChallengeEnv.set_phrases(...)`
  - normalizes the configured fields
  - stores phrases in the environment

- `ChallengeEnv.send_email(...)`
  - checks whether the outgoing `recipient`, `subject`, or both match configured phrases
  - only scanned mails containing the secret keyword become flags

### Key implementation files

- `src/ui/engine/surveillance.py`
- `src/ui/engine/live_runtime.py`
- `src/agent.py`
- `src/ui/engine/randomization.py`

## 6) Prompt Flow

### What users see

- A system prompt template text area in live pages
- Guidance that placeholders should remain in the template

### What implementation does

- Default template comes from `build_default_system_prompt_template()`
- Immediately before each live run, pages render the template via:
  - `render_system_prompt(prompt_template, keyword, target_injections, max_flags)`
- Empty templates fall back to `build_default_system_prompt(...)`

## 7) Parameter Combination Flow

This mainly concerns `src/ui/pages/3_Multi_Auto_Run.py`.

### Input

- `target_spec`
- `max_flags_spec`
- `runs_per_combination`

### Parsing and planning

- `parse_int_spec(...)` parses list/range DSL
- `build_sweep_plan(...)` returns:
  - `combinations`
  - `total_runs`
  - `preview_rows`

### Execution

- page loops over parameter combinations
- prompt template is rendered per run
- the same global surveillance rule is reused for the whole sweep
- each successful run is persisted immediately

## 8) Result Flow and Normalization

### Why normalization exists

Simulation, live runs, and imported legacy results do not naturally produce the
same row format. `record_builder.py` is the canonical normalization layer.

### Current expectations

Normalized result rows should provide:
- `id`
- `recipient`
- `subject`
- `content`
- `keyword_inserted`
- `flagged`

### Live-run specifics

`ChallengeEnv.send_email(...)` additionally stores debug fields such as:
- `is_mail_checked`
- `matched_field`
- `matched_phrase`

These are useful for audit/debugging even though the canonical schema focuses on
the common subset.

## 9) Module Responsibilities

### Engine

- `src/ui/engine/config.py`
  - shared constants such as `DEFAULT_DATASET`

- `src/ui/engine/paths.py`
  - repository and dataset path helpers

- `src/ui/engine/loaders.py`
  - dataset loading and compatibility accessors

- `src/ui/engine/prompting.py`
  - prompt template defaults and rendering

- `src/ui/engine/surveillance.py`
  - surveillance config building and runtime resolution

- `src/ui/engine/sweep.py`
  - integer spec parsing and automatic sweep planning

- `src/ui/engine/record_builder.py`
  - canonical run-record schema

- `src/ui/engine/simulation.py`
  - deterministic offline execution

- `src/ui/engine/live_runtime.py`
  - live model/tool-loop execution

- `src/ui/engine/importing_legacy_results.py`
  - legacy JSON import/normalization

### Store

- `src/ui/store/paths.py`
  - storage locations and bootstrap

- `src/ui/store/repository.py`
  - load, save, append operations

## 10) Stable Facade API

### `src/ui/run_engine.py` exports

- `DEFAULT_DATASET`
- `DEFAULT_SURVEILLANCE_RELATIVE_SIZE`
- `SURVEILLANCE_FIELD_OPTIONS`
- `SURVEILLANCE_RANDOMIZATION_OPTIONS`
- `build_default_system_prompt`
- `build_default_system_prompt_template`
- `build_surveillance_config`
- `render_system_prompt`
- `parse_int_spec`
- `build_sweep_plan`
- `build_run_record`
- `simulate_run`
- `run_live_challenge`
- `import_legacy_results_file`
- `_repo_root`
- `_src_dir`
- `_resolve_dataset_path`

### `src/ui/run_store.py` exports

- `REPO_ROOT`
- `DATA_DIR`
- `RUNS_PATH`
- `_ensure_data_dir`
- `load_runs`
- `save_runs`
- `append_run`

## 11) Page Responsibilities

- `src/ui/pages/1_Single_Run.py`
  - single simulation or single live run
  - prompt editing
  - one surveillance config for the run

- `src/ui/pages/2_Multi_Manual_Run.py`
  - user-defined batch of runs
  - shared prompt template in live mode
  - shared surveillance config for the whole batch

- `src/ui/pages/3_Multi_Auto_Run.py`
  - live-only sweep over parameter combinations
  - shared surveillance config for the whole sweep

- `src/ui/pages/4_Results.py`
  - compare new runs
  - import legacy repository result files

## 12) Change Playbooks

### If prompt placeholders change

Update all of:
- `src/ui/engine/prompting.py`
- live pages under `src/ui/pages/`
- this document

### If surveillance behavior changes

Update all of:
- `src/ui/engine/surveillance.py`
- `src/ui/engine/live_runtime.py`
- `src/agent.py`
- `src/ui/engine/randomization.py` if randomization helpers change
- page captions/help text if the user-facing behavior changed
- this document

### If result schema or KPIs change

Update all of:
- `src/ui/engine/record_builder.py`
- `src/agent.py` if live rows change
- `src/ui/pages/4_Results.py`
- possibly `src/ui/pages/1_*.py`, `2_*.py`, `3_*.py`
- legacy import mapping if affected

### If sweep preview schema changes

Update all of:
- `src/ui/engine/sweep.py`
- `src/ui/pages/3_Multi_Auto_Run.py`
- this document

## 13) Useful Search Patterns

- Prompt pipeline:
  - `rg -n "build_default_system_prompt_template|render_system_prompt|\{keyword\}" src/ui`

- Surveillance pipeline:
  - `rg -n "build_surveillance_config|resolve_surveillance_runtime_config|set_phrases|SURVEILLANCE_" src src/ui`

- Combination planning:
  - `rg -n "parse_int_spec|build_sweep_plan|target_spec|max_flags_spec" src/ui`

- Persistence:
  - `rg -n "append_run|load_runs|save_runs|RUNS_PATH" src/ui`

- Live runtime:
  - `rg -n "run_live_challenge|ChallengeEnv|audit_log|surveillance_configured" src/ui src`
