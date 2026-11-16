"""FastAPI REST web service for converting Mermaid source to SVG.

Run with::

    uvicorn mermaid2svg.api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .core import MAX_SOURCE_LENGTH, MermaidRenderError, render_svg

SVG_MEDIA_TYPE = "image/svg+xml"

app = FastAPI(
    title="mermaid2svg",
    description="Convert Mermaid diagram source to SVG using mermaidx.",
    version="0.1.0",
)


class RenderRequest(BaseModel):
    code: str = Field(..., description="Mermaid diagram source code.", max_length=MAX_SOURCE_LENGTH)


async def _svg_response(code: str, filename: str = "diagram.svg") -> Response:
    try:
        svg = await run_in_threadpool(render_svg, code)
    except MermaidRenderError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=svg,
        media_type=SVG_MEDIA_TYPE,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/render", response_class=Response, responses={200: {"content": {SVG_MEDIA_TYPE: {}}}})
async def render_json(body: RenderRequest) -> Response:
    """Render Mermaid source supplied as JSON (``{"code": "..."}``)."""
    return await _svg_response(body.code)


@app.post(
    "/render/text",
    response_class=Response,
    responses={200: {"content": {SVG_MEDIA_TYPE: {}}}},
    openapi_extra={"requestBody": {"content": {"text/plain": {"schema": {"type": "string"}}}, "required": True}},
)
async def render_text(request: Request) -> Response:
    """Render Mermaid source supplied as a raw ``text/plain`` request body."""
    raw = await request.body()
    if len(raw) > MAX_SOURCE_LENGTH * 4:
        raise HTTPException(status_code=413, detail="Request body too large.")
    try:
        code = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Body must be UTF-8 text.") from exc
    return await _svg_response(code)


@app.post("/render/file", response_class=Response, responses={200: {"content": {SVG_MEDIA_TYPE: {}}}})
async def render_file(file: UploadFile) -> Response:
    """Render an uploaded Mermaid file (e.g. ``diagram.mmd``)."""
    raw = await file.read(MAX_SOURCE_LENGTH * 4 + 1)
    if len(raw) > MAX_SOURCE_LENGTH * 4:
        raise HTTPException(status_code=413, detail="Uploaded file too large.")
    try:
        code = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc
    return await _svg_response(code)


def main() -> None:
    import os

    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
