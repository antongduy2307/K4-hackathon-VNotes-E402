import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.exceptions import SlideNotFoundError, SlideNotReadyError
from app.models.domain import RetrievedChunk
from app.services.rag_service import RAGService


class FakeRepository:
    def __init__(self, *, status: str | None = "ready") -> None:
        self.status = status

    def get(self, slide_id: str):
        if self.status is None:
            return None
        return SimpleNamespace(status=self.status)


class FakeEmbedder:
    def encode(self, texts: list[str]):
        return [[0.1, 0.2] for _ in texts]


class FakeChroma:
    def __init__(self, *, chunks: list[RetrievedChunk] | None = None) -> None:
        self.calls: list[tuple[str, int | None]] = []
        self.search_calls: list[tuple[str, list[float], int]] = []
        # When explicitly set (including to []), both get_slide_chunks and search
        # return exactly this — so tests can simulate "no sources at all" regardless
        # of which retrieval path answer() takes.
        self._chunks = chunks

    def get_slide_chunks(self, *, slide_id: str, top_k: int | None):
        self.calls.append((slide_id, top_k))
        if self._chunks is not None:
            return self._chunks
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
        slide_id: str,
        query_embedding: list[float],
        top_k: int,
    ):
        self.search_calls.append((slide_id, query_embedding, top_k))
        if self._chunks is not None:
            return self._chunks
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


def make_service(*, repository=None, chroma=None, default_top_k=5, max_top_k=10) -> RAGService:
    return RAGService(
        repository=repository or FakeRepository(),
        embedder=FakeEmbedder(),
        chroma=chroma or FakeChroma(),
        default_top_k=default_top_k,
        max_top_k=max_top_k,
    )


def test_retrieve_all_chunks_ignores_top_k_for_summary_flow() -> None:
    chroma = FakeChroma()
    service = make_service(chroma=chroma)

    asyncio.run(service.retrieve_all_chunks(slide_id="s1"))

    assert chroma.calls == [("s1", None)]


def test_retrieve_uses_semantic_search_when_question_is_provided() -> None:
    chroma = FakeChroma()
    service = make_service(chroma=chroma)

    results = asyncio.run(
        service.retrieve(slide_id="s1", question="prompt tốt", top_k=3)
    )

    assert len(results) == 1
    assert results[0].text == "semantic chunk"
    assert chroma.search_calls == [("s1", [0.1, 0.2], 3)]


def test_retrieve_without_question_uses_get_slide_chunks() -> None:
    chroma = FakeChroma()
    service = make_service(chroma=chroma)

    asyncio.run(service.retrieve(slide_id="s1", question="", top_k=None))

    assert chroma.calls == [("s1", 5)]
    assert chroma.search_calls == []


def test_retrieve_clamps_top_k_to_max_top_k() -> None:
    chroma = FakeChroma()
    service = make_service(chroma=chroma, max_top_k=10)

    asyncio.run(service.retrieve(slide_id="s1", question="q", top_k=999))

    assert chroma.search_calls[0][2] == 10


def test_retrieve_raises_when_slide_not_found() -> None:
    service = make_service(repository=FakeRepository(status=None))

    with pytest.raises(SlideNotFoundError):
        asyncio.run(service.retrieve(slide_id="missing", question="q", top_k=None))


def test_retrieve_raises_when_slide_not_ready() -> None:
    service = make_service(repository=FakeRepository(status="processing"))

    with pytest.raises(SlideNotReadyError):
        asyncio.run(service.retrieve(slide_id="s1", question="q", top_k=None))


def test_retrieve_all_chunks_raises_when_slide_not_found() -> None:
    service = make_service(repository=FakeRepository(status=None))

    with pytest.raises(SlideNotFoundError):
        asyncio.run(service.retrieve_all_chunks(slide_id="missing"))


def test_answer_returns_placeholder_message_when_no_sources() -> None:
    service = make_service(chroma=FakeChroma(chunks=[]))

    answer, sources = asyncio.run(service.answer(slide_id="s1", question="q"))

    assert sources == []
    assert "chưa có nội dung" in answer


def test_answer_calls_agent_with_retrieved_sources_when_question_given() -> None:
    service = make_service()

    with patch.object(RAGService, "_answer_with_agent", return_value="câu trả lời") as mock_agent:
        answer, sources = asyncio.run(service.answer(slide_id="s1", question="Gradient descent là gì?"))

    assert answer == "câu trả lời"
    assert len(sources) == 1
    mock_agent.assert_called_once()
    call_args = mock_agent.call_args.args
    assert call_args[0] == "Gradient descent là gì?"
    assert call_args[2] == "s1"


def test_summarize_uses_all_chunks_and_default_question() -> None:
    chroma = FakeChroma()
    service = make_service(chroma=chroma)

    with patch.object(RAGService, "_answer_with_agent", return_value="tóm tắt") as mock_agent:
        answer, sources = asyncio.run(service.summarize(slide_id="s1"))

    assert answer == "tóm tắt"
    assert chroma.calls == [("s1", None)]
    assert chroma.search_calls == []
    default_question = mock_agent.call_args.args[0]
    assert "Tóm tắt" in default_question
