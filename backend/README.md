# VLearn RAG — PDF ingest, summary, Q&A

Minimal RAG pipeline: PDF → page-aware chunks → OpenAI embeddings → Chroma → summary / grounded Q&A.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # then fill OPENAI_API_KEY
```

## Run API

```bash
uvicorn app.main:app --reload --port 8000
```

- `POST /documents` — multipart upload, field `file` (.pdf). Returns `doc_id`.
- `GET /documents/{doc_id}/summary` — full-document summary.
- `POST /chat` — `{"doc_id": "...", "question": "..."}` → grounded answer + source pages.

## Smoke test without the API

```bash
python scripts/try_rag.py path/to/file.pdf "câu hỏi của bạn"
```

## Unit tests

```bash
pytest
```

Covers chunking logic only (no API calls). `pdf_loader` and `rag.py` need a sample PDF and an API key to test end-to-end — see `eval/`.

## Eval

`eval/ground_truth/*.json` — hand-written reference summaries and Q&A pairs per PDF, one file per test document. Copy `example.json`, point `pdf_path` at a real file, fill in `reference_summary` and `qa_pairs` with `expected_pages`.

```bash
python eval/eval_summary.py eval/ground_truth/your_case.json    # LLM-judge score: accuracy/completeness/clarity
python eval/eval_retrieval.py eval/ground_truth/your_case.json  # retrieval grounding pass/fail per question
```

## How it works

1. `pdf_loader.py` — extract text per page (`pdfplumber`).
2. `chunker.py` — flatten pages into one token stream, slide a window (default 500 tokens, 80 overlap) so chunks can span page breaks; each chunk keeps its `page_start`/`page_end`.
3. `embeddings.py` / `vectorstore.py` — embed chunks (`text-embedding-3-small`), store in a local persistent Chroma collection, filterable by `doc_id`.
4. `rag.py`:
   - `ingest_pdf` — run the pipeline above.
   - `summarize_document` — single-shot summary if the doc fits the token budget, else map-reduce (summarize each chunk, then combine).
   - `answer_question` — embed the question, retrieve top-k chunks for that `doc_id`, force the LLM to cite page numbers and to say "tài liệu không đề cập" when context is insufficient.

## Known gaps / next steps

- PDF only. Frontend viewer pipeline (pptx → LibreOffice → PDF.js) is decided separately — once that lands, this backend can ingest the converted PDF directly.
- No auth, no multi-tenant isolation beyond `doc_id` filtering.
- `pdf_loader` appends `extract_tables()` output after the prose text so simple tables aren't lost. Cell text may appear twice (once jumbled in prose, once as clean rows) — harmless for LLM context, but revisit if slides get table-heavy.
- No caching of embeddings/summaries across re-uploads of the same file (re-ingest always re-embeds).
