from pathlib import Path

from app.repositories.slide_repository import SlideRepository


def test_repository_filters_by_owner(tmp_path: Path) -> None:
    repository = SlideRepository(tmp_path / "slides.db")
    repository.initialize()
    repository.create(
        slide_id="slide-1",
        user_id="khoa",
        title="AI",
        original_filename="ai.pdf",
        stored_path=tmp_path / "ai.pdf",
    )

    assert repository.get_owned("slide-1", "khoa") is not None
    assert repository.get_owned("slide-1", "an") is None
