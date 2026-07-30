"""Thin HTTP layer for the three export buttons in the UI ("Lưu vào Anki" /
"Lưu vào Notion" / "Lưu vào Obsidian"). Deliberately NOT LLM-invoked — export
is a deterministic action the user clicks, not something worth routing
through the agent's tool loop. The UI is expected to call note_capture (via
the agent) first to get the filtered notes, then POST that same list here.

Run:
    uvicorn export_api:app --reload --port 8100
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from env_loader import load_agent_env
from export.anki_export import export_anki_to_file
from export.notion_export import push_notes_to_notion
from export.obsidian_export import export_obsidian_to_file

ROOT = Path(__file__).parent
load_agent_env(ROOT)

app = FastAPI(title="VLearn Note Export")


class Note(BaseModel):
    question: str
    answer: str
    sources: list[dict[str, int]] = []


class ExportRequest(BaseModel):
    doc_id: str
    notes: list[Note]


@app.post("/export/anki")
async def export_anki(request: ExportRequest) -> FileResponse:
    notes = [note.model_dump() for note in request.notes]
    if not notes:
        raise HTTPException(400, "No notes to export.")

    out_dir = Path(tempfile.gettempdir()) / "vlearn_exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{request.doc_id}.apkg"

    export_anki_to_file(notes, doc_id=request.doc_id, out_path=out_path)
    return FileResponse(
        out_path,
        media_type="application/octet-stream",
        filename=f"vlearn_{request.doc_id}.apkg",
    )


@app.post("/export/obsidian")
async def export_obsidian(request: ExportRequest) -> FileResponse:
    notes = [note.model_dump() for note in request.notes]
    if not notes:
        raise HTTPException(400, "No notes to export.")

    out_dir = Path(tempfile.gettempdir()) / "vlearn_exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{request.doc_id}.md"

    export_obsidian_to_file(notes, doc_id=request.doc_id, out_path=out_path)
    return FileResponse(
        out_path,
        media_type="text/markdown",
        filename=f"vlearn_{request.doc_id}.md",
    )


@app.post("/export/notion")
async def export_notion(request: ExportRequest) -> dict[str, Any]:
    notes = [note.model_dump() for note in request.notes]
    result = push_notes_to_notion(notes, doc_id=request.doc_id)
    if result.get("error"):
        raise HTTPException(400, result["message"])
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
