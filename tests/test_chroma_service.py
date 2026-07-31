from pathlib import Path

from app.models.domain import DocumentChunk
from app.services.chroma_service import ChromaService


def make_service(tmp_path: Path) -> ChromaService:
    return ChromaService(tmp_path / "chroma", "test_collection")


def make_chunk(slide_id: str, chunk_index: int, page_number: int, text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"{slide_id}:{chunk_index}",
        slide_id=slide_id,
        page_number=page_number,
        chunk_index=chunk_index,
        text=text,
        source_filename="a.pdf",
    )


def test_search_only_returns_chunks_for_the_requested_slide(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    chunks = [
        make_chunk("slide-1", 0, 1, "gradient descent la thuat toan toi uu"),
        make_chunk("slide-2", 0, 1, "hoan toan khac chu de, khong lien quan"),
    ]
    # embeddings don't need to be realistic for a metadata-filter test
    service.add_chunks(chunks, embeddings=[[1.0, 0.0], [0.0, 1.0]])

    results = service.search(slide_id="slide-1", query_embedding=[1.0, 0.0], top_k=5)

    assert len(results) == 1
    assert results[0].chunk_id == "slide-1:0"


def test_get_slide_chunks_returns_all_chunks_for_slide_without_query(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    chunks = [
        make_chunk("slide-1", 0, 1, "phan mot"),
        make_chunk("slide-1", 1, 2, "phan hai"),
        make_chunk("slide-2", 0, 1, "khac slide"),
    ]
    service.add_chunks(chunks, embeddings=[[0.1, 0.1], [0.2, 0.2], [0.3, 0.3]])

    results = service.get_slide_chunks(slide_id="slide-1", top_k=None)

    assert {r.chunk_id for r in results} == {"slide-1:0", "slide-1:1"}


def test_get_slide_chunks_respects_top_k_limit(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    chunks = [make_chunk("slide-1", i, 1, f"chunk {i}") for i in range(5)]
    service.add_chunks(chunks, embeddings=[[float(i), 0.0] for i in range(5)])

    results = service.get_slide_chunks(slide_id="slide-1", top_k=2)

    assert len(results) == 2


def test_delete_slide_removes_only_that_slides_chunks(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    chunks = [
        make_chunk("slide-1", 0, 1, "to delete"),
        make_chunk("slide-2", 0, 1, "keep me"),
    ]
    service.add_chunks(chunks, embeddings=[[0.1, 0.1], [0.2, 0.2]])

    service.delete_slide("slide-1")

    remaining = service.get_slide_chunks(slide_id="slide-1", top_k=None)
    other = service.get_slide_chunks(slide_id="slide-2", top_k=None)
    assert remaining == []
    assert len(other) == 1


def test_add_chunks_with_empty_list_is_a_noop(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    service.add_chunks([], embeddings=[])
    # no exception, nothing to retrieve
    assert service.get_slide_chunks(slide_id="anything", top_k=None) == []


def test_add_chunks_mismatched_lengths_raises(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    chunks = [make_chunk("slide-1", 0, 1, "x")]
    try:
        service.add_chunks(chunks, embeddings=[])
        assert False, "expected ValueError"
    except ValueError:
        pass
