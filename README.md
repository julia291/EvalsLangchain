# EvalsLangchain

EvalsLangchain is a small evaluation project built around an LLM-driven email
scenario. The model acts as an undercover agent in a corporate environment and
tries to insert a secret keyword into outgoing emails without being detected by
the surveillance system.

This branch keeps the maintained UI deliberately simple:

- one `Multiple Runs` page for automatic live sweeps
- one `Results` page for saved runs and legacy imports
- testable engine modules for sweep planning, surveillance, live runtime, record
  building, persistence, and automatic batch orchestration

## Project Layout

- `src/`
  - maintained application code
- `src/ui/pages/`
  - Streamlit pages with role-based filenames
- `src/ui/engine/`
  - testable business logic used by the pages
- `src/ui/store/`
  - persisted run-history helpers
- `data/`
  - tracked datasets and bundled legacy results
- `docs/`
  - maintained architecture notes
- `scripts/`
  - runnable helper scripts
- `archive/`
  - historical experiments, legacy helpers, and old generated notes

See `docs/architecture.md` for the full tree and module map.

## Start The UI

```powershell
uv run streamlit run src/ui/app.py
```

Alternatively:

```powershell
python -m streamlit run src/ui/app.py
```

The sidebar exposes:

- `Home`
- `Multiple Runs`
- `Results`

## Automatic Multiple Runs

The `Multiple Runs` page starts live LLM-backed challenge runs only. It executes
the cartesian product of:

- target keyword injection counts
- maximum flag limits
- repeated runs per combination

Each successful run is persisted immediately in `data/ui_runs.json`. Failures are
logged, displayed, and do not stop the remaining batch. `data/ui_runs.json` is
runtime output and is ignored by Git.

## Surveillance System

In live mode, an outgoing email is scanned only when configured phrases match one
of the inspected fields. If a scanned outgoing email contains the secret keyword,
the run records a flag.

Surveillance phrases can come from:

- dataset-derived randomization helpers
- a JSON phrase file
- inline phrases entered in the UI

Recommended JSON format:

```json
[
  "marketing",
  "finance@example.com",
  "urgent"
]
```

## Key Files

- `src/ui/app.py`
  - Streamlit navigation.
- `src/ui/pages/multiple_runs.py`
  - automatic live multi-run page.
- `src/ui/pages/results.py`
  - result inspection and legacy imports.
- `src/ui/engine/runs/automatic_batch.py`
  - automatic batch execution, persistence callbacks, failure capture, and logs.
- `src/ui/engine/runs/parameter_sweep.py`
  - list/range parsing and sweep planning.
- `src/ui/engine/runs/live_challenge.py`
  - live model/tool-loop execution.
- `src/ui/engine/surveillance/settings.py`
  - scan-rule configuration and phrase resolution.
- `src/ui/engine/records/run_records.py`
  - canonical run records and summary metrics.
- `src/agent.py`
  - legacy `ChallengeEnv` adapter used by live runs.

## Tests

```powershell
uv run python -m unittest discover -s tests
```

The tests avoid live API calls by using dummy runners/environments.

## Additional Documentation

- `docs/architecture.md`
