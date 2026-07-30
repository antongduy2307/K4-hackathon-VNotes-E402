from pydantic import BaseModel


class IngestResponse(BaseModel):
    doc_id: str
    chunks_stored: int


class SummaryResponse(BaseModel):
    doc_id: str
    summary: str


class ChatRequest(BaseModel):
    doc_id: str
    question: str


class Source(BaseModel):
    page_start: int
    page_end: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
