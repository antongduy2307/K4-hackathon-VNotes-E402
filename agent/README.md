# VLearn Tutor Agent

Đứng độc lập với `app/` (RAG backend, ở gốc repo) — chỉ gọi qua HTTP
(`VLEARN_BACKEND_URL`), không import code của `app/`. Ngược lại, `app/`
**có** import trực tiếp `agent.py`/`providers/openai_provider.py` (xem
`app/services/rag_service.py::_answer_with_agent`) để tự tổng hợp câu trả
lời — nghĩa là đổi vị trí/tên các file đó phải sửa cả bên `app/`.

Kiến trúc phiên: **mỗi tài liệu là một phiên (session) riêng biệt, với lịch sử
hội thoại riêng biệt** — không có chuyện nhiều tài liệu dùng chung một phiên,
và `doc_id` không bao giờ đổi giữa hội thoại. Vì vậy `doc_id` là tham số
session (do orchestrator gắn cứng khi phiên bắt đầu), KHÔNG phải thứ model tự
đọc/suy ra từ tin nhắn — loại bỏ hẳn lớp lỗi "model đoán sai/quên doc_id".
Model chỉ gọi `rag_query(query)`, `rag_summary()`, `note_capture()` — không đối
số định danh tài liệu; `apply_session_args()` (`tools/__init__.py`) tự điền
`doc_id` (và `conversation_turns` cho `note_capture`) trước khi hàm thật chạy.

Giao thức: agent gọi RAG qua `POST /api/v1/rag/query` (`{slide_id, question}`)
hoặc `POST /api/v1/rag/summarize` (`{slide_id}`), rồi tổng hợp câu trả lời
cuối cùng (trích trang nguồn từ `sources[].page_number`) để gửi lại người
dùng. `doc_id` phía agent = `slide_id` phía backend, cùng một giá trị, khác
tên do lịch sử phát triển hai bên độc lập.

## Cấu trúc

```
agent/
  agent.py           một vòng gọi model + tool (dùng cho eval routing, và được app/ import trực tiếp)
  chat.py            vòng lặp đầy đủ: gọi tool -> feed kết quả lại model -> câu trả lời cuối, có transcript
  env_loader.py       nạp .env (dùng chung bởi mọi entrypoint)
  versioning.py       hash system_prompt.md + tools.yaml thành artifact_version, để so sánh giữa các lần chỉnh prompt
  run_eval.py         eval độ chính xác routing tool + args
  eval_guardrail.py   eval hành vi cuối: chống prompt-injection cấy trong tài liệu, chống bịa khi RAG rỗng
  export_api.py       FastAPI: 3 endpoint cho nút "Lưu Anki"/"Lưu Notion"/"Lưu Obsidian" trên UI — KHÔNG qua agent/LLM
  tools/
    rag_query/         gọi POST {VLEARN_BACKEND_URL}/api/v1/rag/query (doc_id do session gắn)
    rag_summary/        gọi POST {VLEARN_BACKEND_URL}/api/v1/rag/summarize (doc_id do session gắn)
    note_capture/       lọc lịch sử hội thoại thành note (loại off-topic + tóm tắt toàn slide)
    clarify/             hỏi lại, dừng chờ user (không gọi RAG)
  providers/
    openai_provider.py  wrapper OpenAI Chat Completions, chuẩn hoá tool_calls
  export/
    anki_export.py      note_capture output -> file .apkg (genanki, offline, không cần Anki app)
    notion_export.py     note_capture output -> ý chính, append vào 1 trang Notion có sẵn (Notion API thật)
    obsidian_export.py   note_capture output -> file .md (frontmatter + ý chính + Q&A), không API/auth
  artifacts/
    system_prompt.md    routing rules + guardrail + trust boundary
    tools.yaml           khai báo tool cho model (OpenAI function-calling schema — không có doc_id)
  data/
    eval_base.json       case routing/clarify/out-of-scope/multi-turn (trong CÙNG 1 phiên/tài liệu)
    eval_guardrail.json  case guardrail (mock tool result, chấm câu trả lời cuối)
  samples/
    stream.pdf           PDF mẫu thật để test ingest/chat/export tay, không phải fixture cho pytest
  tests/                 test không cần API key (mock HTTP call tới backend/Notion)
  runs/                  output của run_eval.py (gitignore, trừ .gitkeep)
  transcripts/           output của chat.py (gitignore, trừ .gitkeep)
```

