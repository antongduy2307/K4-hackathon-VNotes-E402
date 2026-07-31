from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.exceptions import SlideNotFoundError
from app.dependencies import (
    get_chroma_service,
    get_file_service,
    get_ingestion_service,
    get_slide_repository,
)
from app.models.domain import SlideRecord
from app.models.schemas import DeleteSlideResponse, SlideResponse, SlideUploadResponse
from app.repositories.slide_repository import SlideRepository
from app.services.chroma_service import ChromaService
from app.services.file_service import FileService
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/slides", tags=["slides"])


def _to_response(record: SlideRecord) -> SlideResponse:
    return SlideResponse(
        slide_id=record.slide_id,
        user_id=record.user_id,
        title=record.title,
        original_filename=record.original_filename,
        status=record.status,
        chunk_count=record.chunk_count,
        created_at=record.created_at,
        error_message=record.error_message,
    )


@router.post(
    "/upload",
    response_model=SlideUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_slide(
    file: Annotated[UploadFile, File(description="PDF hoặc PPTX")],
    user_id: Annotated[str, Form(min_length=1, max_length=100)],
    title: Annotated[str | None, Form(max_length=200)] = None,
    service: IngestionService = Depends(get_ingestion_service),
) -> SlideUploadResponse:
    record = await service.ingest(file=file, user_id=user_id, title=title)
    base = _to_response(record)
    return SlideUploadResponse(**base.model_dump(), message="Tạo RAG thành công")


@router.get("", response_model=list[SlideResponse])
def list_slides(
    user_id: str,
    repository: SlideRepository = Depends(get_slide_repository),
) -> list[SlideResponse]:
    return [_to_response(record) for record in repository.list_for_user(user_id)]


@router.get("/{slide_id}", response_model=SlideResponse)
def get_slide(
    slide_id: str,
    user_id: str,
    repository: SlideRepository = Depends(get_slide_repository),
) -> SlideResponse:
    record = repository.get_owned(slide_id, user_id)
    if record is None:
        raise SlideNotFoundError("Không tìm thấy slide")
    return _to_response(record)


@router.delete("/{slide_id}", response_model=DeleteSlideResponse)
def delete_slide(
    slide_id: str,
    user_id: str,
    repository: SlideRepository = Depends(get_slide_repository),
    chroma: ChromaService = Depends(get_chroma_service),
    file_service: FileService = Depends(get_file_service),
) -> DeleteSlideResponse:
    record = repository.get_owned(slide_id, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy slide")

    chroma.delete_slide(user_id, slide_id)
    deleted = repository.delete(slide_id, user_id)
    file_service.delete_slide_files(slide_id)
    return DeleteSlideResponse(slide_id=slide_id, deleted=deleted)
