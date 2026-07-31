from app.models.domain import PageText
from app.services.chunker_service import ChunkerService


def test_chunker_preserves_metadata_and_limits_size() -> None:
    service = ChunkerService(chunk_size=80, chunk_overlap=15)
    pages = [PageText(page_number=2, text=("Machine learning là một lĩnh vực. " * 12))]

    chunks = service.chunk_pages(
        pages=pages,
        slide_id="slide-1",
        user_id="user-1",
        source_filename="ml.pdf",
    )

    assert len(chunks) > 1
    assert all(chunk.slide_id == "slide-1" for chunk in chunks)
    assert all(chunk.user_id == "user-1" for chunk in chunks)
    assert all(chunk.page_number == 2 for chunk in chunks)
    assert all(len(chunk.text) <= 80 for chunk in chunks)
