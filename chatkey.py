"""Utility helpers for loading the GROQ API key from environment files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv may be missing in minimal installs
    load_dotenv = None  # type: ignore[assignment]


_DEFAULT_FILENAMES: tuple[str, ...] = (".env", ".env.local")
_ENV_KEY = "GROQ_API_KEY"


def _candidate_paths(base_dir: Path | None = None) -> Iterable[Path]:
    base = base_dir or Path(__file__).resolve().parent
    for name in _DEFAULT_FILENAMES:
        candidate = base / name
        if candidate.exists():
            yield candidate


def load_env(path: Path | str | None = None) -> None:
    """Load environment variables from a dotenv file if available."""

    if load_dotenv is None:
        return

    if path is not None:
        path_obj = Path(path)
        if path_obj.exists():
            load_dotenv(path_obj, override=False)
        return

    for candidate in _candidate_paths():
        load_dotenv(candidate, override=False)
        break


def get_groq_api_key(path: Path | str | None = None, *, required: bool = True) -> Optional[str]:
    """Return the GROQ API key, optionally loading it from a dotenv file."""

    load_env(path)
    api_key = os.getenv(_ENV_KEY)
    if required and not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to a .env file or export it before running."
        )
    return api_key


def prompt_for_key(prompt: str = "Enter GROQ API key (create one for free at https://console.groq.com/keys): ") -> str:
    try:
        return input(prompt).strip()
    except EOFError as exc:  # pragma: no cover - interactive only
        raise RuntimeError("No API key provided.") from exc


def save_key(key: str, path: Path | str | None = None) -> None:
    key = key.strip()
    if not key:
        raise ValueError("API key is empty.")

    target = Path(path) if path else Path(".env")
    lines: list[str] = []
    if target.exists():
        lines = target.read_text(encoding="utf-8").splitlines()
        filtered = [line for line in lines if not line.startswith(f"{_ENV_KEY}=")]
    else:
        filtered = []
    filtered.append(f"{_ENV_KEY}={key}")
    target.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def ensure_api_key(path: Path | str | None = None) -> str:
    try:
        key = get_groq_api_key(path, required=False)
    except RuntimeError:
        key = None
    if key:
        return key

    key = prompt_for_key()
    if not key:
        raise RuntimeError("GROQ API key is required.")
    save_key(key, path)
    os.environ[_ENV_KEY] = key
    return key


__all__ = [
    "load_env",
    "get_groq_api_key",
    "prompt_for_key",
    "save_key",
    "ensure_api_key",
]
