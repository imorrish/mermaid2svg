"""Shared rendering logic used by the REST API, Gradio app and MCP server."""

from __future__ import annotations

import os
import threading
from pathlib import Path

import mermaidx

MAX_SOURCE_LENGTH = int(os.environ.get("MERMAID2SVG_MAX_SOURCE_LENGTH", "100000"))

# The embedded JS engine is not guaranteed to be thread-safe, so serialise renders.
_render_lock = threading.Lock()


class MermaidRenderError(ValueError):
    """Raised when Mermaid source is invalid or cannot be rendered."""


def render_svg(mermaid_code: str) -> str:
    """Render Mermaid source code to an SVG string."""
    if not isinstance(mermaid_code, str) or not mermaid_code.strip():
        raise MermaidRenderError("Mermaid source must be a non-empty string.")
    if len(mermaid_code) > MAX_SOURCE_LENGTH:
        raise MermaidRenderError(
            f"Mermaid source exceeds the maximum length of {MAX_SOURCE_LENGTH} characters."
        )
    try:
        with _render_lock:
            return mermaidx.render(mermaid_code).svg()
    except Exception as exc:  # mermaidx raises RuntimeError on syntax errors
        raise MermaidRenderError(str(exc)) from exc


def save_svg(mermaid_code: str, path: str | os.PathLike) -> Path:
    """Render Mermaid source code and write the SVG to ``path``."""
    svg = render_svg(mermaid_code)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    return out
