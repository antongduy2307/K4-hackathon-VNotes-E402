"""Turn note_capture's filtered notes into a single downloadable Obsidian
note (.md). No API, no auth, no network call — Obsidian just reads files from
a folder (a "vault"), so exporting is nothing more than writing a well-formed
markdown file for the user to drop into theirs.

Re-exporting the same document updates the same note in place instead of
producing a new one each time: only questions not already recorded in the
file get appended, and only that new batch gets consolidated into additional
key points — previously exported content is left untouched rather than
regenerated, so re-summarizing doesn't reword/duplicate earlier bullets.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from export.notion_export import consolidate_notes

_KEY_POINTS_HEADING = "## Ý chính"
_QA_HEADING = "## Chi tiết câu hỏi & trả lời"
_TITLE_FRONTMATTER_RE = re.compile(r'^title:\s*"(.*)"\s*$', re.MULTILINE)


def _format_source(note: dict[str, Any]) -> str:
    sources = note.get("sources") or []
    if not sources:
        return ""
    pages = ", ".join(
        f"tr.{s['page_start']}" if s["page_start"] == s["page_end"] else f"tr.{s['page_start']}-{s['page_end']}"
        for s in sources
    )
    return f" *(nguồn: {pages})*"


def _qa_block(note: dict[str, Any]) -> str:
    question = str(note.get("question") or "")
    answer = str(note.get("answer") or "")
    return f"### {question}\n\n{answer}{_format_source(note)}"


def parse_existing_note(content: str) -> dict[str, Any] | None:
    """Best-effort parse of our own fixed template. Returns None if the file
    doesn't look machine-generated (e.g. user rewrote it by hand) — callers
    should treat that as "start fresh" rather than risk mangling edits.
    """
    title_match = _TITLE_FRONTMATTER_RE.search(content)
    if not title_match or _KEY_POINTS_HEADING not in content or _QA_HEADING not in content:
        return None

    title = title_match.group(1)
    key_points_block = content.split(_KEY_POINTS_HEADING, 1)[1].split(_QA_HEADING, 1)[0]
    key_points = [line[2:].strip() for line in key_points_block.splitlines() if line.startswith("- ")]

    qa_block = content.split(_QA_HEADING, 1)[1]
    qa_entries: dict[str, str] = {}
    for chunk in re.split(r"(?:^|\n)### ", qa_block)[1:]:
        lines = chunk.strip("\n").split("\n", 1)
        question = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        qa_entries[question] = body

    return {"title": title, "key_points": key_points, "qa_entries": qa_entries}


def render_note(*, title: str, key_points: list[str], qa_bodies: dict[str, str]) -> str:
    frontmatter = "\n".join(["---", f'title: "{title}"', "tags: [vlearn, tutor-session]", "---"])
    key_points_section = "\n".join(f"- {point}" for point in key_points)
    qa_section = "\n\n".join(f"### {question}\n\n{body}" for question, body in qa_bodies.items())
    return (
        f"{frontmatter}\n\n"
        f"# {title}\n\n"
        f"{_KEY_POINTS_HEADING}\n\n{key_points_section}\n\n"
        f"{_QA_HEADING}\n\n{qa_section}"
    )


def build_obsidian_markdown(
    notes: list[dict[str, Any]],
    *,
    title: str,
    existing_content: str | None = None,
    openai_api_key: str | None = None,
) -> str:
    if not notes:
        raise ValueError("No notes to export.")

    existing = parse_existing_note(existing_content) if existing_content else None

    if existing:
        already_asked = set(existing["qa_entries"])
        new_notes = [n for n in notes if str(n.get("question") or "") not in already_asked]
        final_title = existing["title"]
        qa_bodies = dict(existing["qa_entries"])
        key_points = list(existing["key_points"])
    else:
        new_notes = notes
        final_title = title
        qa_bodies = {}
        key_points = []

    for note in new_notes:
        question = str(note.get("question") or "")
        answer = str(note.get("answer") or "")
        qa_bodies[question] = f"{answer}{_format_source(note)}"

    if new_notes:
        new_key_points = consolidate_notes(new_notes, api_key=openai_api_key)
        key_points.extend(p for p in new_key_points if p not in key_points)

    return render_note(title=final_title, key_points=key_points, qa_bodies=qa_bodies)


def export_obsidian_to_file(
    notes: list[dict[str, Any]],
    *,
    title: str,
    out_path: Path,
    openai_api_key: str | None = None,
) -> Path:
    existing_content = out_path.read_text(encoding="utf-8") if out_path.exists() else None
    content = build_obsidian_markdown(notes, title=title, existing_content=existing_content, openai_api_key=openai_api_key)
    out_path.write_text(content, encoding="utf-8")
    return out_path
