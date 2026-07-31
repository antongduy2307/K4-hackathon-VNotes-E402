from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SlideResponse(BaseModel):
    slide_id: str
    user_id: str
    title: str
    original_filename: str
    status: str
    chunk_count: int
    created_at: datetime
    error_message: str | None = None


class SlideUploadResponse(SlideResponse):
    message: str


class RetrieveRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    slide_id: str = Field(min_length=1, max_length=100)
    question: str = Field(default="", min_length=0, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=50)


class SourceChunk(BaseModel):
    chunk_id: str
    page_number: int
    chunk_index: int
    text: str
    score: float


class RetrieveResponse(BaseModel):
    slide_id: str
    sources: list[SourceChunk]


class RAGQueryResponse(RetrieveResponse):
    answer: str


class DeleteSlideResponse(BaseModel):
    slide_id: str
    deleted: bool
