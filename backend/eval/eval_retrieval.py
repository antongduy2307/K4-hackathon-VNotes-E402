"""Grounding check: for each Q&A pair, does retrieval hit the expected source pages?

Usage:
    python eval/eval_retrieval.py eval/ground_truth/example.json
"""
import json
import sys

sys.path.insert(0, ".")

from app.core.rag import answer_question, ingest_pdf  # noqa: E402


def pages_overlap(retrieved_sources: list[dict], expected_pages: list[int]) -> bool:
    retrieved_pages = set()
    for s in retrieved_sources:
        retrieved_pages.update(range(s["page_start"], s["page_end"] + 1))
    return bool(retrieved_pages & set(expected_pages))


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    ingest_pdf(case["doc_id"], case["pdf_path"])

    total = len(case["qa_pairs"])
    hits = 0

    for qa in case["qa_pairs"]:
        result = answer_question(case["doc_id"], qa["question"])
        grounded = pages_overlap(result["sources"], qa["expected_pages"])
        hits += grounded

        print(f"Q: {qa['question']}")
        print(f"A: {result['answer']}")
        print(f"Expected pages: {qa['expected_pages']} | Retrieved: {result['sources']}")
        print(f"Grounded: {'PASS' if grounded else 'FAIL'}\n")

    print(f"Retrieval grounding: {hits}/{total} passed")


if __name__ == "__main__":
    main()
