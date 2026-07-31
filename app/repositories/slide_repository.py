from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.models.domain import SlideRecord


class SlideRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS slides (
                    slide_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_slides_user_id ON slides(user_id)"
            )

    def create(
        self,
        *,
        slide_id: str,
        user_id: str,
        title: str,
        original_filename: str,
        stored_path: Path,
    ) -> SlideRecord:
        created_at = datetime.now(UTC)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO slides (
                    slide_id, user_id, title, original_filename, stored_path,
                    status, chunk_count, created_at, error_message
                ) VALUES (?, ?, ?, ?, ?, 'processing', 0, ?, NULL)
                """,
                (
                    slide_id,
                    user_id,
                    title,
                    original_filename,
                    str(stored_path),
                    created_at.isoformat(),
                ),
            )
        record = self.get(slide_id)
        assert record is not None
        return record

    def mark_ready(self, slide_id: str, chunk_count: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE slides
                SET status = 'ready', chunk_count = ?, error_message = NULL
                WHERE slide_id = ?
                """,
                (chunk_count, slide_id),
            )

    def mark_failed(self, slide_id: str, error_message: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE slides
                SET status = 'failed', error_message = ?
                WHERE slide_id = ?
                """,
                (error_message[:1000], slide_id),
            )

    def get(self, slide_id: str) -> SlideRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM slides WHERE slide_id = ?", (slide_id,)
            ).fetchone()
        return self._to_record(row) if row else None

    def get_owned(self, slide_id: str, user_id: str) -> SlideRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM slides
                WHERE slide_id = ? AND user_id = ?
                """,
                (slide_id, user_id),
            ).fetchone()
        return self._to_record(row) if row else None

    def list_for_user(self, user_id: str) -> list[SlideRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM slides
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._to_record(row) for row in rows]

    def delete(self, slide_id: str, user_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM slides WHERE slide_id = ? AND user_id = ?",
                (slide_id, user_id),
            )
        return cursor.rowcount > 0

    @staticmethod
    def _to_record(row: sqlite3.Row) -> SlideRecord:
        data = dict(row)
        data["stored_path"] = Path(data["stored_path"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return SlideRecord.model_validate(data)
