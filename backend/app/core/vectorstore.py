"""Chroma-backed vector store for document chunks."""
import chromadb

from app.config import settings
from app.core.chunker import Chunk
from app.core.embeddings import embed_query, embed_texts

_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
_collection = _client.get_or_create_collection(name="vlearn_chunks")


def add_chunks(doc_id: str, chunks: list[Chunk]) -> None:
    if not chunks:
        return
    embeddings = embed_texts([c.text for c in chunks])
    _collection.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[
            {"doc_id": doc_id, "page_start": c.page_start, "page_end": c.page_end}
            for c in chunks
        ],
    )


def query(doc_id: str, question: str, top_k: int = 5) -> list[dict]:
    query_embedding = embed_query(question)
    result = _collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"doc_id": doc_id},
    )
    hits = []
    for text, meta, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({"text": text, "metadata": meta, "distance": distance})
    return hits


def get_all_chunks(doc_id: str) -> list[dict]:
    """Fetch every chunk for a document, ordered by page — used for full-document summarization."""
    result = _collection.get(where={"doc_id": doc_id})
    items = list(zip(result["documents"], result["metadatas"]))
    items.sort(key=lambda pair: pair[1]["page_start"])
    return [{"text": text, "metadata": meta} for text, meta in items]


def delete_document(doc_id: str) -> None:
    _collection.delete(where={"doc_id": doc_id})
