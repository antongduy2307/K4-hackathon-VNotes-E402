from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True, slots=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str
    slide_id: str
    user_id: str
    page_number: int
    chunk_index: int
    text: str
    source_filename: str


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    page_number: int
    chunk_index: int
    distance: float
    score: float


class SlideRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slide_id: str
    user_id: str
    title: str
    original_filename: str
    stored_path: Path
    status: str
    chunk_count: int
    created_at: datetime
    error_message: str | None = None
