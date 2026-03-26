"""Thin OpenAI API wrapper for OpenGraph AI engine calls.

TODO: Add Anthropic/Claude support via a provider flag.
TODO: Add batch mode for high-volume extraction workloads.
TODO: Add structured output mode (JSON schema / function calling).
"""

import os

import openai


# TODO: Make model name configurable via a config file or ENV.
_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TIMEOUT = 30.0


def call_llm(prompt: str) -> str:
    """Call the configured OpenAI model and return the response text.

    Reads OPENAI_API_KEY from the environment.  Raises EnvironmentError
    if the key is absent so callers get a clear failure message instead
    of an obscure API 401.

    TODO: Add retry logic with exponential back-off on rate-limit errors.
    TODO: Add Claude/Anthropic support — swap client based on PROVIDER env var.
    TODO: Add structured output via response_format={"type": "json_object"}.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set. "
            "Export it before running OpenGraph AI."
        )

    model = os.environ.get("OPENAI_MODEL", _DEFAULT_MODEL)

    client = openai.OpenAI(api_key=api_key, timeout=_DEFAULT_TIMEOUT)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content or ""
