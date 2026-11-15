"""Gradio web app: paste or upload Mermaid source, preview and download the SVG.

Run with::

    python -m mermaid2svg.gradio_app
"""

from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

import gradio as gr

from .core import MermaidRenderError, render_svg

EXAMPLE = """flowchart LR
    User --> FrontDoor[Azure Front Door]
    FrontDoor --> App[App Service]
    App --> SQL[(Azure SQL)]
    App --> Storage[(Blob Storage)]
"""


def _preview_html(svg: str) -> str:
    # Embed as an <img> data URI so any markup inside the SVG cannot execute in the page.
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        '<div style="background:#fff;padding:1em;border-radius:8px;overflow:auto">'
        f'<img alt="Rendered Mermaid diagram" style="max-width:100%" src="data:image/svg+xml;base64,{data}"/>'
        "</div>"
    )


def load_file(file_path: str | None) -> str:
    """Return the text content of an uploaded Mermaid file."""
    if not file_path:
        return ""
    return Path(file_path).read_text(encoding="utf-8")


def convert(mermaid_code: str) -> tuple[str, str | None, str]:
    """Render Mermaid source; returns (preview HTML, SVG file path, SVG text)."""
    try:
        svg = render_svg(mermaid_code)
    except MermaidRenderError as exc:
        raise gr.Error(str(exc)) from exc
    out_dir = Path(tempfile.mkdtemp(prefix="mermaid2svg_"))
    out_path = out_dir / "diagram.svg"
    out_path.write_text(svg, encoding="utf-8")
    return _preview_html(svg), str(out_path), svg


def build_app() -> gr.Blocks:
    with gr.Blocks(title="mermaid2svg") as demo:
        gr.Markdown("# mermaid2svg\nPaste or upload Mermaid source, then convert it to SVG.")
        with gr.Row():
            with gr.Column():
                code = gr.Code(value=EXAMPLE, label="Mermaid source", lines=15)
                upload = gr.File(
                    label="…or upload a Mermaid file",
                    file_types=[".mmd", ".mermaid", ".txt", ".md"],
                    type="filepath",
                )
                button = gr.Button("Convert to SVG", variant="primary")
            with gr.Column():
                preview = gr.HTML(label="Preview")
                download = gr.File(label="Download SVG")
                svg_text = gr.Code(label="SVG source", language="html", lines=10)

        upload.upload(load_file, inputs=upload, outputs=code)
        button.click(convert, inputs=code, outputs=[preview, download, svg_text])
    return demo


def main() -> None:
    build_app().launch(
        server_name=os.environ.get("HOST", "127.0.0.1"),
        server_port=int(os.environ.get("PORT", "7860")),
    )


if __name__ == "__main__":
    main()
