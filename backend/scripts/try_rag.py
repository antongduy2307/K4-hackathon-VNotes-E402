"""CLI smoke test: ingest a PDF, print its summary, ask it a question.

Usage:
    python scripts/try_rag.py path/to/file.pdf "câu hỏi của bạn"
"""
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from app.core.rag import answer_question, ingest_pdf, summarize_document  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "Tài liệu này nói về nội dung gì?"
    doc_id = "smoke-test-doc"

    print(f"Ingesting {pdf_path} ...")
    n_chunks = ingest_pdf(doc_id, pdf_path)
    print(f"Stored {n_chunks} chunks.\n")

    print("=== SUMMARY ===")
    print(summarize_document(doc_id))

    print("\n=== Q&A ===")
    print(f"Q: {question}")
    result = answer_question(doc_id, question)
    print(f"A: {result['answer']}")
    print(f"Sources: {result['sources']}")


if __name__ == "__main__":
    main()
