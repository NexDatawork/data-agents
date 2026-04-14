"""Thin OpenAI API wrapper for OpenGraph AI engine calls.

TODO: Add Anthropic/Claude support via a provider flag.
TODO: Add batch mode for high-volume extraction workloads.
"""

from __future__ import annotations
import os


import logging
import time
from pathlib import Path
from typing import Any
from pathlib import Path

import openai

from engine.config import get_optional_env, get_required_env, load_env_config

logger = logging.getLogger(__name__)

# TODO: Make model name configurable via a config file or ENV.
_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TIMEOUT = 60.0
_ENV_LOADED = False


def _load_local_env() -> None:
    """Load key-value pairs from .env.local into process env if missing.

    This keeps CLI usage simple for local development sessions where users
    restart terminals and do not want to re-export OPENAI_API_KEY each time.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    _ENV_LOADED = True
    env_path = Path.cwd() / ".env.local"
    if not env_path.exists() or not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _make_client() -> openai.OpenAI:
    """Create an authenticated OpenAI client from environment variables."""
    _load_local_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set. "
            "Set it in .env.local or export it before running OpenGraph AI."
        )
    return openai.OpenAI(api_key=api_key, timeout=_DEFAULT_TIMEOUT)


def _resolve_model(override: str | None) -> str:
    """Return the model name to use, respecting env-var and caller overrides."""
    return override or os.environ.get("OPENAI_MODEL", _DEFAULT_MODEL)


def call_llm(prompt: str, *, model: str | None = None) -> str:
    """Call the configured OpenAI model with a single user prompt.

    Reads OPENAI_API_KEY from the environment.  Raises EnvironmentError
    if the key is absent so callers get a clear failure message instead
    of an obscure API 401.

    Args:
        prompt: The user message text.
        model:  Optional model override (falls back to OPENAI_MODEL env var or gpt-4o-mini).

    TODO: Add retry logic with exponential back-off on rate-limit errors.
    TODO: Add Claude/Anthropic support — swap client based on PROVIDER env var.
    """
    client = _make_client()
    response = client.chat.completions.create(
        model=_resolve_model(model),
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def call_llm_messages(
    messages: list[dict[str, str]],
    *,
    json_mode: bool = False,
    model: str | None = None,
) -> str:
    """Call the configured OpenAI model with a full messages list.

    Supports system + user + assistant turns and optional JSON output mode
    (``response_format={"type": "json_object"}``).  When ``json_mode=True``
    the model is instructed to return only valid JSON — no markdown, no prose.

    Args:
        messages:  List of ``{"role": ..., "content": ...}`` dicts.
        json_mode: When True, enables OpenAI's JSON response format.
                   Only supported by gpt-4o, gpt-4o-mini, gpt-4-turbo and newer.
        model:     Optional model override.

    Returns:
        Raw string content of the assistant response.

    Raises:
        EnvironmentError: If OPENAI_API_KEY is not set.
        openai.BadRequestError: If json_mode is used with an unsupported model.
    """
    client = _make_client()
    kwargs: dict[str, Any] = {
        "model": _resolve_model(model),
        "messages": messages,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""
_DEFAULT_TIMEOUT = 30.0
_RETRYABLE_EXCEPTIONS = (
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.InternalServerError,
    openai.RateLimitError,
)


def call_llm(
    prompt: str,
    *,
    system_prompt: str | None = None,
    response_format: dict[str, str] | None = None,
    max_retries: int = 3,
    search_from: str | Path | None = None,
) -> str:
    """Call the configured OpenAI model and return the response text.

    Reads `OPENAI_API_KEY` from the environment and never logs or prints the key.
    Retries transient connection/rate-limit failures with exponential back-off so
    higher-level extractors can safely process large multi-chunk inputs.
    """
    load_env_config(search_from=search_from)
    api_key = get_required_env("OPENAI_API_KEY", search_from=search_from)
    model = get_optional_env(
        "OPENAI_MODEL",
        _DEFAULT_MODEL,
        search_from=search_from,
    ) or _DEFAULT_MODEL
    client = openai.OpenAI(api_key=api_key, timeout=_DEFAULT_TIMEOUT)

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    attempts = max(1, max_retries)
    for attempt in range(1, attempts + 1):
        try:
            request_args: dict[str, Any] = {
                "model": model,
                "messages": messages,
            }
            if response_format is not None:
                request_args["response_format"] = response_format

            response = client.chat.completions.create(**request_args)
            return response.choices[0].message.content or ""
        except _RETRYABLE_EXCEPTIONS as exc:
            if attempt == attempts:
                raise

            delay = min(8.0, 2.0 ** (attempt - 1))
            logger.warning(
                "Retrying OpenAI request after transient failure on attempt %s/%s: %s",
                attempt,
                attempts,
                exc,
            )
            time.sleep(delay)

    return ""
