from __future__ import annotations

from typing import Any

from tools._shared import err, get_json


def rag_summary(doc_id: str = "") -> dict[str, Any]:
    try:
        if not doc_id:
            return {
                "tool": "rag_summary",
                "error": "missing_argument",
                "message": "doc_id is required.",
            }
        result = get_json(f"/documents/{doc_id}/summary")
        return {
            "tool": "rag_summary",
            "doc_id": doc_id,
            "summary": result.get("summary", ""),
        }
    except Exception as exc:
        return err("rag_summary", exc)
