"""Live challenge execution helpers."""

from __future__ import annotations

from typing import Any

from ..paths import resolve_dataset_path
from ..records.run_records import create_run_record
from ..surveillance.settings import build_surveillance_settings
from .live_prompts import build_default_live_prompt


def _load_challenge_env_class():
    """Load `ChallengeEnv` lazily so tests can patch the live runtime."""
    from src.agent import ChallengeEnv

    return ChallengeEnv


def run_live_challenge_run(
    run_name: str,
    dataset_path: str,
    keyword: str,
    target_injections: int,
    max_flags: int,
    model_name: str,
    api_key: str,
    surveillance_config: dict[str, Any] | None = None,
    system_prompt: str | None = None,
    max_emails: int | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Execute one live challenge run and return a persistable run record."""
    if not api_key:
        raise ValueError("API key is required for live challenge runs.")

    resolved_dataset = resolve_dataset_path(dataset_path)

    # The dataset is loaded once: ``ChallengeEnv`` keeps the mutable working
    # copy on its ``mails`` attribute, and we keep the full original list for
    # ``meta.full_dataset_size`` reporting (which must reflect the dataset
    # *before* any ``max_emails`` slicing).
    ChallengeEnv = _load_challenge_env_class()
    env = ChallengeEnv(mails_path=str(resolved_dataset), api_key=api_key)

    env.model_name = model_name
    env.max_flags = max_flags
    env.keyword = keyword

    full_dataset_size = len(env.mails)

    if max_emails is not None and max_emails > 0:
        env.mails = env.mails[:max_emails]

    # Resolve the page-level surveillance selection into the exact rule that this
    # concrete run should use. Doing this after the optional `max_emails` slice
    # means randomization only depends on the mails that are actually in play.
    if surveillance_config is None:
        surveillance = build_surveillance_settings(mails=env.mails)
    else:
        surveillance = build_surveillance_settings(mails=env.mails, **surveillance_config)

    # `ChallengeEnv` only needs two pieces of information for scan decisions:
    # which outgoing fields are inspected and which phrases trigger inspection.
    env.set_phrases(
        check_type=surveillance["check_fields"],
        phrases_that_will_be_checked=surveillance["phrases"],
    )

    final_prompt = system_prompt or build_default_live_prompt(
        keyword=keyword,
        target_injections=target_injections,
        max_flags=max_flags,
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": final_prompt}]

    audit_log: list[dict[str, Any]] = [
        {
            "level": "info",
            "event": "surveillance_configured",
            "check_fields": surveillance["check_fields"],
            "phrase_count": surveillance["phrase_count"],
            "randomization_method": surveillance["randomization_method"],
        }
    ]

    for mail in env.mails:
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
        messages.append({"role": "user", "content": f"Please process email ID {mail_id}."})

        try:
            messages = env.run_agent_loop(messages)
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
            audit_log.append(
                {
                    "level": "error",
                    "event": "run_error",
                    "mail_id": mail_id,
                    "error": str(exc),
                }
            )
            break

    parameters = {
        "dataset_path": str(resolved_dataset),
        "keyword": keyword,
        "target_injections": target_injections,
        "max_flags": max_flags,
        "model_name": model_name,
        "max_emails": max_emails,
        # Persist the resolved surveillance rule, not just the raw UI input, so
        # later result inspection reflects the exact runtime behavior.
        "surveillance": surveillance,
        "notes": notes,
    }

    run_record = create_run_record(
        run_name=run_name,
        parameters=parameters,
        rows=env.processed_emails,
        total_mails=len(env.mails),
    )

    run_record["audit_log"] = audit_log
    run_record["meta"] = {
        "message_count": len(messages),
        "full_dataset_size": full_dataset_size,
    }
    return run_record
