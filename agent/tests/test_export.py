from __future__ import annotations

import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from export.anki_export import build_anki_deck, export_anki_to_file
from export.notion_export import push_notes_to_notion

SAMPLE_NOTES = [
    {"question": "Gradient descent là gì?", "answer": "Thuật toán tối ưu lặp.", "sources": [{"page_start": 3, "page_end": 4}]},
    {"question": "Momentum dùng để làm gì?", "answer": "Tăng tốc hội tụ.", "sources": [{"page_start": 5, "page_end": 5}]},
]


class AnkiExportTests(unittest.TestCase):
    def test_build_deck_has_one_card_per_note(self) -> None:
        deck = build_anki_deck(SAMPLE_NOTES, doc_id="day03_optimization")
        self.assertEqual(len(deck.notes), 2)

    def test_same_doc_id_produces_same_deck_id_across_calls(self) -> None:
        deck1 = build_anki_deck(SAMPLE_NOTES, doc_id="day03_optimization")
        deck2 = build_anki_deck(SAMPLE_NOTES, doc_id="day03_optimization")
        self.assertEqual(deck1.deck_id, deck2.deck_id)

    def test_different_doc_id_produces_different_deck_id(self) -> None:
        deck1 = build_anki_deck(SAMPLE_NOTES, doc_id="day03_optimization")
        deck2 = build_anki_deck(SAMPLE_NOTES, doc_id="day01_intro")
        self.assertNotEqual(deck1.deck_id, deck2.deck_id)

    def test_empty_notes_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_anki_deck([], doc_id="day03_optimization")

    def test_export_writes_a_valid_apkg_zip_file(self) -> None:
        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "deck.apkg"
            export_anki_to_file(SAMPLE_NOTES, doc_id="day03_optimization", out_path=out_path)
            self.assertTrue(out_path.exists())
            self.assertTrue(zipfile.is_zipfile(out_path))


class NotionExportTests(unittest.TestCase):
    def test_missing_api_key_returns_error_without_http_call(self) -> None:
        result = push_notes_to_notion(SAMPLE_NOTES, doc_id="day03_optimization", api_key=None, database_id="db123")
        self.assertEqual(result["error"], "missing_config")

    def test_missing_database_id_returns_error_without_http_call(self) -> None:
        result = push_notes_to_notion(SAMPLE_NOTES, doc_id="day03_optimization", api_key="secret", database_id=None)
        self.assertEqual(result["error"], "missing_config")

    def test_empty_notes_returns_error(self) -> None:
        result = push_notes_to_notion([], doc_id="day03_optimization", api_key="secret", database_id="db123")
        self.assertEqual(result["error"], "no_notes")

    @patch("export.notion_export.requests.post")
    def test_creates_one_page_per_note_with_correct_properties(self, mock_post: Mock) -> None:
        mock_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"id": "page-1", "url": "https://notion.so/page-1"}),
        )
        result = push_notes_to_notion(SAMPLE_NOTES, doc_id="day03_optimization", api_key="secret", database_id="db123")

        self.assertEqual(result["created_count"], 2)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(mock_post.call_count, 2)

        first_call_payload = mock_post.call_args_list[0].kwargs["json"]
        self.assertEqual(first_call_payload["parent"], {"database_id": "db123"})
        title = first_call_payload["properties"]["Question"]["title"][0]["text"]["content"]
        self.assertEqual(title, "Gradient descent là gì?")

    @patch("export.notion_export.requests.post", side_effect=ConnectionError("network down"))
    def test_per_note_http_failure_is_collected_not_raised(self, _mock_post: Mock) -> None:
        result = push_notes_to_notion(SAMPLE_NOTES, doc_id="day03_optimization", api_key="secret", database_id="db123")
        self.assertEqual(result["created_count"], 0)
        self.assertEqual(result["failed_count"], 2)


if __name__ == "__main__":
    unittest.main()