## Setup

```bash
cd agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env   # điền OPENAI_API_KEY; VLEARN_BACKEND_URL trỏ tới app/ đang chạy (mặc định http://localhost:8000)
```

## Chạy thử (cần `app/` đang chạy — `uvicorn app.main:app` ở gốc repo)

```bash
python chat.py --version v0 --doc-id <slide_id thật đã upload qua /api/v1/slides/upload>
```

`--doc-id` cố định cho suốt phiên chat này (đúng 1 tài liệu). Gõ câu hỏi bình
thường, không cần tự chèn context — ví dụ: "Tóm tắt tài liệu này giúp mình."
Transcript lưu ở `transcripts/*.transcript.json`. Có sẵn `samples/stream.pdf`
để upload thử qua `POST /api/v1/slides/upload` nếu chưa có tài liệu nào.

## Eval routing + args (không cần backend thật đang chạy — tool lỗi vẫn được chấm là bằng chứng)

```bash
python run_eval.py --version v0
```
Mỗi case trong `data/eval_base.json` khai `doc_id` riêng (giả lập 1 phiên/1 tài
liệu). Kết quả lưu `runs/*.json`, in bảng PASS/FAIL + `tool_routing_accuracy` /
`argument_accuracy` / `multiturn_accuracy`.

## Eval guardrail (backend không bắt buộc — tool result bị mock có chủ đích)

```bash
python eval_guardrail.py
```
Từng case tự thay `TOOL_FUNCTIONS[mock_tool]` bằng một hàm trả cố định nội
dung độc hại/rỗng, chạy hết vòng lặp thật (`chat.run_model_tool_loop`), rồi
kiểm câu trả lời CUỐI CÙNG không chứa `forbidden_patterns` (rò rỉ system
prompt, tuân theo chỉ thị cấy trong tài liệu) và có ít nhất một trong
`required_patterns_any` (ví dụ câu từ chối "tài liệu không đề cập" khi RAG
không có dữ liệu).

## Export (app-driven, không qua LLM)

`note_capture` chỉ lọc + trả note có cấu trúc. Export ra Anki/Notion/Obsidian
là hành động người dùng bấm nút trên UI, gọi thẳng `export_api.py` với đúng
list note đó — không để model tự quyết định ghi ra hệ thống ngoài.

```bash
uvicorn export_api:app --reload --port 8100
```

- `POST /export/anki` — body `{"doc_id": "...", "notes": [...]}` (notes lấy
  nguyên từ output của `note_capture`) → trả file `.apkg` tải về, import thẳng
  vào Anki. Offline hoàn toàn, không cần Anki app/AnkiConnect chạy nền — genanki
  tự sinh file. Deck ID cố định theo `doc_id` (hash), nên export lại cùng tài
  liệu sẽ update đúng deck đó khi import lại, không tạo trùng.
- `POST /export/notion` — cùng body → tổng hợp toàn bộ câu hỏi-đáp thành các Ý
  CHÍNH (gộp câu hỏi trùng chủ đề, không liệt kê nguyên văn Q&A) rồi append vào
  MỘT trang Notion có sẵn dưới dạng bullet list, không cần database/cột gì.
  Setup 3 bước, không cần biết code:
  1. Tạo integration tại notion.so/my-integrations, copy token → `NOTION_API_KEY`.
  2. Mở BẤT KỲ trang Notion nào, Share → Connections → add integration đó.
  3. Copy URL trang đó (hoặc chỉ id 32 ký tự) → `NOTION_PAGE_ID`.
  Tổng hợp ý chính dùng 1 lần gọi OpenAI (`OPENAI_API_KEY` đã có sẵn) — nếu
  thiếu key hoặc gọi lỗi, tự rơi về mỗi note 1 bullet "câu hỏi — câu trả lời"
  (không chặn export). Trả về `key_point_count`, `key_points`, `page_url`.
