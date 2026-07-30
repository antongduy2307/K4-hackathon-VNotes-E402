import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.core.rag import ingest_pdf, summarize_document
from app.models.schemas import IngestResponse, SummaryResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=IngestResponse)
async def upload_document(file: UploadFile) -> IngestResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only .pdf is supported right now")

    doc_id = str(uuid.uuid4())
    os.makedirs(settings.upload_dir, exist_ok=True)
    dest_path = os.path.join(settings.upload_dir, f"{doc_id}.pdf")

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    chunks_stored = ingest_pdf(doc_id, dest_path)
    return IngestResponse(doc_id=doc_id, chunks_stored=chunks_stored)


@router.get("/{doc_id}/summary", response_model=SummaryResponse)
async def get_summary(doc_id: str) -> SummaryResponse:
    try:
        summary = summarize_document(doc_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return SummaryResponse(doc_id=doc_id, summary=summary)
