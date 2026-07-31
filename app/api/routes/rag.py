from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_rag_service
from app.models.domain import RetrievedChunk
from app.models.schemas import (
    RAGQueryResponse,
    RetrieveRequest,
    RetrieveResponse,
    SourceChunk,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


def _source(chunk: RetrievedChunk) -> SourceChunk:
    return SourceChunk(
        chunk_id=chunk.chunk_id,
        page_number=chunk.page_number,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        score=round(chunk.score, 4),
    )


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_context(
    request: RetrieveRequest,
    service: RAGService = Depends(get_rag_service),
) -> RetrieveResponse:
    sources = await service.retrieve(
        slide_id=request.slide_id,
        question=request.question,
        top_k=request.top_k,
    )
    return RetrieveResponse(
        slide_id=request.slide_id,
        sources=[_source(item) for item in sources],
    )


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RetrieveRequest,
    service: RAGService = Depends(get_rag_service),
) -> RAGQueryResponse:
    answer, sources = await service.answer(
        slide_id=request.slide_id,
        question=request.question,
        top_k=request.top_k,
    )
    return RAGQueryResponse(
        slide_id=request.slide_id,
        answer=answer,
        sources=[_source(item) for item in sources],
    )

@router.post("/summarize", response_model=RAGQueryResponse)
async def summarize_slide(
    request: RetrieveRequest,
    service: RAGService = Depends(get_rag_service),
) -> RAGQueryResponse:
    answer, sources = await service.summarize(
        slide_id=request.slide_id,
    )
    return RAGQueryResponse(
        slide_id=request.slide_id,
        answer=answer,
        sources=[_source(item) for item in sources],
    )