- `POST /export/obsidian` — body thêm `title` (tên hiển thị của slide/tài
  liệu, không phải `doc_id`) → trả file `.md` tải về. Frontmatter CHỈ có
  `title` — không doc_id, không ngày giờ, không tag rối mắt. Nội dung: mục "Ý
  chính" (dùng chung `consolidate_notes` với Notion) + mục "Chi tiết câu hỏi &
  trả lời" đầy đủ Q&A kèm trích trang. Không API, không auth, không network
  call ngoài (trừ 1 lần gọi OpenAI để tổng hợp ý chính, cùng fallback như
  Notion nếu thiếu key).
  **Export lại cùng tài liệu sẽ UPDATE file cũ, không tạo file mới**: dựa vào
  `doc_id` để xác định đúng file (`{doc_id}.md` trong thư mục export tạm),
  đọc nội dung cũ, chỉ thêm câu hỏi CHƯA từng xuất hiện trong file (so theo
  nguyên văn câu hỏi), chỉ tổng hợp ý chính cho riêng phần mới đó rồi nối vào
  danh sách ý chính cũ — không đụng/viết lại các câu hỏi và ý chính đã xuất
  trước đó. Nếu không có câu hỏi mới nào, file giữ nguyên y hệt. Nếu file cũ
  không đúng format do bị sửa tay, tự động coi như chưa có gì và tạo lại từ
  đầu (không cố gộp, tránh làm hỏng thêm).

## Test không cần API key

```bash
pytest
```
Mock HTTP call bằng `unittest.mock.patch`, kiểm tra: tool registry khớp
`tools.yaml`, `eval_base.json`/`eval_guardrail.json` đúng shape, `rag_query`/
`rag_summary` không bao giờ raise exception (luôn trả dict lỗi) khi backend
sập, logic lọc của `note_capture` (giữ đúng câu hỏi chi tiết, loại whole-doc
summary + off-topic), `anki_export`/`obsidian_export` sinh nội dung hợp lệ
theo schema `page_number` thật, `notion_export` gọi đúng payload và không
raise khi Notion API lỗi/thiếu config.

## Đã verify sống với `app/` thật (không phải mock)

Upload PDF thật → `rag_summary`/`rag_query` qua agent trả lời đúng, có trích
trang → `note_capture` lọc đúng → export Anki/Obsidian/Notion đều thành công.
Chi tiết root cause của 1 bug thật đã sửa (schema `sources`, endpoint
`rag_summary`, và một bug retrieval ở `app/services/chroma_service.py` không
thuộc phạm vi agent) — xem lịch sử commit.

## Việc còn lại / TODO

- `eval_guardrail.py` và `run_eval.py` đều cần `OPENAI_API_KEY` thật để chạy —
  chỉ `pytest` chạy được hoàn toàn offline.
- `export/notion_export.py` gọi Notion API tuần tự từng note (không batch) —
  đủ nhanh cho demo vài chục note, nếu về sau nhiều note nên cân nhắc song song
  hoá hoặc rate-limit backoff.
- `tools/_shared.py` dùng `requests` đồng bộ, timeout cố định 30s — nếu
  backend RAG chậm, có thể cần tăng timeout hoặc polling job riêng.
- Retrieval với câu hỏi ngắn/viết tắt (vd "PAIR framework") đôi khi miss chunk
  đúng dù nội dung có tồn tại — vấn đề chất lượng embedding/top_k phía `app/`,
  chưa tối ưu.
- Frontend (`frontend/`) hiện gọi API cũ (`/documents`, `/chat`, `doc_id`
  trong `sources`) — chưa khớp `app/` thật. Việc kết nối frontend sẽ làm ở
  bước sau, có confirm riêng.
