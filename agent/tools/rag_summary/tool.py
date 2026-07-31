from __future__ import annotations

from typing import Any

from tools._shared import err, post_json


def rag_summary(user_id: str = "", slide_id: str = "") -> dict[str, Any]:
    try:
        if not user_id or not slide_id:
            return {
                "tool": "rag_summary",
                "error": "missing_argument",
                "message": "user_id and slide_id are required.",
            }
        result = post_json(
            "/api/v1/rag/query",
            {"user_id": user_id, "slide_id": slide_id, "question": "Tóm tắt nội dung slide này"},
        )
        return {
            "tool": "rag_summary",
            "user_id": user_id,
            "slide_id": slide_id,
            "summary": result.get("answer", ""),
        }
    except Exception as exc:
        return err("rag_summary", exc)
