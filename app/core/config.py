from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GitiNote RAG API"
    api_prefix: str = "/api/v1"

    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    chroma_dir: Path = Path("data/chroma")
    sqlite_path: Path = Path("data/slides.db")
    chroma_collection: str = "slide_chunks"

    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_device: str = "cpu"

    chunk_size: int = Field(default=900, ge=200)
    chunk_overlap: int = Field(default=150, ge=0)
    embedding_batch_size: int = Field(default=32, ge=1)
    default_top_k: int = Field(default=5, ge=1)
    max_top_k: int = Field(default=10, ge=1)
    max_file_size_mb: int = Field(default=30, ge=1)

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
