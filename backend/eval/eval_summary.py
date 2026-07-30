"""LLM-judge scoring of generated summaries against hand-written ground truth.

Usage:
    python eval/eval_summary.py eval/ground_truth/example.json
"""
import json
import sys

sys.path.insert(0, ".")

from app.core.llm import chat  # noqa: E402
from app.core.rag import ingest_pdf, summarize_document  # noqa: E402

_JUDGE_PROMPT = (
    "Bạn là giám khảo chấm tóm tắt tài liệu học tập. So sánh SUMMARY được sinh ra với "
    "REFERENCE (chuẩn). Chấm theo 3 tiêu chí, mỗi tiêu chí 0-5: "
    "(1) độ chính xác - không bịa thông tin, "
    "(2) độ đầy đủ - có đủ ý chính so với reference, "
    "(3) độ rõ ràng - dễ hiểu với người học. "
    "Trả về JSON: {\"accuracy\": int, \"completeness\": int, \"clarity\": int, \"notes\": str}"
)


def score_summary(generated: str, reference: str) -> dict:
    user_prompt = f"REFERENCE:\n{reference}\n\nSUMMARY:\n{generated}"
    raw = chat(_JUDGE_PROMPT, user_prompt, temperature=0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw, "parse_error": True}


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    ingest_pdf(case["doc_id"], case["pdf_path"])
    generated = summarize_document(case["doc_id"])
    result = score_summary(generated, case["reference_summary"])

    print("=== GENERATED SUMMARY ===")
    print(generated)
    print("\n=== SCORE ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
