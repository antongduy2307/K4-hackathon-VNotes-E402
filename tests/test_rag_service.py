import asyncio
from types import SimpleNamespace

from app.models.domain import RetrievedChunk
from app.services.rag_service import RAGService


class FakeRepository:
    def get_owned(self, slide_id: str, user_id: str):
        return SimpleNamespace(status="ready")


class FakeEmbedder:
    def encode(self, texts: list[str]):
        return [[0.1, 0.2] for _ in texts]


class FakeChroma:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int | None]] = []
        self.search_calls: list[tuple[str, str, list[float], int]] = []

    def get_slide_chunks(self, *, user_id: str, slide_id: str, top_k: int | None):
        self.calls.append((user_id, slide_id, top_k))
        return [
            RetrievedChunk(
                chunk_id="c1",
                text="chunk 1",
                page_number=1,
                chunk_index=0,
                distance=0.0,
                score=1.0,
            )
        ]

    def search(
        self,
        *,
        user_id: str,
        slide_id: str,
        query_embedding: list[float],
        top_k: int,
    ):
        self.search_calls.append((user_id, slide_id, query_embedding, top_k))
        return [
            RetrievedChunk(
                chunk_id="c2",
                text="semantic chunk",
                page_number=2,
                chunk_index=1,
                distance=0.1,
                score=0.9,
            )
        ]


def test_retrieve_all_chunks_ignores_top_k_for_summary_flow() -> None:
    chroma = FakeChroma()
    service = RAGService(
        repository=FakeRepository(),
        embedder=FakeEmbedder(),
        chroma=chroma,
        default_top_k=5,
        max_top_k=10,
    )

    asyncio.run(service.retrieve_all_chunks(user_id="u1", slide_id="s1"))

    assert chroma.calls == [("u1", "s1", None)]


def test_retrieve_uses_semantic_search_when_question_is_provided() -> None:
    chroma = FakeChroma()
    service = RAGService(
        repository=FakeRepository(),
        embedder=FakeEmbedder(),
        chroma=chroma,
        default_top_k=5,
        max_top_k=10,
    )

    results = asyncio.run(
        service.retrieve(user_id="u1", slide_id="s1", question="prompt tốt", top_k=3)
    )

    assert len(results) == 1
    assert results[0].text == "semantic chunk"
    assert chroma.search_calls == [("u1", "s1", [0.1, 0.2], 3)]
