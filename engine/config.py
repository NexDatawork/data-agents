"""Configuration helpers for OpenGraph AI.

Loads local environment files without requiring external dependencies so the CLI
and internal modules can discover secrets such as `OPENAI_API_KEY`
automatically during development.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

_DEFAULT_ENV_FILES = (".env", ".env.local")
_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _normalize_base_path(search_from: str | Path | None) -> Path:
    """Return a resolved directory path to search for local env files."""
    base = Path(search_from).expanduser() if search_from is not None else Path.cwd()
    if base.exists() and base.is_file():
        return base.resolve().parent
    return base.resolve() if base.exists() else base.absolute()


def _candidate_env_files(
    search_from: str | Path | None,
    env_files: Iterable[str],
) -> list[Path]:
    """Return ordered candidate env files from project root down to the target path."""
    seen: set[Path] = set()
    candidates: list[Path] = []

    for seed in (_PROJECT_ROOT, Path.cwd(), _normalize_base_path(search_from)):
        ordered_dirs = [*reversed(seed.parents), seed]
        for directory in ordered_dirs:
            for env_name in env_files:
                candidate = (directory / env_name).resolve()
                if candidate in seen or not candidate.is_file():
                    continue
                seen.add(candidate)
                candidates.append(candidate)

    return candidates


def _parse_env_line(line: str) -> tuple[str, str] | None:
    """Parse a single KEY=VALUE env file line."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if stripped.startswith("export "):
        stripped = stripped.removeprefix("export ").strip()

    if "=" not in stripped:
        return None

    key, value = stripped.split("=", maxsplit=1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None

    if value and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    else:
        value = value.split(" #", maxsplit=1)[0].rstrip()

    return key, value.replace("\\n", "\n")


def load_env_config(
    search_from: str | Path | None = None,
    *,
    env_files: Iterable[str] = _DEFAULT_ENV_FILES,
    override: bool = False,
    force_reload: bool = False,
) -> list[Path]:
    """Load local `.env` files into `os.environ`.

    Precedence order is:
    1. already-exported shell environment variables
    2. nearest `.env.local`
    3. nearest `.env`
    4. parent-directory env files toward the project root

    The `force_reload` flag is accepted for test friendliness and future caching,
    but loading currently remains explicit and deterministic on every call.
    """
    del force_reload  # Intentional: kept for a stable public interface.

    merged_values: dict[str, str] = {}
    loaded_files = _candidate_env_files(search_from, env_files)

    for env_path in loaded_files:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(raw_line)
            if parsed is None:
                continue
            key, value = parsed
            merged_values[key] = value

    for key, value in merged_values.items():
        if override or not os.environ.get(key):
            os.environ[key] = value

    return loaded_files


def get_optional_env(
    name: str,
    default: str | None = None,
    *,
    search_from: str | Path | None = None,
    env_files: Iterable[str] = _DEFAULT_ENV_FILES,
    force_reload: bool = False,
) -> str | None:
    """Return an environment variable after auto-loading local env files."""
    load_env_config(
        search_from=search_from,
        env_files=env_files,
        force_reload=force_reload,
    )
    return os.environ.get(name, default)


def get_required_env(
    name: str,
    *,
    search_from: str | Path | None = None,
    env_files: Iterable[str] = _DEFAULT_ENV_FILES,
    force_reload: bool = False,
) -> str:
    """Return a required environment variable or raise a clear configuration error."""
    value = get_optional_env(
        name,
        search_from=search_from,
        env_files=env_files,
        force_reload=force_reload,
    )
    if value:
        return value

    raise EnvironmentError(
        f"{name} is not set. Create a local `.env.local` (preferred) or `.env` file "
        f"from `.env.example`, or set {name} in your shell before running OpenGraph AI."
    )
