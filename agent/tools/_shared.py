from __future__ import annotations

import os
import unicodedata
from typing import Any

import requests

TIMEOUT = 30


def fold_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def backend_base_url() -> str:
    return os.getenv("VLEARN_BACKEND_URL", "http://localhost:8000").rstrip("/")


def err(tool: str, exc: Exception) -> dict[str, Any]:
    return {"tool": tool, "error": type(exc).__name__, "message": str(exc)}


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{backend_base_url()}{path}", json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_json(path: str) -> dict[str, Any]:
    response = requests.get(f"{backend_base_url()}{path}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()
