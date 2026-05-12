# Architecture

This repository is organized around one maintained Streamlit workflow: automatic
live multi-runs plus result inspection.

## Project Tree

```text
EvalsLangchain/
|-- data/
|   |-- mails.json
|   `-- one_mail.json
|-- docs/
|   `-- architecture.md
|-- scripts/
|   `-- validate_project.py
|-- src/
|   |-- __init__.py
|   |-- agent.py
|   `-- ui/
|       |-- __init__.py
|       |-- app.py
|       |-- pages/
|       |   |-- multiple_runs.py
|       |   `-- results.py
|       |-- engine/
|       |   |-- records/
|       |   |-- runs/
|       |   `-- surveillance/
|       `-- store/
|-- tests/
|-- pyproject.toml
|-- uv.lock
`-- README.md
```

## UI Flow

1. `src/ui/app.py` exposes `Home`, `Multiple Runs`, and `Results`.
2. `src/ui/pages/multiple_runs.py` collects live settings, surveillance
   settings, parameter ranges, and the prompt template.
3. `src/ui/engine/runs/parameter_sweep.py` parses range/list input and builds
   the cartesian plan for `target_injections x max_flags`.
4. `src/ui/engine/preflight.py` validates every input (API key, dataset,
   phrase file, surveillance config, prompt template) up front. The
   Multiple Runs page is the single validation entry point: on Start it
   calls `validate_run_inputs(...)`, displays the full issue list, and
   only invokes the batch if the report is clean. The batch
   orchestrator itself does not validate and trusts its inputs.
5. `src/ui/engine/runs/automatic_batch.py` executes each planned live run,
   persists successful runs immediately, records failures, and emits logs.
6. `src/ui/engine/runs/live_challenge.py` runs the model/tool loop against
   `ChallengeEnv`.
7. `src/ui/engine/records/run_records.py` normalizes rows and summary metrics.
8. `src/ui/store/repository.py` persists live runs by model name for the
   Results page.

## Module Responsibilities

- `src/ui/pages/`
  - Streamlit controllers only.
- `src/ui/engine/preflight.py`
  - `validate_run_inputs(...)` returns a structured `ValidationReport`
    covering API key, dataset, phrase file, surveillance config,
    combinations, scalar bounds, and prompt template placeholders.
    The Multiple Runs page is the single caller in the maintained code
    path. `RunInputsInvalid` (a `ValueError` subclass carrying the
    report) is provided for scripts or future entry points that want a
    raise-on-error contract.
- `src/ui/engine/runs/automatic_batch.py`
  - Batch orchestration, run names, notes metadata, summary rows, logging, and
    failure capture.
- `src/ui/engine/runs/parameter_sweep.py`
  - Integer sweep parsing and cartesian plan construction.
- `src/ui/engine/runs/live_prompts.py`
  - Default live prompt templates and placeholder rendering.
- `src/ui/engine/runs/live_challenge.py`
  - Live challenge execution and audit-log collection.
- `src/ui/engine/surveillance/settings.py`
  - Transport settings, runtime phrase resolution, and scan matching.
- `src/ui/engine/surveillance/phrase_sources.py`
  - File and inline phrase loading.
- `src/ui/engine/surveillance/random_phrases.py`
  - Recipient-derived phrase sampling.
- `src/ui/engine/validation.py`
  - Fast diagnostics for imports, datasets, and grouped run storage.
- `src/ui/engine/records/mail_dataset.py`
  - Dataset loading and mail field accessors.
- `src/ui/engine/records/run_records.py`
  - Canonical run schema and summary metrics.
- `src/ui/store/repository.py`
  - Run-history persistence.

## Important Invariants

- All run inputs are validated by `src/ui/engine/preflight.py` at the
  page layer before any live LLM call. A failed pre-flight on the page
  stops the batch from starting and shows the issue list to the user.
  The batch orchestrator itself does not re-validate; direct callers
  (scripts, future entry points) are responsible for running
  pre-flight themselves if they want the same guarantee.
- The maintained run UI is live-only.
- Prompt templates support `{keyword}`, `{target_injections}`, and `{max_flags}`.
- Automatic run names encode their dimensions:
  `prefix-t{target_injections}-f{max_flags}-r{repetition}`.
- Successful runs are saved immediately so a later failure does not lose earlier
  results.
- Batch failures are logged and shown in the UI while remaining runs continue.
- The resolved surveillance rule is stored in each run record for reproducible
  result inspection.
- Persisted runs use schema version 2 and are grouped under
  `models.{model_name}.runs`.
- Each persisted run stores flattened `hyperparameters` for filtering and
  charting in the Results page.
- `data/ui_runs.json` is runtime output and ignored by Git.
- `scripts/validate_project.py` is the local validation entry point for
  imports, datasets, run storage, compilation, and tests.

## Where To Change Things

- UI navigation: `src/ui/app.py`
- Automatic batch controls: `src/ui/pages/multiple_runs.py`
- Result display: `src/ui/pages/results.py`
- Run-start input validation: `src/ui/engine/preflight.py`
- Batch orchestration and logging: `src/ui/engine/runs/automatic_batch.py`
- Sweep parsing: `src/ui/engine/runs/parameter_sweep.py`
- Live model loop: `src/ui/engine/runs/live_challenge.py`
- Live tool environment: `src/agent.py`
- Surveillance rules: `src/ui/engine/surveillance/settings.py`
- Run records and result normalization: `src/ui/engine/records/run_records.py`
- Run persistence: `src/ui/store/repository.py`
- Standing project diagnostics: `src/ui/engine/validation.py` and
  `scripts/validate_project.py`

## Testing Focus

- `tests/test_automatic_runs.py`
  - Naming, notes metadata, persistence, failure continuation, progress
    callbacks, and log emission without live API calls.
- `tests/test_sweep.py`
  - Parameter parsing and sweep previews.
- `tests/test_surveillance_runtime.py`
  - Surveillance settings resolution, normalization edge cases, and
    live-runtime wiring with a dummy environment.
- `tests/test_validation.py`
  - Dataset, run-store, and import validation behavior including error
    branches (missing file, invalid JSON, model_name mismatch, empty
    or null recipient).
- `tests/test_preflight.py`
  - Pre-flight happy path, every error branch, `RunInputsInvalid`
    message construction, and a batch-level integration test
    confirming `run_live` is never called when inputs are invalid.
- `tests/test_repository.py`
  - Run-store grouping, hyperparameter flattening, schema enforcement.
- `tests/test_repository_internals.py`
  - `_flatten`, `_ungroup`, corrupt-file logging, atomic save-write
    safety.
- `tests/test_phrase_sources.py`
  - Inline parsing, JSON phrase file loading, deduplication.
- `tests/test_random_phrases.py`
  - Each recipient-derived sampler under seeded randomness, defensive
    handling of malformed mails.
- `tests/test_run_records.py`
  - Mail-row normalization (current and legacy shapes), summary metrics,
    success criteria.
- `tests/test_mail_dataset.py`
  - Dataset loader shapes and field accessor coercions.
- `tests/test_live_prompts.py`
  - Default prompt rendering and template placeholder substitution.

## LLM Proxy Configuration

`src/agent.py` no longer mutates `os.environ["OPENAI_API_BASE"]`. The
proxy URL is resolved at `ChallengeEnv` construction time with the
precedence:

1. Explicit `proxy_url=` argument.
2. `EVALSLANGCHAIN_PROXY_URL` environment variable.
3. `DEFAULT_PROXY_URL` constant in `src/agent.py`.

This makes the live runtime testable without global state pollution
between processes.
