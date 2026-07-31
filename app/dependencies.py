from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.repositories.slide_repository import SlideRepository
from app.services.chroma_service import ChromaService
from app.services.chunker_service import ChunkerService
from app.services.embedding_service import EmbeddingService
from app.services.extractor_service import ExtractorService
from app.services.file_service import FileService
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService


@lru_cache
def get_slide_repository() -> SlideRepository:
    settings = get_settings()
    repository = SlideRepository(settings.sqlite_path)
    repository.initialize()
    return repository


@lru_cache
def get_file_service() -> FileService:
    settings = get_settings()
    return FileService(settings.upload_dir, settings.max_file_size_mb)


@lru_cache
def get_extractor_service() -> ExtractorService:
    return ExtractorService()


@lru_cache
def get_chunker_service() -> ChunkerService:
    settings = get_settings()
    return ChunkerService(settings.chunk_size, settings.chunk_overlap)


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        batch_size=settings.embedding_batch_size,
    )


@lru_cache
def get_chroma_service() -> ChromaService:
    settings = get_settings()
    return ChromaService(settings.chroma_dir, settings.chroma_collection)


@lru_cache
def get_ingestion_service() -> IngestionService:
    return IngestionService(
        repository=get_slide_repository(),
        file_service=get_file_service(),
        extractor=get_extractor_service(),
        chunker=get_chunker_service(),
        embedder=get_embedding_service(),
        chroma=get_chroma_service(),
    )


@lru_cache
def get_rag_service() -> RAGService:
    settings = get_settings()
    return RAGService(
        repository=get_slide_repository(),
        embedder=get_embedding_service(),
        chroma=get_chroma_service(),
        default_top_k=settings.default_top_k,
        max_top_k=settings.max_top_k,
    )
