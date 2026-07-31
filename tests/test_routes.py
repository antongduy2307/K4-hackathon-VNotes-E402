from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.routes import rag as rag_routes
from app.api.routes import slides as slides_routes
from app.core.exceptions import AppError
from app.dependencies import (
    get_chroma_service,
    get_file_service,
    get_ingestion_service,
    get_rag_service,
    get_slide_repository,
)
from app.models.domain import RetrievedChunk, SlideRecord


def make_record(
    slide_id: str = "s1",
    *,
    status: str = "ready",
    stored_path: Path = Path("data/uploads/ai.pdf"),
    original_filename: str = "ai.pdf",
) -> SlideRecord:
    return SlideRecord(
        slide_id=slide_id,
        title="AI slide",
        original_filename=original_filename,
        stored_path=stored_path,
        status=status,
        chunk_count=3,
        created_at=datetime.now(UTC),
        error_message=None,
    )


class FakeRepository:
    def __init__(self, records: dict[str, SlideRecord] | None = None) -> None:
        self.records = records or {}

    def get(self, slide_id: str) -> SlideRecord | None:
        return self.records.get(slide_id)

    def list_all(self) -> list[SlideRecord]:
        return list(self.records.values())

    def delete(self, slide_id: str) -> bool:
        return self.records.pop(slide_id, None) is not None


class FakeIngestion:
    async def ingest(self, *, file, title) -> SlideRecord:
        return make_record("new-slide")


class FakeRAGService:
    async def retrieve(self, *, slide_id: str, question: str, top_k):
        return [RetrievedChunk(chunk_id="c1", text="chunk", page_number=2, chunk_index=0, distance=0.0, score=1.0)]

    async def answer(self, *, slide_id: str, question: str, top_k):
        sources = [RetrievedChunk(chunk_id="c1", text="chunk", page_number=2, chunk_index=0, distance=0.0, score=1.0)]
        return "câu trả lời", sources

    async def summarize(self, *, slide_id: str):
        return "tóm tắt", []


class FakeChroma:
    def __init__(self, page_chunks: list[RetrievedChunk] | None = None) -> None:
        self.deleted: str | None = None
        self.page_chunks = page_chunks if page_chunks is not None else []

    def delete_slide(self, slide_id: str) -> None:
        self.deleted = slide_id

    def get_page_chunks(self, *, slide_id: str, page_number: int) -> list[RetrievedChunk]:
        return self.page_chunks


class FakeFileService:
    def delete_slide_files(self, slide_id: str) -> None:
        pass


def make_app(
    *,
    repository: FakeRepository | None = None,
    ingestion: FakeIngestion | None = None,
    rag_service: FakeRAGService | None = None,
    chroma: FakeChroma | None = None,
) -> tuple[FastAPI, FakeRepository, FakeChroma]:
    app = FastAPI()
    api = APIRouter(prefix="/api/v1")
    api.include_router(slides_routes.router)
    api.include_router(rag_routes.router)
    app.include_router(api)

    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        status_code = 404 if "không tìm thấy" in str(exc).lower() else 400
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    repository = repository if repository is not None else FakeRepository()
    chroma = chroma if chroma is not None else FakeChroma()

    app.dependency_overrides[get_slide_repository] = lambda: repository
    app.dependency_overrides[get_ingestion_service] = lambda: (ingestion or FakeIngestion())
    app.dependency_overrides[get_rag_service] = lambda: (rag_service or FakeRAGService())
    app.dependency_overrides[get_chroma_service] = lambda: chroma
    app.dependency_overrides[get_file_service] = lambda: FakeFileService()
    return app, repository, chroma


