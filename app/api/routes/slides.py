from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.exceptions import SlideNotFoundError
from app.dependencies import (
    get_chroma_service,
    get_file_service,
    get_ingestion_service,
    get_slide_repository,
)
from app.models.domain import SlideRecord
from app.models.schemas import (
    DeleteSlideResponse,
    PageTextResponse,
    SlideResponse,
    SlideUploadResponse,
)
from app.repositories.slide_repository import SlideRepository
from app.services.chroma_service import ChromaService
from app.services.file_service import FileService
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/slides", tags=["slides"])

_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def _to_response(record: SlideRecord) -> SlideResponse:
    return SlideResponse(
        slide_id=record.slide_id,
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
    title: Annotated[str | None, Form(max_length=200)] = None,
    service: IngestionService = Depends(get_ingestion_service),
) -> SlideUploadResponse:
    record = await service.ingest(file=file, title=title)
    base = _to_response(record)
    return SlideUploadResponse(**base.model_dump(), message="Tạo RAG thành công")


@router.get("", response_model=list[SlideResponse])
def list_slides(
    repository: SlideRepository = Depends(get_slide_repository),
) -> list[SlideResponse]:
    return [_to_response(record) for record in repository.list_all()]


@router.get("/{slide_id}", response_model=SlideResponse)
def get_slide(
    slide_id: str,
    repository: SlideRepository = Depends(get_slide_repository),
) -> SlideResponse:
    record = repository.get(slide_id)
    if record is None:
        raise SlideNotFoundError("Không tìm thấy slide")
    return _to_response(record)


@router.get("/{slide_id}/file")
def get_slide_file(
    slide_id: str,
    repository: SlideRepository = Depends(get_slide_repository),
) -> FileResponse:
    record = repository.get(slide_id)
    if record is None:
        raise SlideNotFoundError("Không tìm thấy slide")
    if not record.stored_path.exists():
        raise SlideNotFoundError("Không tìm thấy file slide trên server")

    media_type = _MEDIA_TYPES.get(record.stored_path.suffix.lower(), "application/octet-stream")
    # FileResponse defaults Content-Disposition to "attachment" whenever filename
    # is set, which tells browsers to force-download instead of rendering inline
    # — wrong for a viewer endpoint. "inline" is what lets react-pdf/pdfjs (and a
    # plain browser tab navigating here directly) display it instead.
    return FileResponse(
        record.stored_path,
        media_type=media_type,
        filename=record.original_filename,
        content_disposition_type="inline",
    )


@router.get("/{slide_id}/pages/{page_number}", response_model=PageTextResponse)
def get_slide_page_text(
    slide_id: str,
    page_number: int,
    repository: SlideRepository = Depends(get_slide_repository),
    chroma: ChromaService = Depends(get_chroma_service),
) -> PageTextResponse:
    record = repository.get(slide_id)
    if record is None:
        raise SlideNotFoundError("Không tìm thấy slide")

    chunks = chroma.get_page_chunks(slide_id=slide_id, page_number=page_number)
    text = "\n\n".join(chunk.text for chunk in chunks)
    return PageTextResponse(slide_id=slide_id, page_number=page_number, text=text)


@router.delete("/{slide_id}", response_model=DeleteSlideResponse)
def delete_slide(
    slide_id: str,
    repository: SlideRepository = Depends(get_slide_repository),
    chroma: ChromaService = Depends(get_chroma_service),
    file_service: FileService = Depends(get_file_service),
) -> DeleteSlideResponse:
    record = repository.get(slide_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy slide")

    chroma.delete_slide(slide_id)
    deleted = repository.delete(slide_id)
    file_service.delete_slide_files(slide_id)
    return DeleteSlideResponse(slide_id=slide_id, deleted=deleted)
