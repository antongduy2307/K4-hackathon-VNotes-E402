from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .clarify.tool import ask_user
from .note_capture.tool import generate_note
from .rag_query.tool import rag_query
from .rag_summary.tool import rag_summary

# These keys are the names the model sees AND the names data/eval_base.json
# matches against. If a tool is renamed, keep it in sync across ALL of:
#   artifacts/tools.yaml  ->  this dict  ->  data/eval_base.json
TOOL_FUNCTIONS = {
    "rag_query": rag_query,
    "rag_summary": rag_summary,
    "clarify": ask_user,
    "note_capture": generate_note,
}

# Fields these tools need that must come from the session, never from the
# model's own tool-call args: doc_id is fixed for the whole session (one
# document per session — it never changes mid-conversation, so the model
# must not be trusted to parse/carry/guess it from message text), and
# conversation_turns must be the real recorded session log, not something
# the model retypes from memory.
SESSION_INJECTED_ARGS: dict[str, list[str]] = {
    "rag_query": ["doc_id"],
    "rag_summary": ["doc_id"],
    "note_capture": ["doc_id", "conversation_turns"],
}


def apply_session_args(tool_name: str, args: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    keys = SESSION_INJECTED_ARGS.get(tool_name, [])
    return {**args, **{key: session[key] for key in keys if key in session}}


def load_tool_declarations(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["tools"]


def to_openai_tools(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": item["name"],
            "description": item.get("description", ""),
            "parameters": item.get("parameters", {"type": "object", "properties": {}}),
        },
    } for item in declarations]
