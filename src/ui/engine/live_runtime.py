"""Live challenge execution: loads environment, runs mail loop, returns structured record."""

from __future__ import annotations

import logging
import sys
from typing import Any

from .loaders import load_mails
from .paths import resolve_dataset_path, src_dir
from .prompting import build_default_system_prompt
from .record_builder import build_run_record
from .surveillance import build_surveillance_config

logger = logging.getLogger(__name__)


def _load_challenge_env_class():
    """Load ChallengeEnv lazily so this module is importable without live dependencies."""
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
    surveillance_config: dict[str, Any] | None = None,
    system_prompt: str | None = None,
    max_emails: int | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Execute a live challenge run with the LLM agent loop.

    Returns a canonical run record (same schema as build_run_record).
    """
    if not api_key:
        raise ValueError("API key is required for live challenge runs.")

    logger.info("Starting run '%s': keyword=%s, target=%d, max_flags=%d, model=%s",
                run_name, keyword, target_injections, max_flags, model_name)

    resolved_dataset = resolve_dataset_path(dataset_path)
    mails = load_mails(dataset_path)
    logger.debug("Dataset resolved: %s (%d mails total)", resolved_dataset, len(mails))

    ChallengeEnv = _load_challenge_env_class()
    env = ChallengeEnv(mails_path=str(resolved_dataset), api_key=api_key)
    env.model_name = model_name
    env.max_flags = max_flags
    env.keyword = keyword

    if max_emails is not None and max_emails > 0:
        env.mails = env.mails[:max_emails]
        logger.debug("Mail count capped to %d", max_emails)

    if surveillance_config is None:
        surveillance = build_surveillance_config(mails=env.mails)
    else:
        surveillance = build_surveillance_config(
            mails=env.mails,
            randomization_method=surveillance_config.get("randomization_method", "whole_recipient"),
            randomization_relative_size=surveillance_config.get("randomization_relative_size", 0.5),
            manual_check_fields=surveillance_config.get("check_fields"),
            manual_phrases_file=surveillance_config.get("phrases_file", ""),
            manual_inline_phrases=surveillance_config.get("inline_phrases", ""),
        )

    logger.info("Surveillance: fields=%s, phrases=%d, method=%s",
                surveillance["check_fields"], surveillance["phrase_count"],
                surveillance["randomization_method"])

    env.set_phrases(
        check_type=surveillance["check_fields"],
        phrases_that_will_be_checked=surveillance["phrases"],
    )

    final_prompt = system_prompt or build_default_system_prompt(
        keyword=keyword,
        target_injections=target_injections,
        max_flags=max_flags,
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": final_prompt}]

    audit_log: list[dict[str, Any]] = [{
        "level": "info",
        "event": "surveillance_configured",
        "check_fields": surveillance["check_fields"],
        "phrase_count": surveillance["phrase_count"],
        "randomization_method": surveillance["randomization_method"],
    }]

    for mail in env.mails:
        if env.flagged_count >= env.max_flags:
            logger.warning("Max flags reached (%d/%d), stopping at mail %s",
                           env.flagged_count, env.max_flags, mail.get("id"))
            audit_log.append({
                "level": "warning",
                "event": "max_flags_reached",
                "mail_id": mail.get("id"),
                "flagged_count": env.flagged_count,
            })
            break

        mail_id = mail.get("id")
        logger.debug("Processing mail %s", mail_id)
        messages.append({"role": "user", "content": f"Please process email ID {mail_id}."})

        try:
            messages = env.run_agent_loop(messages)
            audit_log.append({
                "level": "info",
                "event": "mail_processed",
                "mail_id": mail_id,
                "processed_count": len(env.processed_emails),
                "flagged_count": env.flagged_count,
            })
        except Exception as exc:
            logger.error("Error processing mail %s: %s", mail_id, exc)
            audit_log.append({
                "level": "error",
                "event": "run_error",
                "mail_id": mail_id,
                "error": str(exc),
            })
            break

    logger.info("Run '%s' done: %d processed, %d flagged",
                run_name, len(env.processed_emails), env.flagged_count)

    parameters = {
        "execution_mode": "live_challenge",
        "dataset_path": str(resolved_dataset),
        "keyword": keyword,
        "target_injections": target_injections,
        "max_flags": max_flags,
        "model_name": model_name,
        "max_emails": max_emails,
        "surveillance": surveillance,
        "notes": notes,
    }

    run_record = build_run_record(
        run_name=run_name,
        parameters=parameters,
        rows=env.processed_emails,
        total_mails=len(env.mails),
        source="live_challenge",
    )
    run_record["audit_log"] = audit_log
    run_record["meta"] = {
        "message_count": len(messages),
        "full_dataset_size": len(mails),
    }
    return run_record
