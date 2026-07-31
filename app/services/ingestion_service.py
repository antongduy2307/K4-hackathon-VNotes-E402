from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from anyio import to_thread
from fastapi import UploadFile

from app.models.domain import SlideRecord
from app.repositories.slide_repository import SlideRepository
from app.services.chroma_service import ChromaService
from app.services.chunker_service import ChunkerService
from app.services.embedding_service import EmbeddingService
from app.services.extractor_service import ExtractorService
from app.services.file_service import FileService


class IngestionService:
    def __init__(
        self,
        *,
        repository: SlideRepository,
        file_service: FileService,
        extractor: ExtractorService,
        chunker: ChunkerService,
        embedder: EmbeddingService,
        chroma: ChromaService,
    ) -> None:
        self.repository = repository
        self.file_service = file_service
        self.extractor = extractor
        self.chunker = chunker
        self.embedder = embedder
        self.chroma = chroma

    async def ingest(
        self,
        *,
        file: UploadFile,
        user_id: str,
        title: str | None,
    ) -> SlideRecord:
        slide_id = str(uuid4())
        original_filename = Path(file.filename or "slide").name
        resolved_title = (title or Path(original_filename).stem).strip()
        stored_path = await self.file_service.save_upload(file, slide_id)

        self.repository.create(
            slide_id=slide_id,
            user_id=user_id,
            title=resolved_title,
            original_filename=original_filename,
            stored_path=stored_path,
        )

        try:
            chunk_count = await to_thread.run_sync(
                self._process_sync,
                slide_id,
                user_id,
                original_filename,
                stored_path,
            )
            self.repository.mark_ready(slide_id, chunk_count)
        except Exception as exc:
            self.repository.mark_failed(slide_id, str(exc))
            self.chroma.delete_slide(user_id, slide_id)
            raise

        record = self.repository.get_owned(slide_id, user_id)
        assert record is not None
        return record

    def _process_sync(
        self,
        slide_id: str,
        user_id: str,
        original_filename: str,
        stored_path: Path,
    ) -> int:
        pages = self.extractor.extract(stored_path)
        chunks = self.chunker.chunk_pages(
            pages=pages,
            slide_id=slide_id,
            user_id=user_id,
            source_filename=original_filename,
        )
        embeddings = self.embedder.encode([chunk.text for chunk in chunks])
        self.chroma.add_chunks(chunks, embeddings)
        return len(chunks)
