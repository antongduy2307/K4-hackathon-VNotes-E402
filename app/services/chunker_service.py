from __future__ import annotations

import re

from app.models.domain import DocumentChunk, PageText


class ChunkerService:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap phải nhỏ hơn chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(
        self,
        *,
        pages: list[PageText],
        slide_id: str,
        source_filename: str,
    ) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        global_index = 0

        for page in pages:
            for piece in self._split_text(page.text):
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{slide_id}:{global_index}",
                        slide_id=slide_id,
                        page_number=page.page_number,
                        chunk_index=global_index,
                        text=piece,
                        source_filename=source_filename,
                    )
                )
                global_index += 1

        return chunks

    def _split_text(self, text: str) -> list[str]:
        text = re.sub(r"[ \t]+", " ", text).strip()
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            desired_end = min(start + self.chunk_size, text_length)
            end = self._find_boundary(text, start, desired_end)
            piece = text[start:end].strip()
            if piece:
                chunks.append(piece)
            if end >= text_length:
                break

            next_start = max(end - self.chunk_overlap, start + 1)
            while next_start < end and not text[next_start].isspace():
                next_start += 1
            start = next_start if next_start < end else end

        return chunks

    def _find_boundary(self, text: str, start: int, desired_end: int) -> int:
        if desired_end >= len(text):
            return len(text)

        search_start = start + int(self.chunk_size * 0.65)
        search_start = min(search_start, desired_end)
        window = text[search_start:desired_end]

        for separator in ("\n\n", "\n", ". ", "; ", ", ", " "):
            position = window.rfind(separator)
            if position != -1:
                return search_start + position + len(separator)
        return desired_end
