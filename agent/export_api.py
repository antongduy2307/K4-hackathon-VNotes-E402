"""Thin HTTP layer for the frontend's note-capture + export flow. Deliberately
NOT LLM-invoked for export itself — export is a deterministic action the user
clicks, not something worth routing through the agent's tool loop.

Flow: frontend accumulates real Q&A exchanges as the user chats (already has
them, since it renders the chat) -> POST /notes/capture to filter them with
the exact same logic note_capture uses inside the full agent loop (pure
function, no LLM call) -> POST the returned notes to /export/{anki,notion,
obsidian}.

Run:
    uvicorn export_api:app --reload --port 8100
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from env_loader import load_agent_env
from export.anki_export import export_anki_to_file
from export.notion_export import push_notes_to_notion
from export.obsidian_export import export_obsidian_to_file
from tools.note_capture.tool import generate_note

ROOT = Path(__file__).parent
load_agent_env(ROOT)

app = FastAPI(title="VLearn Note Export")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConversationTurn(BaseModel):
    question: str
    answer: str
    tool_used: str | None = None
    sources: list[dict[str, Any]] = []


class CaptureRequest(BaseModel):
    doc_id: str
    conversation_turns: list[ConversationTurn]


class Note(BaseModel):
    question: str
    answer: str
    sources: list[dict[str, Any]] = []


class ExportRequest(BaseModel):
    doc_id: str
    notes: list[Note]
    title: str | None = None  # human-readable document/slide name; falls back to doc_id if absent


@app.post("/notes/capture")
async def capture_notes(request: CaptureRequest) -> dict[str, Any]:
    turns = [t.model_dump() for t in request.conversation_turns]
    return generate_note(doc_id=request.doc_id, conversation_turns=turns)


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

    export_obsidian_to_file(notes, title=request.title or request.doc_id, out_path=out_path)
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
