"""Tests for local environment configuration loading."""

import os
from pathlib import Path

import pytest

from engine.config import get_required_env, load_env_config
from engine.llm import provider


def test_load_env_config_reads_local_env_file(monkeypatch, tmp_path: Path) -> None:
    env_path = tmp_path / ".env.local"
    env_path.write_text(
        "# local development secrets\nOPENAI_API_KEY=file-test-key\nOPENAI_MODEL=gpt-test\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    loaded_files = load_env_config(search_from=tmp_path, force_reload=True)

    assert env_path.resolve() in loaded_files
    assert os.environ["OPENAI_API_KEY"] == "file-test-key"
    assert os.environ["OPENAI_MODEL"] == "gpt-test"


def test_load_env_config_override_behavior(monkeypatch, tmp_path: Path) -> None:
    env_path = tmp_path / ".env.local"
    env_path.write_text("OPENAI_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "already-set")

    load_env_config(search_from=tmp_path, force_reload=True)
    assert os.environ["OPENAI_API_KEY"] == "already-set"

    load_env_config(search_from=tmp_path, override=True, force_reload=True)
    assert os.environ["OPENAI_API_KEY"] == "from-file"


def test_get_required_env_raises_clear_error_when_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
        get_required_env("OPENAI_API_KEY", search_from=tmp_path, force_reload=True)


def test_provider_uses_local_env_file_automatically(monkeypatch, tmp_path: Path) -> None:
    env_path = tmp_path / ".env.local"
    env_path.write_text("OPENAI_API_KEY=file-loaded-key\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    captured: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs: object):
            captured["request"] = kwargs
            message = type("Message", (), {"content": '{"ok": true}'})()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    class FakeChat:
        def __init__(self) -> None:
            self.completions = FakeCompletions()

    class FakeClient:
        def __init__(self, *, api_key: str, timeout: float) -> None:
            captured["api_key"] = api_key
            captured["timeout"] = timeout
            self.chat = FakeChat()

    monkeypatch.setattr(provider.openai, "OpenAI", FakeClient)

    result = provider.call_llm("hello", max_retries=1, search_from=tmp_path)

    assert result == '{"ok": true}'
    assert captured["api_key"] == "file-loaded-key"
