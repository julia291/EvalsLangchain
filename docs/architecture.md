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
4. `src/ui/engine/runs/automatic_batch.py` executes each planned live run,
   persists successful runs immediately, records failures, and emits logs.
5. `src/ui/engine/runs/live_challenge.py` runs the model/tool loop against
   `ChallengeEnv`.
6. `src/ui/engine/records/run_records.py` normalizes rows and summary metrics.
7. `src/ui/store/repository.py` persists live runs by model name for the
   Results page.

## Module Responsibilities

- `src/ui/pages/`
  - Streamlit controllers only.
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
- `src/ui/engine/records/mail_dataset.py`
  - Dataset loading and mail field accessors.
- `src/ui/engine/records/run_records.py`
  - Canonical run schema and summary metrics.
- `src/ui/store/repository.py`
  - Run-history persistence.

## Important Invariants

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

## Where To Change Things

- UI navigation: `src/ui/app.py`
- Automatic batch controls: `src/ui/pages/multiple_runs.py`
- Result display: `src/ui/pages/results.py`
- Batch orchestration and logging: `src/ui/engine/runs/automatic_batch.py`
- Sweep parsing: `src/ui/engine/runs/parameter_sweep.py`
- Live model loop: `src/ui/engine/runs/live_challenge.py`
- Live tool environment: `src/agent.py`
- Surveillance rules: `src/ui/engine/surveillance/settings.py`
- Run records and result normalization: `src/ui/engine/records/run_records.py`
- Run persistence: `src/ui/store/repository.py`

## Testing Focus

- `tests/test_automatic_runs.py`
  - Naming, notes metadata, persistence, failure continuation, progress
    callbacks, and log emission without live API calls.
- `tests/test_sweep.py`
  - Parameter parsing and sweep previews.
- `tests/test_surveillance_runtime.py`
  - Surveillance settings resolution and live-runtime wiring with a dummy
    environment.
