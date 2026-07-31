from pathlib import Path

from app.repositories.slide_repository import SlideRepository


def make_repository(tmp_path: Path) -> SlideRepository:
    repository = SlideRepository(tmp_path / "slides.db")
    repository.initialize()
    return repository


def test_repository_get_returns_created_record(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create(
        slide_id="slide-1",
        title="AI",
        original_filename="ai.pdf",
        stored_path=tmp_path / "ai.pdf",
    )

    assert repository.get("slide-1") is not None
    assert repository.get("unknown-slide") is None


def test_created_record_starts_in_processing_status_with_zero_chunks(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    record = repository.create(
        slide_id="slide-1",
        title="AI",
        original_filename="ai.pdf",
        stored_path=tmp_path / "ai.pdf",
    )

    assert record.status == "processing"
    assert record.chunk_count == 0
    assert record.error_message is None


def test_mark_ready_updates_status_and_chunk_count(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create(
        slide_id="slide-1",
        title="AI",
        original_filename="ai.pdf",
        stored_path=tmp_path / "ai.pdf",
    )

    repository.mark_ready("slide-1", chunk_count=42)
    record = repository.get("slide-1")

    assert record.status == "ready"
    assert record.chunk_count == 42
    assert record.error_message is None


def test_mark_failed_updates_status_and_error_message(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create(
        slide_id="slide-1",
        title="AI",
        original_filename="ai.pdf",
        stored_path=tmp_path / "ai.pdf",
    )

    repository.mark_failed("slide-1", "boom")
    record = repository.get("slide-1")

    assert record.status == "failed"
    assert record.error_message == "boom"


def test_list_all_returns_every_slide_newest_first(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create(
        slide_id="slide-1",
        title="First",
        original_filename="a.pdf",
        stored_path=tmp_path / "a.pdf",
    )
    repository.create(
        slide_id="slide-2",
        title="Second",
        original_filename="b.pdf",
        stored_path=tmp_path / "b.pdf",
    )

    records = repository.list_all()

    assert {record.slide_id for record in records} == {"slide-1", "slide-2"}
    assert len(records) == 2


def test_delete_removes_record_and_reports_whether_it_existed(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create(
        slide_id="slide-1",
        title="AI",
        original_filename="ai.pdf",
        stored_path=tmp_path / "ai.pdf",
    )

    assert repository.delete("slide-1") is True
    assert repository.get("slide-1") is None
    assert repository.delete("slide-1") is False
