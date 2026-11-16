"""MCP server exposing Mermaid-to-SVG conversion as tools for agents.

Run over stdio (default)::

    python -m mermaid2svg.mcp_server

or over HTTP::

    python -m mermaid2svg.mcp_server --transport streamable-http
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .core import MermaidRenderError, render_svg, save_svg

OUTPUT_DIR = Path(os.environ.get("MERMAID2SVG_OUTPUT_DIR", "output")).resolve()

mcp = MCPServer(
    "mermaid2svg",
    instructions="Convert Mermaid diagram source code into SVG images.",
)


@mcp.tool()
def mermaid_to_svg(mermaid_code: str) -> str:
    """Render Mermaid diagram source code and return the SVG markup as a string."""
    try:
        return render_svg(mermaid_code)
    except MermaidRenderError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def save_mermaid_svg(mermaid_code: str, filename: str = "diagram.svg") -> str:
    """Render Mermaid diagram source code and save it as an SVG file.

    The file is written inside the server's output directory
    (``MERMAID2SVG_OUTPUT_DIR``, default ``./output``). Returns the absolute path.
    """
    name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name).lstrip(".")
    if not name:
        name = "diagram.svg"
    if not name.lower().endswith(".svg"):
        name += ".svg"
    try:
        return str(save_svg(mermaid_code, OUTPUT_DIR / name))
    except MermaidRenderError as exc:
        raise ToolError(str(exc)) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="mermaid2svg MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transports.")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transports.")
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
