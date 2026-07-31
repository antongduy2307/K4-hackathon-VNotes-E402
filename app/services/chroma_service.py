from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.models.domain import DocumentChunk, RetrievedChunk


class ChromaService:
    def __init__(self, persist_path: Path, collection_name: str) -> None:
        self.client = chromadb.PersistentClient(path=str(persist_path))
        self.collection: Collection = self.client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Số chunk và embedding không khớp")
        if not chunks:
            return

        self.collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "slide_id": chunk.slide_id,
                    "user_id": chunk.user_id,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "source_filename": chunk.source_filename,
                }
                for chunk in chunks
            ],
        )

    def search(
        self,
        *,
        user_id: str,
        slide_id: str,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"slide_id": {"$eq": slide_id}},
                ]
            },
            include=["documents", "metadatas", "distances"],
        )

        ids = self._first(results.get("ids"))
        documents = self._first(results.get("documents"))
        metadatas = self._first(results.get("metadatas"))
        distances = self._first(results.get("distances"))

        retrieved: list[RetrievedChunk] = []
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=False
        ):
            normalized_metadata = self._normalize_metadata(metadata)
            distance_value = float(distance)
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(chunk_id),
                    text=str(document),
                    page_number=int(normalized_metadata.get("page_number", 0)),
                    chunk_index=int(normalized_metadata.get("chunk_index", 0)),
                    distance=distance_value,
                    score=max(0.0, min(1.0, 1.0 - distance_value)),
                )
            )
        return retrieved

    def get_slide_chunks(
        self,
        *,
        user_id: str,
        slide_id: str,
        top_k: int | None,
    ) -> list[RetrievedChunk]:
        kwargs: dict[str, Any] = {
            "where": {
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"slide_id": {"$eq": slide_id}},
                ]
            },
            "include": ["documents", "metadatas"],
        }
        if top_k is not None:
            kwargs["limit"] = top_k

        results = self.collection.get(**kwargs)

        ids = self._first(results.get("ids"))
        documents = self._first(results.get("documents"))
        metadatas = self._first(results.get("metadatas"))

        retrieved: list[RetrievedChunk] = []
        for chunk_id, document, metadata in zip(ids, documents, metadatas, strict=False):
            normalized_metadata = self._normalize_metadata(metadata)
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(chunk_id),
                    text=str(document),
                    page_number=int(normalized_metadata.get("page_number", 0)),
                    chunk_index=int(normalized_metadata.get("chunk_index", 0)),
                    distance=0.0,
                    score=1.0,
                )
            )
        return retrieved

    def delete_slide(self, user_id: str, slide_id: str) -> None:
        self.collection.delete(
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"slide_id": {"$eq": slide_id}},
                ]
            }
        )

    @staticmethod
    def _first(value: Any) -> list[Any]:
        if not value:
            return []
        return value[0] or []

    @staticmethod
    def _normalize_metadata(metadata: Any) -> dict[str, Any]:
        if isinstance(metadata, dict):
            return metadata
        if metadata is None:
            return {}
        if hasattr(metadata, "get"):
            return dict(metadata)
        if isinstance(metadata, str):
            try:
                parsed = json.loads(metadata)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}
