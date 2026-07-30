from __future__ import annotations

from typing import Any

from tools._shared import err, post_json


def rag_query(doc_id: str = "", query: str = "") -> dict[str, Any]:
    try:
        if not doc_id or not query:
            return {
                "tool": "rag_query",
                "error": "missing_argument",
                "message": "Both doc_id and query are required.",
            }
        result = post_json("/chat", {"doc_id": doc_id, "question": query})
        return {
            "tool": "rag_query",
            "doc_id": doc_id,
            "query": query,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
        }
    except Exception as exc:
        return err("rag_query", exc)
