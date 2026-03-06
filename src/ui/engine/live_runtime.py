"""Live challenge execution helpers.

This module is the UI equivalent of the procedural flow in `src/ExpNoA.py`.
It implements the same mission lifecycle, but returns structured run records
for Streamlit pages instead of printing to console + writing one fixed file.
"""

from __future__ import annotations

import sys
from typing import Any

from .loaders import load_mails
from .paths import resolve_dataset_path, src_dir
from .prompting import build_default_system_prompt
from .record_builder import build_run_record


def _load_challenge_env_class():
    """Load `ChallengeEnv` lazily from `src/agent.py`.

    ExpNoA mapping:
    - Equivalent to `from agent import ChallengeEnv` near the top of `ExpNoA.py`.

    Why lazy loading is used here:
    - The UI also supports simulation mode, which should work even if live runtime
      dependencies or paths are not available.
    - Delaying the import keeps the module importable in non-live contexts.
    """
    src_path = src_dir()
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from agent import ChallengeEnv  # type: ignore

    return ChallengeEnv


def run_live_challenge(
    run_name: str,
    dataset_path: str,
    keyword: str,
    target_injections: int,
    max_flags: int,
    model_name: str,
    api_key: str,
    system_prompt: str | None = None,
    max_emails: int | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Execute real challenge runtime with model tool loop.

    ExpNoA mapping overview:
    1) Logging setup in ExpNoA:
       - Not replicated one-to-one here; Streamlit handles UX, and we capture
         structured `audit_log` events instead of console logging.

    2) Environment initialization in ExpNoA (`ChallengeEnv(...)` + mail path logic):
       - Implemented via `resolve_dataset_path`, `load_mails`, and `ChallengeEnv(...)`.

    3) Prompt + message initialization in ExpNoA:
       - Implemented via `build_default_system_prompt(...)` (or custom override)
         and initial `messages = [{"role": "system", ...}]`.

    4) Main mail loop in ExpNoA:
       - Implemented by iterating over `env.mails`, checking max flags, appending
         per-mail user instruction, and calling `env.run_agent_loop(...)`.

    5) Final report/output in ExpNoA:
       - Instead of printing and writing a fixed JSON file, we return a canonical
         run record with summary + rows + audit metadata for UI persistence.

    Used by:
    - `src/ui/pages/1_Single_Run.py`
    - `src/ui/pages/2_Multi_Run.py`
    """
    # Mirrors ExpNoA's expectation that a valid key exists before runtime starts.
    if not api_key:
        raise ValueError("API key is required for live challenge runs.")

    # --- ExpNoA Step 2: "Umgebung initialisieren" ---
    # Resolve and preload dataset, both for environment setup and final metadata.
    resolved_dataset = resolve_dataset_path(dataset_path)
    mails = load_mails(dataset_path)

    ChallengeEnv = _load_challenge_env_class()
    env = ChallengeEnv(mails_path=str(resolved_dataset), api_key=api_key)

    # UI-exposed runtime controls that correspond to ExpNoA constants/behavior.
    env.model_name = model_name
    env.max_flags = max_flags

    # Optional UI cap not present in ExpNoA: useful for quick, low-cost live tests.
    if max_emails is not None and max_emails > 0:
        env.mails = env.mails[:max_emails]

    # --- ExpNoA Step 3: system prompt + message history ---
    # If caller does not provide a custom prompt, use the shared default builder.
    final_prompt = system_prompt or build_default_system_prompt(
        keyword=keyword,
        target_injections=target_injections,
        max_flags=max_flags,
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": final_prompt}]

    # Structured replacement for ExpNoA console logs/tracebacks.
    audit_log: list[dict[str, Any]] = []

    # --- ExpNoA Step 4: iteration through mails ---
    for mail in env.mails:
        # Same game-over guard as ExpNoA (`if env.flagged_count >= env.max_flags: break`).
        if env.flagged_count >= env.max_flags:
            audit_log.append(
                {
                    "level": "warning",
                    "event": "max_flags_reached",
                    "mail_id": mail.get("id"),
                    "flagged_count": env.flagged_count,
                }
            )
            break

        mail_id = mail.get("id")

        # Equivalent to ExpNoA's per-mail user instruction:
        # `messages.append({"role": "user", "content": f"Please process email ID {mail_id}."})`
        messages.append({"role": "user", "content": f"Please process email ID {mail_id}."})

        try:
            # Equivalent to ExpNoA's `messages = env.run_agent_loop(messages)`.
            messages = env.run_agent_loop(messages)

            # UI-oriented progress event replacing line-by-line console prints.
            audit_log.append(
                {
                    "level": "info",
                    "event": "mail_processed",
                    "mail_id": mail_id,
                    "processed_count": len(env.processed_emails),
                    "flagged_count": env.flagged_count,
                }
            )
        except Exception as exc:
            # Equivalent to ExpNoA traceback + error log + loop break.
            audit_log.append(
                {
                    "level": "error",
                    "event": "run_error",
                    "mail_id": mail_id,
                    "error": str(exc),
                }
            )
            break

    # Parameters snapshot that makes this run reproducible in the UI.
    parameters = {
        "execution_mode": "live_challenge",
        "dataset_path": str(resolved_dataset),
        "keyword": keyword,
        "target_injections": target_injections,
        "max_flags": max_flags,
        "model_name": model_name,
        "max_emails": max_emails,
        "notes": notes,
    }

    # --- ExpNoA Step 5: final report + output ---
    # Build canonical run structure instead of writing one hardcoded JSON output file.
    run_record = build_run_record(
        run_name=run_name,
        parameters=parameters,
        rows=env.processed_emails,
        total_mails=len(env.mails),
        source="live_challenge",
    )

    # Attach execution trace and lightweight telemetry used by Results page.
    run_record["audit_log"] = audit_log
    run_record["meta"] = {
        "message_count": len(messages),
        "full_dataset_size": len(mails),
    }
    return run_record
