from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError


class FileService:
    ALLOWED_EXTENSIONS = {".pdf", ".pptx"}

    def __init__(self, upload_dir: Path, max_file_size_mb: int) -> None:
        self.upload_dir = upload_dir
        self.max_bytes = max_file_size_mb * 1024 * 1024

    async def save_upload(self, file: UploadFile, slide_id: str) -> Path:
        original_name = Path(file.filename or "slide").name
        extension = Path(original_name).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError("Chỉ hỗ trợ file .pdf và .pptx")

        destination = self.upload_dir / f"{slide_id}{extension}"
        destination.parent.mkdir(parents=True, exist_ok=True)

        total_size = 0
        try:
            with destination.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)
                    if total_size > self.max_bytes:
                        raise FileTooLargeError("File vượt quá giới hạn dung lượng")
                    output.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

        return destination

    def delete_slide_files(self, slide_id: str) -> None:
        for file_path in self.upload_dir.glob(f"{slide_id}.*"):
            file_path.unlink(missing_ok=True)
