"""Orchestration: ingest a PDF, summarize it, answer questions grounded in it."""
import tiktoken

from app.config import settings
from app.core.chunker import chunk_pages
from app.core.llm import chat
from app.core.pdf_loader import load_pdf_pages
from app.core.vectorstore import add_chunks, delete_document, get_all_chunks, query

_ENCODING = tiktoken.get_encoding("cl100k_base")

_MAP_PROMPT = (
    "Bạn là trợ giảng. Tóm tắt đoạn tài liệu sau bằng tiếng Việt, ngắn gọn, "
    "giữ lại các khái niệm và số liệu quan trọng. Chỉ trả về bản tóm tắt."
)
_REDUCE_PROMPT = (
    "Bạn là trợ giảng. Dưới đây là các tóm tắt từng phần của cùng một tài liệu, theo thứ tự trang. "
    "Kết hợp chúng thành MỘT bản tóm tắt mạch lạc cho người học, có cấu trúc "
    "(giới thiệu, các ý chính theo thứ tự, kết luận nếu phù hợp). Trả lời bằng tiếng Việt."
)
_ANSWER_PROMPT = (
    "Bạn là trợ giảng, chỉ được trả lời dựa trên NGỮ CẢNH cung cấp bên dưới, trích từ tài liệu học. "
    "Nếu ngữ cảnh không đủ để trả lời, nói rõ là tài liệu không đề cập. "
    "Luôn ghi rõ số trang nguồn (vd: 'theo trang 3') cho mỗi ý bạn nêu. Trả lời bằng tiếng Việt."
)

# single-shot summarization budget: below this token count, skip map-reduce
_SINGLE_SHOT_TOKEN_BUDGET = 6000


def ingest_pdf(doc_id: str, pdf_path: str) -> int:
    """Extract, chunk, embed, and store a PDF. Returns number of chunks stored."""
    delete_document(doc_id)  # re-ingest is idempotent
    pages = load_pdf_pages(pdf_path)
    chunks = chunk_pages(
        doc_id,
        pages,
        chunk_size_tokens=settings.chunk_size_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    add_chunks(doc_id, chunks)
    return len(chunks)


def summarize_document(doc_id: str) -> str:
    chunks = get_all_chunks(doc_id)
    if not chunks:
        raise ValueError(f"No chunks found for doc_id={doc_id}. Ingest it first.")

    full_text = "\n\n".join(c["text"] for c in chunks)
    total_tokens = len(_ENCODING.encode(full_text))

    if total_tokens <= _SINGLE_SHOT_TOKEN_BUDGET:
        return chat(_MAP_PROMPT, full_text)

    # map: summarize each chunk independently
    partial_summaries = [chat(_MAP_PROMPT, c["text"]) for c in chunks]

    # reduce: combine partial summaries into one, with page ranges for traceability
    combined = "\n\n".join(
        f"[Trang {c['metadata']['page_start']}-{c['metadata']['page_end']}] {summary}"
        for c, summary in zip(chunks, partial_summaries)
    )
    return chat(_REDUCE_PROMPT, combined)


def answer_question(doc_id: str, question: str, top_k: int | None = None) -> dict:
    hits = query(doc_id, question, top_k=top_k or settings.retrieval_top_k)
    if not hits:
        return {
            "answer": "Tài liệu này chưa được xử lý hoặc không tìm thấy nội dung liên quan.",
            "sources": [],
        }

    context = "\n\n".join(
        f"[Trang {h['metadata']['page_start']}-{h['metadata']['page_end']}] {h['text']}"
        for h in hits
    )
    user_prompt = f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {question}"
    answer = chat(_ANSWER_PROMPT, user_prompt)

    sources = [
        {"page_start": h["metadata"]["page_start"], "page_end": h["metadata"]["page_end"]}
        for h in hits
    ]
    return {"answer": answer, "sources": sources}
