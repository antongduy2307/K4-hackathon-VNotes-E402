"""Turn note_capture's filtered notes into a single downloadable Obsidian
note (.md). No API, no auth, no network call — Obsidian just reads files from
a folder (a "vault"), so exporting is nothing more than writing a well-formed
markdown file for the user to drop into theirs (or double-click to open if
Obsidian is already set to watch that folder).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from export.notion_export import consolidate_notes


def _format_source(note: dict[str, Any]) -> str:
    sources = note.get("sources") or []
    if not sources:
        return ""
    pages = ", ".join(
        f"tr.{s['page_start']}" if s["page_start"] == s["page_end"] else f"tr.{s['page_start']}-{s['page_end']}"
        for s in sources
    )
    return f" *(nguồn: {pages})*"


def build_obsidian_markdown(notes: list[dict[str, Any]], *, doc_id: str, openai_api_key: str | None = None) -> str:
    if not notes:
        raise ValueError("No notes to export.")

    now = datetime.now()
    key_points = consolidate_notes(notes, api_key=openai_api_key)

    frontmatter = "\n".join([
        "---",
        f'doc_id: "{doc_id}"',
        f'created: "{now.strftime("%Y-%m-%d %H:%M")}"',
        "tags: [vlearn, tutor-session]",
        "---",
    ])

    key_points_section = "\n".join(f"- {point}" for point in key_points)

    qa_lines = []
    for note in notes:
        question = str(note.get("question") or "")
        answer = str(note.get("answer") or "")
        qa_lines.append(f"### {question}\n\n{answer}{_format_source(note)}\n")
    qa_section = "\n".join(qa_lines)

    return (
        f"{frontmatter}\n\n"
        f"# VLearn Tutor — {doc_id}\n\n"
        f"## Ý chính\n\n{key_points_section}\n\n"
        f"## Chi tiết câu hỏi & trả lời\n\n{qa_section}"
    )


def export_obsidian_to_file(
    notes: list[dict[str, Any]],
    *,
    doc_id: str,
    out_path: Path,
    openai_api_key: str | None = None,
) -> Path:
    content = build_obsidian_markdown(notes, doc_id=doc_id, openai_api_key=openai_api_key)
    out_path.write_text(content, encoding="utf-8")
    return out_path
