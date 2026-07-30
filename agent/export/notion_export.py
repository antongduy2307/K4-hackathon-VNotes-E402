"""Push note_capture's filtered notes into a Notion database, one page per note.

Requires a Notion integration token with access to the target database, and
the database shared with that integration (Notion won't grant access
otherwise, even with a valid token). Expected database schema:

  Question  -> title
  Answer    -> rich_text
  Source    -> rich_text
  DocID     -> rich_text
"""
from __future__ import annotations

import os
from typing import Any

import requests

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
TIMEOUT = 30


def _format_source(note: dict[str, Any]) -> str:
    sources = note.get("sources") or []
    if not sources:
        return ""
    return ", ".join(
        f"tr.{s['page_start']}" if s["page_start"] == s["page_end"] else f"tr.{s['page_start']}-{s['page_end']}"
        for s in sources
    )


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _page_payload(database_id: str, note: dict[str, Any], doc_id: str) -> dict[str, Any]:
    question = str(note.get("question") or "")
    answer = str(note.get("answer") or "")
    return {
        "parent": {"database_id": database_id},
        "properties": {
            "Question": {"title": [{"text": {"content": question[:2000]}}]},
            "Answer": {"rich_text": [{"text": {"content": answer[:2000]}}]},
            "Source": {"rich_text": [{"text": {"content": _format_source(note)}}]},
            "DocID": {"rich_text": [{"text": {"content": doc_id}}]},
        },
    }


def push_notes_to_notion(
    notes: list[dict[str, Any]],
    *,
    doc_id: str,
    database_id: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    api_key = api_key or os.getenv("NOTION_API_KEY")
    database_id = database_id or os.getenv("NOTION_DATABASE_ID")

    if not api_key:
        return {"error": "missing_config", "message": "NOTION_API_KEY is not set."}
    if not database_id:
        return {"error": "missing_config", "message": "NOTION_DATABASE_ID is not set."}
    if not notes:
        return {"error": "no_notes", "message": "No notes to export."}

    created: list[dict[str, str]] = []
    failed: list[dict[str, Any]] = []

    for note in notes:
        payload = _page_payload(database_id, note, doc_id)
        try:
            response = requests.post(
                f"{NOTION_API_BASE}/pages",
                headers=_headers(api_key),
                json=payload,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
            created.append({"question": note.get("question"), "page_id": body.get("id"), "url": body.get("url")})
        except Exception as exc:
            failed.append({"question": note.get("question"), "error": type(exc).__name__, "message": str(exc)})

    return {
        "created_count": len(created),
        "failed_count": len(failed),
        "created": created,
        "failed": failed,
    }
