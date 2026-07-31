import pytest

from app.models.domain import PageText
from app.services.chunker_service import ChunkerService


def test_chunker_preserves_metadata_and_limits_size() -> None:
    service = ChunkerService(chunk_size=80, chunk_overlap=15)
    pages = [PageText(page_number=2, text=("Machine learning là một lĩnh vực. " * 12))]

    chunks = service.chunk_pages(
        pages=pages,
        slide_id="slide-1",
        source_filename="ml.pdf",
    )

    assert len(chunks) > 1
    assert all(chunk.slide_id == "slide-1" for chunk in chunks)
    assert all(chunk.page_number == 2 for chunk in chunks)
    assert all(len(chunk.text) <= 80 for chunk in chunks)


def test_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValueError):
        ChunkerService(chunk_size=50, chunk_overlap=50)


def test_empty_page_text_produces_no_chunks() -> None:
    service = ChunkerService(chunk_size=80, chunk_overlap=15)
    pages = [PageText(page_number=1, text="   ")]

    chunks = service.chunk_pages(pages=pages, slide_id="slide-1", source_filename="a.pdf")

    assert chunks == []


def test_chunk_ids_and_chunk_index_are_sequential_across_pages() -> None:
    service = ChunkerService(chunk_size=20, chunk_overlap=5)
    pages = [
        PageText(page_number=1, text="Đoạn văn đầu tiên khá dài để tạo nhiều mảnh nhỏ khác nhau."),
        PageText(page_number=2, text="Đoạn văn thứ hai cũng đủ dài để bị chia thành nhiều mảnh."),
    ]

    chunks = service.chunk_pages(pages=pages, slide_id="slide-9", source_filename="a.pdf")

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert [chunk.chunk_id for chunk in chunks] == [f"slide-9:{i}" for i in range(len(chunks))]
    # page_number tracks which page each chunk came from, in order
    page_numbers = [chunk.page_number for chunk in chunks]
    assert page_numbers == sorted(page_numbers)


def test_short_text_within_chunk_size_produces_single_chunk() -> None:
    service = ChunkerService(chunk_size=500, chunk_overlap=50)
    pages = [PageText(page_number=1, text="Câu ngắn.")]

    chunks = service.chunk_pages(pages=pages, slide_id="slide-1", source_filename="a.pdf")

    assert len(chunks) == 1
    assert chunks[0].text == "Câu ngắn."
