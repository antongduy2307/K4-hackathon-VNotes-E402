from __future__ import annotations

from typing import Any

from tools._shared import fold_text

BROAD_SCOPE_MARKERS = (
    "tom tat", "tong quan", "khai quat", "noi chung", "toan bo",
    "ca slide", "ca tai lieu", "ca bai giang", "overview", "summary", "summarize",
)


def _is_broad_scope(question: str) -> bool:
    folded = fold_text(question)
    return any(marker in folded for marker in BROAD_SCOPE_MARKERS)


def _classify(exchange: dict[str, Any]) -> tuple[bool, str | None]:
    """Returns (keep, exclude_reason)."""
    tool_used = exchange.get("tool_used")
    question = str(exchange.get("question") or "")

    if tool_used == "rag_summary":
        return False, "whole_document_summary"
    if tool_used != "rag_query":
        return False, "off_topic_or_unanswered"
    if not question.strip():
        return False, "empty_question"
    if _is_broad_scope(question):
        return False, "broad_scope_question"
    return True, None


def generate_note(doc_id: str = "", conversation_turns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    conversation_turns = conversation_turns or []

    notes: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for exchange in conversation_turns:
        keep, reason = _classify(exchange)
        if keep:
            notes.append({
                "question": exchange.get("question"),
                "answer": exchange.get("answer"),
                "sources": exchange.get("sources", []),
            })
        else:
            excluded.append({"question": exchange.get("question"), "reason": reason})

    return {
        "tool": "note_capture",
        "doc_id": doc_id,
        "notes": notes,
        "excluded": excluded,
        "kept_count": len(notes),
        "excluded_count": len(excluded),
    }
