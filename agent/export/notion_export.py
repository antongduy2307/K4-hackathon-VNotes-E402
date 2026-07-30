"""Push note_capture's filtered notes into Notion as consolidated key points
appended to a single existing page — not a database.

Setup friction, deliberately minimized for non-technical users:
  1. Create an internal integration at notion.so/my-integrations, copy its token.
  2. Open ANY Notion page, click Share -> Connections -> add that integration.
  3. Copy that page's URL (or just its 32-char id) into NOTION_PAGE_ID.

No database, no column schema, no page properties to get right.

Content is consolidated into bullet-point key ideas via one LLM call (merging
near-duplicate questions instead of dumping raw Q&A rows), since that's what
was asked for. If OPENAI_API_KEY isn't available, falls back to one bullet
per note ("question — answer") so the export still works without it.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

import requests

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
TIMEOUT = 30

_CONSOLIDATE_SYSTEM_PROMPT = (
    "Bạn tổng hợp các câu hỏi-đáp của một buổi học thành các Ý CHÍNH ngắn gọn. "
    "Mỗi ý một dòng, bắt đầu bằng '- '. Gộp các câu hỏi cùng chủ đề lại với nhau "
    "thành một ý, không liệt kê lặp. Viết lại thành kiến thức cô đọng, không chép "
    "nguyên văn câu hỏi. Trả lời bằng tiếng Việt, không thêm lời dẫn."
)

_PAGE_ID_PATTERN = re.compile(r"([0-9a-fA-F]{32}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")


def extract_page_id(value: str) -> str:
    """Accepts a raw page id or a full Notion URL and returns the bare id."""
    match = _PAGE_ID_PATTERN.search(value)
    return match.group(1).replace("-", "") if match else value


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _fallback_bullets(notes: list[dict[str, Any]]) -> list[str]:
    bullets = []
    for note in notes:
        question = str(note.get("question") or "").strip()
        answer = str(note.get("answer") or "").strip()
        bullets.append(f"{question} — {answer}" if answer else question)
    return bullets


def consolidate_notes(notes: list[dict[str, Any]], *, api_key: str | None = None, model: str = "gpt-4o-mini") -> list[str]:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_bullets(notes)

    from openai import OpenAI

    qa_text = "\n\n".join(f"Q: {n.get('question', '')}\nA: {n.get('answer', '')}" for n in notes)
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": _CONSOLIDATE_SYSTEM_PROMPT},
                {"role": "user", "content": qa_text},
            ],
        )
        text = response.choices[0].message.content or ""
    except Exception:
        return _fallback_bullets(notes)

    bullets = [line.lstrip("-• ").strip() for line in text.splitlines() if line.strip().lstrip("-• ").strip()]
    return bullets or _fallback_bullets(notes)


def _bulleted_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _heading_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def push_notes_to_notion(
    notes: list[dict[str, Any]],
    *,
    doc_id: str,
    page_id: str | None = None,
    api_key: str | None = None,
    openai_api_key: str | None = None,
) -> dict[str, Any]:
    api_key = api_key or os.getenv("NOTION_API_KEY")
    page_id = page_id or os.getenv("NOTION_PAGE_ID")

    if not api_key:
        return {"error": "missing_config", "message": "NOTION_API_KEY is not set."}
    if not page_id:
        return {"error": "missing_config", "message": "NOTION_PAGE_ID is not set."}
    if not notes:
        return {"error": "no_notes", "message": "No notes to export."}

    page_id = extract_page_id(page_id)
    bullets = consolidate_notes(notes, api_key=openai_api_key)

    heading = f"VLearn Tutor — {doc_id} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    children = [_heading_block(heading), *[_bulleted_block(b) for b in bullets]]

    try:
        response = requests.patch(
            f"{NOTION_API_BASE}/blocks/{page_id}/children",
            headers=_headers(api_key),
            json={"children": children},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc)}

    return {
        "key_point_count": len(bullets),
        "key_points": bullets,
        "page_url": f"https://www.notion.so/{page_id}",
    }
