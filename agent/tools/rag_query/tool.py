from __future__ import annotations

from typing import Any

from tools._shared import err, post_json


def rag_query(user_id: str = "", slide_id: str = "", query: str = "") -> dict[str, Any]:
    try:
        if not user_id or not slide_id or not query:
            return {
                "tool": "rag_query",
                "error": "missing_argument",
                "message": "user_id, slide_id, and query are required.",
            }
        result = post_json(
            "/api/v1/rag/query",
            {"user_id": user_id, "slide_id": slide_id, "question": query},
        )
        return {
            "tool": "rag_query",
            "user_id": user_id,
            "slide_id": slide_id,
            "query": query,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
        }
    except Exception as exc:
        return err("rag_query", exc)
