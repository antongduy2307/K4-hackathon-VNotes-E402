from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools import TOOL_FUNCTIONS, load_tool_declarations
from tools.note_capture.tool import generate_note
from tools.rag_query.tool import rag_query
from tools.rag_summary.tool import rag_summary

ROOT = Path(__file__).resolve().parents[1]


class AgentProjectContractTests(unittest.TestCase):
    def test_declared_tools_are_implemented(self) -> None:
        declarations = load_tool_declarations(ROOT / "artifacts" / "tools.yaml")
        declared = {item["name"] for item in declarations}
        self.assertEqual(declared, set(TOOL_FUNCTIONS))
        self.assertIn("rag_query", declared)
        self.assertIn("rag_summary", declared)
        self.assertIn("clarify", declared)

    def test_eval_base_cases_reference_declared_tools_only(self) -> None:
        declarations = load_tool_declarations(ROOT / "artifacts" / "tools.yaml")
        declared = {item["name"] for item in declarations}
        data = json.loads((ROOT / "data" / "eval_base.json").read_text(encoding="utf-8"))
        for case in data["cases"]:
            for call in case.get("expect", {}).get("tool_calls", []):
                self.assertIn(call["name"], declared, msg=f"case {case['id']} expects undeclared tool {call['name']}")

    def test_eval_base_cases_have_unique_ids_and_required_shape(self) -> None:
        data = json.loads((ROOT / "data" / "eval_base.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in cases:
            self.assertEqual(case["phase"], "B")
            self.assertIn(case["failure_type"], {
                "wrong_tool", "wrong_arg_value", "wrong_boundary",
                "unnecessary_tool", "out_of_scope", "missing_info",
            })
            self.assertTrue(case["metadata"]["what_it_tests"])

    def test_eval_guardrail_cases_have_required_shape(self) -> None:
        data = json.loads((ROOT / "data" / "eval_guardrail.json").read_text(encoding="utf-8"))
        for case in data["cases"]:
            self.assertIn(case["mock_tool"], TOOL_FUNCTIONS)
            self.assertTrue(case["forbidden_patterns"] or case["required_patterns_any"])


class RagToolHttpContractTests(unittest.TestCase):
    """rag_query/rag_summary must call the backend over HTTP and degrade
    gracefully (never raise) when the backend is unreachable or returns
    partial data — the agent loop treats every tool result as a plain dict.
    """

    @patch("tools.rag_query.tool.post_json")
    def test_rag_query_calls_rag_query_endpoint_with_slide_id(self, mock_post: Mock) -> None:
        mock_post.return_value = {"answer": "42", "sources": [{"page_number": 1}]}
        result = rag_query(doc_id="s1", query="what is it?")
        mock_post.assert_called_once_with(
            "/api/v1/rag/query",
            {"slide_id": "s1", "question": "what is it?"},
        )
        self.assertEqual(result["answer"], "42")
        self.assertEqual(result["sources"], [{"page_number": 1}])

    @patch("tools.rag_query.tool.post_json", side_effect=ConnectionError("backend down"))
    def test_rag_query_returns_error_dict_instead_of_raising(self, _mock_post: Mock) -> None:
        result = rag_query(doc_id="s1", query="q")
        self.assertEqual(result["tool"], "rag_query")
        self.assertIn("error", result)

    def test_rag_query_missing_args_is_handled_locally_without_http_call(self) -> None:
        result = rag_query(doc_id="", query="q")
        self.assertEqual(result["error"], "missing_argument")

    @patch("tools.rag_summary.tool.post_json")
    def test_rag_summary_calls_dedicated_summarize_endpoint(self, mock_post: Mock) -> None:
        mock_post.return_value = {"answer": "tóm tắt", "sources": [{"page_number": 1}]}
        result = rag_summary(doc_id="s1")
        mock_post.assert_called_once_with(
            "/api/v1/rag/summarize",
            {"slide_id": "s1"},
        )
        self.assertEqual(result["summary"], "tóm tắt")

    @patch("tools.rag_summary.tool.post_json", side_effect=ConnectionError("backend down"))
    def test_rag_summary_returns_error_dict_instead_of_raising(self, _mock_post: Mock) -> None:
        result = rag_summary(doc_id="s1")
        self.assertEqual(result["tool"], "rag_summary")
        self.assertIn("error", result)


class NoteCaptureFilterTests(unittest.TestCase):
    def test_keeps_only_rag_query_exchanges_with_specific_questions(self) -> None:
        turns = [
            {"question": "Gradient descent hoạt động thế nào?", "answer": "...", "tool_used": "rag_query", "sources": [{"page_number": 3}]},
            {"question": "Tóm tắt tài liệu này giúp mình", "answer": "...", "tool_used": "rag_summary", "sources": []},
            {"question": "Đặt vé máy bay giúp mình", "answer": "Ngoài phạm vi.", "tool_used": None, "sources": []},
            {"question": "Tóm tắt toàn bộ nội dung slide", "answer": "...", "tool_used": "rag_query", "sources": [{"page_number": 1}]},
        ]
        result = generate_note(doc_id="doc1", conversation_turns=turns)

        self.assertEqual(result["kept_count"], 1)
        self.assertEqual(result["notes"][0]["question"], "Gradient descent hoạt động thế nào?")
        self.assertEqual(result["excluded_count"], 3)
        reasons = {item["reason"] for item in result["excluded"]}
        self.assertEqual(reasons, {"whole_document_summary", "off_topic_or_unanswered", "broad_scope_question"})

    def test_empty_conversation_returns_empty_note(self) -> None:
        result = generate_note(doc_id="doc1", conversation_turns=[])
        self.assertEqual(result["kept_count"], 0)
        self.assertEqual(result["notes"], [])

    def test_broad_scope_english_marker_is_excluded(self) -> None:
        turns = [
            {"question": "Give me an overview of this deck", "answer": "...", "tool_used": "rag_query", "sources": []},
        ]
        result = generate_note(doc_id="doc1", conversation_turns=turns)
        self.assertEqual(result["kept_count"], 0)
        self.assertEqual(result["excluded"][0]["reason"], "broad_scope_question")


if __name__ == "__main__":
    unittest.main()
