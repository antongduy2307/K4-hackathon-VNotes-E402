from __future__ import annotations

from typing import Any

from tools._shared import err, post_json


def rag_summary(doc_id: str = "") -> dict[str, Any]:
    try:
        if not doc_id:
            return {
                "tool": "rag_summary",
                "error": "missing_argument",
                "message": "doc_id is required.",
            }
        result = post_json("/api/v1/rag/summarize", {"slide_id": doc_id})
        return {
            "tool": "rag_summary",
            "doc_id": doc_id,
            "summary": result.get("answer", ""),
            "sources": result.get("sources", []),
        }
    except Exception as exc:
        return err("rag_summary", exc)
