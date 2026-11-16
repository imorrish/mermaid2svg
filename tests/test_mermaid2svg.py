import asyncio

import pytest
from fastapi.testclient import TestClient

from mermaid2svg import MermaidRenderError, render_svg, save_svg
from mermaid2svg import mcp_server
from mermaid2svg.api import app
from mermaid2svg.gradio_app import convert, load_file

VALID = "graph TD; A[Start] --> B[End]"
INVALID = "this is not mermaid"


def test_render_svg_returns_svg():
    svg = render_svg(VALID)
    assert svg.lstrip().startswith("<svg")
    assert "Start" in svg


@pytest.mark.parametrize("code", ["", "   ", INVALID])
def test_render_svg_rejects_bad_input(code):
    with pytest.raises(MermaidRenderError):
        render_svg(code)


def test_save_svg(tmp_path):
    out = save_svg(VALID, tmp_path / "sub" / "d.svg")
    assert out.read_text().lstrip().startswith("<svg")


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_api_render_json(client):
    r = client.post("/render", json={"code": VALID})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert r.text.lstrip().startswith("<svg")


def test_api_render_text(client):
    r = client.post("/render/text", content=VALID, headers={"Content-Type": "text/plain"})
    assert r.status_code == 200
    assert r.text.lstrip().startswith("<svg")


def test_api_render_file(client):
    r = client.post("/render/file", files={"file": ("d.mmd", VALID.encode(), "text/plain")})
    assert r.status_code == 200
    assert r.text.lstrip().startswith("<svg")


def test_api_render_invalid(client):
    r = client.post("/render", json={"code": INVALID})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_gradio_convert():
    code = load_file(VALID.encode())
    preview, path, svg = convert(code)
    assert "data:image/svg+xml;base64," in preview
    assert svg.lstrip().startswith("<svg")
    with open(path) as f:
        assert f.read() == svg


def test_gradio_convert_invalid():
    import gradio as gr

    with pytest.raises(gr.Error):
        convert(INVALID)


def test_mcp_tools_registered():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = {t.name for t in tools}
    assert {"mermaid_to_svg", "save_mermaid_svg"} <= names


def test_mcp_mermaid_to_svg():
    assert mcp_server.mermaid_to_svg(VALID).lstrip().startswith("<svg")


def test_mcp_save_sanitises_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "OUTPUT_DIR", tmp_path)
    path = mcp_server.save_mermaid_svg(VALID, "../../etc/evil")
    assert path == str(tmp_path / "evil.svg")
    assert (tmp_path / "evil.svg").exists()


def test_mcp_invalid_raises_tool_error():
    from mcp.server.mcpserver.exceptions import ToolError

    with pytest.raises(ToolError):
        mcp_server.mermaid_to_svg(INVALID)
