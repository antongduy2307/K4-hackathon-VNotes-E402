import asyncio
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile

from app.services.file_service import FileService


def test_save_upload_stores_file_in_single_directory(tmp_path: Path) -> None:
    service = FileService(tmp_path, 30)
    upload = UploadFile(filename="sample.pdf", file=BytesIO(b"hello slide"))

    stored_path = asyncio.run(service.save_upload(upload, "slide-123"))

    assert stored_path == tmp_path / "slide-123.pdf"
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"hello slide"
    assert not (tmp_path / "slide-123").exists()
