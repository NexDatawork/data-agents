"""Thin OpenAI API wrapper for OpenGraph AI engine calls.

TODO: Add Anthropic/Claude support via a provider flag.
TODO: Add batch mode for high-volume extraction workloads.
"""

import os
from typing import Any

import openai


# TODO: Make model name configurable via a config file or ENV.
_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TIMEOUT = 60.0


def _make_client() -> openai.OpenAI:
    """Create an authenticated OpenAI client from environment variables."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set. "
            "Export it before running OpenGraph AI."
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
