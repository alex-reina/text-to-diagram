"""Helpers for extracting PlantUML code and rendering diagrams."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence
from uuid import uuid4

import requests
from requests import RequestException

try:  # pragma: no cover - optional dependency
    from plantuml import PlantUML
except ImportError:  # pragma: no cover - optional dependency
    PlantUML = None  # type: ignore[misc,assignment]


class PlantUMLRenderingError(RuntimeError):
    """Raised when PlantUML rendering fails."""


@dataclass
class PlantUMLDiagram:
    """Represents a rendered PlantUML diagram."""

    code: str
    data: bytes
    format: str = "png"
    image_url: str | None = None
    editor_url: str | None = None


_PLANTUML_PATTERN = re.compile(r"(?is)(@startuml.*?@enduml)")
_DEFAULT_PNG_ENDPOINT = "https://www.plantuml.com/plantuml/png/"
_DEFAULT_SVG_ENDPOINT = "https://www.plantuml.com/plantuml/svg/"


def extract_plantuml_blocks(text: str) -> List[str]:
    """Return PlantUML snippets found within the text."""

    # The pattern captures each bounded @startuml…@enduml block including newlines.
    return [match.group(1).strip() for match in _PLANTUML_PATTERN.finditer(text)]


def _resolve_endpoint(fmt: str) -> str:
    fmt = fmt.lower()
    custom = os.getenv("PLANTUML_SERVER_URL")
    if custom:
        return custom if custom.endswith("/") else custom + "/"
    if fmt == "svg":
        return _DEFAULT_SVG_ENDPOINT
    return _DEFAULT_PNG_ENDPOINT


def _create_client(fmt: str) -> PlantUML:
    if PlantUML is None:  # pragma: no cover - optional dependency
        raise ImportError(
            "The 'plantuml' package is required to render diagrams. Install it via pip."
        )
    # LangChain's PlantUML client speaks HTTP; we only swap the base URL by format.
    endpoint = _resolve_endpoint(fmt)
    return PlantUML(url=endpoint)


def render_plantuml(code: str, fmt: str = "png") -> PlantUMLDiagram:
    """Render a single PlantUML snippet and return the diagram result."""

    client = _create_client(fmt)
    image_url, editor_url = _build_diagram_urls(client, fmt, code)
    if not image_url:
        raise PlantUMLRenderingError("Could not create PlantUML image URL.")

    data = _download_diagram(image_url)
    return PlantUMLDiagram(
        code=code,
        data=data,
        format=fmt,
        image_url=image_url,
        editor_url=editor_url,
    )


def _build_diagram_urls(client: PlantUML, fmt: str, code: str) -> tuple[str | None, str | None]:
    try:
        image_url = client.get_url(code)
    except AttributeError:  # pragma: no cover - fallback when method missing
        image_url = None
    except Exception:  # pragma: no cover - defensive
        image_url = None

    editor_url: str | None = None
    if image_url:
        try:
            from urllib.parse import urlparse, urlunparse

            # PlantUML encodes the same diagram in different paths for image/editor views.
            parsed = urlparse(image_url)
            path = parsed.path
            if "/png/" in path:
                editor_path = path.replace("/png/", "/uml/", 1)
            elif "/svg/" in path:
                editor_path = path.replace("/svg/", "/uml/", 1)
            else:
                editor_path = path
            editor_url = urlunparse(parsed._replace(path=editor_path))
        except Exception:  # pragma: no cover - best-effort
            editor_url = None

    return image_url, editor_url


def _download_diagram(url: str) -> bytes:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except RequestException as exc:  # pragma: no cover - network errors
        raise PlantUMLRenderingError(f"Failed to download diagram: {exc}") from exc
    return response.content


def render_plantuml_from_text(text: str, fmt: str = "png") -> List[PlantUMLDiagram]:
    """Extract PlantUML snippets from text and render them."""

    blocks = extract_plantuml_blocks(text)
    diagrams: List[PlantUMLDiagram] = []
    for block in blocks:
        try:
            diagrams.append(render_plantuml(block, fmt=fmt))
        except PlantUMLRenderingError:
            raise
        # Allow other exceptions (e.g., network) to bubble so callers can decide whether to continue.
    return diagrams


def save_diagrams(diagrams: Iterable[PlantUMLDiagram], directory: Path) -> List[Path]:
    """Persist rendered diagrams to disk and return the file paths."""

    saved_paths: List[Path] = []
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for index, diagram in enumerate(diagrams, start=1):
        filename = f"diagram_{timestamp}_{uuid4().hex[:8]}_{index}.{diagram.format}"
        path = directory / filename
        path.write_bytes(diagram.data)
        saved_paths.append(path)
    # Return order matches the input iterator so callers can zip results deterministically.
    return saved_paths


__all__ = [
    "PlantUMLDiagram",
    "PlantUMLRenderingError",
    "extract_plantuml_blocks",
    "render_plantuml",
    "render_plantuml_from_text",
    "save_diagrams",
]
