from app.core.chunker import chunk_pages
from app.core.pdf_loader import PageText


def test_chunk_pages_respects_size_and_overlap():
    pages = [
        PageText(page_number=1, text="alpha " * 300),
        PageText(page_number=2, text="beta " * 300),
    ]
    chunks = chunk_pages("doc1", pages, chunk_size_tokens=100, overlap_tokens=20)

    assert len(chunks) > 1
    assert all(c.chunk_id.startswith("doc1::chunk_") for c in chunks)
    assert chunks[0].page_start == 1


def test_chunk_pages_tracks_page_span_across_boundary():
    pages = [
        PageText(page_number=1, text="alpha " * 50),
        PageText(page_number=2, text="beta " * 50),
    ]
    chunks = chunk_pages("doc1", pages, chunk_size_tokens=200, overlap_tokens=0)

    # a single big chunk should span both pages since total tokens < chunk_size
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2


def test_chunk_pages_skips_empty_pages():
    pages = [
        PageText(page_number=1, text=""),
        PageText(page_number=2, text="content here"),
    ]
    chunks = chunk_pages("doc1", pages, chunk_size_tokens=100, overlap_tokens=10)

    assert len(chunks) == 1
    assert chunks[0].page_start == 2
