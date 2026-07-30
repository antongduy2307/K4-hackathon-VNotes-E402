from __future__ import annotations

import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from export.anki_export import build_anki_deck, export_anki_to_file
from export.notion_export import consolidate_notes, extract_page_id, push_notes_to_notion
from export.obsidian_export import build_obsidian_markdown, export_obsidian_to_file, parse_existing_note

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


class ObsidianExportTests(unittest.TestCase):
    def test_frontmatter_only_has_title_no_doc_id_or_date(self) -> None:
        content = build_obsidian_markdown(SAMPLE_NOTES, title="Week 03 - Optimization", openai_api_key=None)
        self.assertTrue(content.startswith("---\n"))
        self.assertIn('title: "Week 03 - Optimization"', content)
        self.assertNotIn("doc_id", content)
        self.assertNotIn("created", content)

    def test_markdown_includes_key_points_and_qa_sections(self) -> None:
        content = build_obsidian_markdown(SAMPLE_NOTES, title="Week 03 - Optimization", openai_api_key=None)
        self.assertIn("## Ý chính", content)
        self.assertIn("## Chi tiết câu hỏi & trả lời", content)
        self.assertIn("Gradient descent là gì?", content)
        self.assertIn("tr.3-4", content)

    def test_empty_notes_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_obsidian_markdown([], title="Week 03 - Optimization")

    def test_export_writes_utf8_file(self) -> None:
        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "note.md"
            export_obsidian_to_file(SAMPLE_NOTES, title="Week 03 - Optimization", out_path=out_path, openai_api_key=None)
            self.assertTrue(out_path.exists())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("Gradient descent", text)

    def test_reexport_updates_same_file_instead_of_duplicating(self) -> None:
        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "note.md"
            export_obsidian_to_file(SAMPLE_NOTES[:1], title="Week 03 - Optimization", out_path=out_path, openai_api_key=None)
            first_content = out_path.read_text(encoding="utf-8")
            self.assertIn("Gradient descent", first_content)
            self.assertNotIn("Momentum", first_content)

            export_obsidian_to_file(SAMPLE_NOTES, title="Week 03 - Optimization", out_path=out_path, openai_api_key=None)
            second_content = out_path.read_text(encoding="utf-8")
            # both old and newly-added question still present, in the SAME file
            self.assertIn("Gradient descent", second_content)
            self.assertIn("Momentum", second_content)
            self.assertEqual(second_content.count("### Gradient descent là gì?"), 1)

    def test_reexport_with_no_new_questions_leaves_file_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "note.md"
            export_obsidian_to_file(SAMPLE_NOTES, title="Week 03 - Optimization", out_path=out_path, openai_api_key=None)
            first_content = out_path.read_text(encoding="utf-8")

            export_obsidian_to_file(SAMPLE_NOTES, title="Week 03 - Optimization", out_path=out_path, openai_api_key=None)
            second_content = out_path.read_text(encoding="utf-8")
            self.assertEqual(first_content, second_content)

    def test_parse_existing_note_roundtrip(self) -> None:
        content = build_obsidian_markdown(SAMPLE_NOTES, title="Week 03 - Optimization", openai_api_key=None)
        parsed = parse_existing_note(content)
        self.assertEqual(parsed["title"], "Week 03 - Optimization")
        self.assertEqual(set(parsed["qa_entries"]), {"Gradient descent là gì?", "Momentum dùng để làm gì?"})

    def test_parse_existing_note_returns_none_for_hand_edited_file(self) -> None:
        self.assertIsNone(parse_existing_note("# Some random note\n\njust text, not our format"))


class NotionPageIdTests(unittest.TestCase):
    def test_extracts_id_from_full_url(self) -> None:
        url = "https://www.notion.so/myteam/a1b2c3d4e5f647890abcdef123456789?v=xyz"
        self.assertEqual(extract_page_id(url), "a1b2c3d4e5f647890abcdef123456789")

    def test_extracts_id_from_dashed_url(self) -> None:
        url = "https://www.notion.so/a1b2c3d4-e5f6-4789-0abc-def123456789"
        self.assertEqual(extract_page_id(url), "a1b2c3d4e5f647890abcdef123456789")

    def test_passes_through_bare_id(self) -> None:
        self.assertEqual(extract_page_id("a1b2c3d4e5f647890abcdef123456789"), "a1b2c3d4e5f647890abcdef123456789")


class ConsolidateNotesTests(unittest.TestCase):
    def test_without_openai_key_falls_back_to_one_bullet_per_note(self) -> None:
        bullets = consolidate_notes(SAMPLE_NOTES, api_key=None)
        self.assertEqual(len(bullets), 2)
        self.assertIn("Gradient descent là gì?", bullets[0])

    @patch("openai.OpenAI")
    def test_uses_llm_output_lines_when_key_present(self, mock_openai_cls: Mock) -> None:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="- Ý chính A\n- Ý chính B"))]
        )
        mock_openai_cls.return_value = mock_client

        bullets = consolidate_notes(SAMPLE_NOTES, api_key="secret")
        self.assertEqual(bullets, ["Ý chính A", "Ý chính B"])

    @patch("openai.OpenAI", side_effect=RuntimeError("network down"))
    def test_llm_failure_falls_back_to_one_bullet_per_note(self, _mock_openai_cls: Mock) -> None:
        bullets = consolidate_notes(SAMPLE_NOTES, api_key="secret")
        self.assertEqual(len(bullets), 2)


class NotionExportTests(unittest.TestCase):
    def test_missing_api_key_returns_error_without_http_call(self) -> None:
        result = push_notes_to_notion(SAMPLE_NOTES, doc_id="day03_optimization", api_key=None, page_id="page123")
        self.assertEqual(result["error"], "missing_config")

    def test_missing_page_id_returns_error_without_http_call(self) -> None:
        result = push_notes_to_notion(SAMPLE_NOTES, doc_id="day03_optimization", api_key="secret", page_id=None)
        self.assertEqual(result["error"], "missing_config")

    def test_empty_notes_returns_error(self) -> None:
        result = push_notes_to_notion([], doc_id="day03_optimization", api_key="secret", page_id="page123")
        self.assertEqual(result["error"], "no_notes")

    @patch("export.notion_export.requests.patch")
    def test_appends_heading_and_one_bullet_per_key_point(self, mock_patch: Mock) -> None:
        mock_patch.return_value = Mock(raise_for_status=Mock())
        result = push_notes_to_notion(
            SAMPLE_NOTES, doc_id="day03_optimization", api_key="secret", page_id="page123", openai_api_key=None,
        )

        self.assertEqual(result["key_point_count"], 2)
        mock_patch.assert_called_once()
        call_url = mock_patch.call_args.args[0]
        self.assertEqual(call_url, "https://api.notion.com/v1/blocks/page123/children")
        children = mock_patch.call_args.kwargs["json"]["children"]
        self.assertEqual(children[0]["type"], "heading_2")
        self.assertEqual(len(children), 1 + 2)  # heading + 2 fallback bullets

    @patch("export.notion_export.requests.patch", side_effect=ConnectionError("network down"))
    def test_http_failure_returns_error_instead_of_raising(self, _mock_patch: Mock) -> None:
        result = push_notes_to_notion(SAMPLE_NOTES, doc_id="day03_optimization", api_key="secret", page_id="page123")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
