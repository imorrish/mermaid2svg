# mermaid2svg
Convert mermaid markdown to svg as a web app, api and mcp server.

Handy for converting AI generated diagrams into SVG which can be inserted into FOR as an image.

Try it out on [Huggingface spaces](https://huggingface.co/spaces/imorrish/mermaid2svg)

Rendering is done in pure Python with [mermaidx](https://pypi.org/project/mermaidx/)
(no browser, Node.js or npm required):

```python
import mermaidx
d = mermaidx.render(mermaid_code)
d.save("azure_architecture.svg")
```

## Install

```bash
pip install -r requirements.txt      # or: pip install -e ".[all]"
```

## 1. FastAPI REST web service

```bash
uvicorn mermaid2svg.api:app --host 0.0.0.0 --port 8000   # or: mermaid2svg-api
```

Interactive docs at `http://localhost:8000/docs`. All render endpoints return `image/svg+xml`
(or HTTP 422 with a `detail` message for invalid Mermaid):

| Method | Path           | Body                                  |
|--------|----------------|---------------------------------------|
| GET    | `/health`      | –                                     |
| POST   | `/render`      | JSON `{"code": "graph TD; A-->B"}`    |
| POST   | `/render/text` | raw `text/plain` Mermaid source       |
| POST   | `/render/file` | multipart upload, field name `file`   |

```bash
curl -X POST localhost:8000/render -H 'Content-Type: application/json' \
     -d '{"code": "graph TD; A-->B"}' -o diagram.svg
curl -X POST localhost:8000/render/text --data-binary @diagram.mmd -H 'Content-Type: text/plain' -o diagram.svg
curl -X POST localhost:8000/render/file -F file=@diagram.mmd -o diagram.svg
```

## 2. Gradio web app

```bash
python -m mermaid2svg.gradio_app      # or: mermaid2svg-gradio
```

Open `http://localhost:7860`, paste Mermaid source (or upload a `.mmd`/`.mermaid`/`.txt`/`.md` file),
click **Convert to SVG** to preview the diagram and download the SVG.

## 3. MCP server

```bash
python -m mermaid2svg.mcp_server                                  # stdio (default)
python -m mermaid2svg.mcp_server --transport streamable-http --port 8000
```

Tools:

- `mermaid_to_svg(mermaid_code)` – returns the SVG markup as a string.
- `save_mermaid_svg(mermaid_code, filename="diagram.svg")` – writes the SVG to the output directory
  (`MERMAID2SVG_OUTPUT_DIR`, default `./output`) and returns its path. The filename is sanitised so
  files cannot be written outside that directory.

Example client configuration (e.g. Claude Desktop / VS Code):

```json
{
  "mcpServers": {
    "mermaid2svg": {
      "command": "python",
      "args": ["-m", "mermaid2svg.mcp_server"],
      "env": { "MERMAID2SVG_OUTPUT_DIR": "/path/to/output" }
    }
  }
}
```

## Configuration

| Variable                        | Default      | Description                              |
|---------------------------------|--------------|------------------------------------------|
| `HOST` / `PORT`                 | `127.0.0.1` / `8000` (API), `7860` (Gradio) | Bind address          |
| `MERMAID2SVG_MAX_SOURCE_LENGTH` | `100000`     | Maximum Mermaid source length (chars)    |
| `MERMAID2SVG_OUTPUT_DIR`        | `./output`   | Where the MCP `save_mermaid_svg` tool writes |

## Tests

```bash
pip install -e ".[test]"
pytest
```