def test_upload_slide_does_not_require_user_id() -> None:
    app, _repo, _chroma = make_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/slides/upload",
        data={"title": "Machine Learning"},
        files={"file": ("slides.pdf", BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert "user_id" not in body
    assert body["slide_id"] == "new-slide"


def test_list_slides_does_not_require_user_id_query_param() -> None:
    repository = FakeRepository({"s1": make_record("s1")})
    app, _repo, _chroma = make_app(repository=repository)
    client = TestClient(app)

    response = client.get("/api/v1/slides")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert "user_id" not in body[0]


def test_get_slide_returns_404_when_missing() -> None:
    app, _repo, _chroma = make_app(repository=FakeRepository({}))
    client = TestClient(app)

    response = client.get("/api/v1/slides/unknown")

    assert response.status_code == 404


def test_get_slide_returns_record_without_user_id_query_param() -> None:
    repository = FakeRepository({"s1": make_record("s1")})
    app, _repo, _chroma = make_app(repository=repository)
    client = TestClient(app)

    response = client.get("/api/v1/slides/s1")

    assert response.status_code == 200
    assert "user_id" not in response.json()


def test_delete_slide_removes_record_and_chroma_chunks() -> None:
    repository = FakeRepository({"s1": make_record("s1")})
    chroma = FakeChroma()
    app, _repo, _chroma = make_app(repository=repository, chroma=chroma)
    client = TestClient(app)

    response = client.delete("/api/v1/slides/s1")

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert chroma.deleted == "s1"
    assert repository.get("s1") is None


def test_rag_query_endpoint_only_needs_slide_id_and_question() -> None:
    app, _repo, _chroma = make_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/rag/query",
        json={"slide_id": "s1", "question": "Gradient descent là gì?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "user_id" not in body
    assert body["answer"] == "câu trả lời"
    assert body["sources"][0]["page_number"] == 2


def test_rag_retrieve_endpoint_only_needs_slide_id() -> None:
    app, _repo, _chroma = make_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/rag/retrieve",
        json={"slide_id": "s1", "question": "Gradient descent là gì?"},
    )

    assert response.status_code == 200
    assert response.json()["sources"][0]["page_number"] == 2


def test_rag_summarize_endpoint_only_needs_slide_id() -> None:
    app, _repo, _chroma = make_app()
    client = TestClient(app)

    response = client.post("/api/v1/rag/summarize", json={"slide_id": "s1"})

    assert response.status_code == 200
    assert response.json()["answer"] == "tóm tắt"


def test_rag_query_rejects_missing_slide_id() -> None:
    app, _repo, _chroma = make_app()
    client = TestClient(app)

    response = client.post("/api/v1/rag/query", json={"question": "q"})

    assert response.status_code == 422


def test_get_slide_file_streams_the_stored_pdf_bytes(tmp_path: Path) -> None:
    pdf_path = tmp_path / "s1.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")
    repository = FakeRepository({"s1": make_record("s1", stored_path=pdf_path)})
    app, _repo, _chroma = make_app(repository=repository)
    client = TestClient(app)

    response = client.get("/api/v1/slides/s1/file")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 fake content"


def test_get_slide_file_404_when_slide_missing() -> None:
    app, _repo, _chroma = make_app(repository=FakeRepository({}))
    client = TestClient(app)

    response = client.get("/api/v1/slides/unknown/file")

    assert response.status_code == 404


def test_get_slide_file_404_when_file_missing_on_disk(tmp_path: Path) -> None:
    missing_path = tmp_path / "gone.pdf"
    repository = FakeRepository({"s1": make_record("s1", stored_path=missing_path)})
    app, _repo, _chroma = make_app(repository=repository)
    client = TestClient(app)

    response = client.get("/api/v1/slides/s1/file")

    assert response.status_code == 404


def test_get_slide_page_text_joins_chunks_in_order() -> None:
    repository = FakeRepository({"s1": make_record("s1")})
    chroma = FakeChroma(page_chunks=[
        RetrievedChunk(chunk_id="s1:0", text="Phần đầu", page_number=3, chunk_index=0, distance=0.0, score=1.0),
        RetrievedChunk(chunk_id="s1:1", text="Phần sau", page_number=3, chunk_index=1, distance=0.0, score=1.0),
    ])
    app, _repo, _chroma = make_app(repository=repository, chroma=chroma)
    client = TestClient(app)

    response = client.get("/api/v1/slides/s1/pages/3")

    assert response.status_code == 200
    body = response.json()
    assert body["page_number"] == 3
    assert body["text"] == "Phần đầu\n\nPhần sau"


def test_get_slide_page_text_404_when_slide_missing() -> None:
    app, _repo, _chroma = make_app(repository=FakeRepository({}))
    client = TestClient(app)

    response = client.get("/api/v1/slides/unknown/pages/1")

    assert response.status_code == 404


def test_get_slide_page_text_empty_when_no_chunks_for_page() -> None:
    repository = FakeRepository({"s1": make_record("s1")})
    app, _repo, _chroma = make_app(repository=repository, chroma=FakeChroma(page_chunks=[]))
    client = TestClient(app)

    response = client.get("/api/v1/slides/s1/pages/99")

    assert response.status_code == 200
    assert response.json()["text"] == ""
