from __future__ import annotations

import zipfile

from fastapi.testclient import TestClient

from export_api import app

client = TestClient(app)

SAMPLE_TURNS = [
    {
        "question": "Gradient descent là gì?",
        "answer": "Thuật toán tối ưu lặp.",
        "tool_used": "rag_query",
        "sources": [{"chunk_id": "c1", "page_number": 3, "chunk_index": 0, "text": "...", "score": 0.9}],
    },
    {
        "question": "Tóm tắt tài liệu này giúp mình",
        "answer": "...",
        "tool_used": "rag_summary",
        "sources": [],
    },
    {
        "question": "Đặt vé máy bay giúp mình",
        "answer": "Ngoài phạm vi.",
        "tool_used": None,
        "sources": [],
    },
]


def test_capture_notes_filters_out_summary_and_offtopic_exchanges() -> None:
    response = client.post(
        "/notes/capture",
        json={"doc_id": "doc1", "conversation_turns": SAMPLE_TURNS},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kept_count"] == 1
    assert body["notes"][0]["question"] == "Gradient descent là gì?"
    assert body["excluded_count"] == 2


def test_capture_notes_accepts_real_source_chunk_shape_without_validation_error() -> None:
    # Note.sources used to be typed list[dict[str, int]], which would reject
    # chunk_id (str) / text (str) / score (float) from the real backend shape.
    response = client.post(
        "/notes/capture",
        json={
            "doc_id": "doc1",
            "conversation_turns": [{
                "question": "q",
                "answer": "a",
                "tool_used": "rag_query",
                "sources": [{"chunk_id": "abc", "page_number": 5, "chunk_index": 2, "text": "hello", "score": 0.87}],
            }],
        },
    )

    assert response.status_code == 200
    assert response.json()["kept_count"] == 1


def test_export_anki_returns_a_valid_apkg_file() -> None:
    response = client.post(
        "/export/anki",
        json={
            "doc_id": "doc1",
            "notes": [{
                "question": "Gradient descent là gì?",
                "answer": "Thuật toán tối ưu.",
                "sources": [{"chunk_id": "c1", "page_number": 3, "chunk_index": 0, "text": "...", "score": 0.9}],
            }],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    import io
    assert zipfile.is_zipfile(io.BytesIO(response.content))


def test_export_anki_rejects_empty_notes() -> None:
    response = client.post("/export/anki", json={"doc_id": "doc1", "notes": []})
    assert response.status_code == 400


def test_export_obsidian_returns_markdown_with_real_source_shape() -> None:
    response = client.post(
        "/export/obsidian",
        json={
            "doc_id": "doc1",
            "title": "Test Doc",
            "notes": [{
                "question": "Gradient descent là gì?",
                "answer": "Thuật toán tối ưu.",
                "sources": [{"chunk_id": "c1", "page_number": 3, "chunk_index": 0, "text": "...", "score": 0.9}],
            }],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert b"Gradient descent" in response.content


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
