# VLearn Tutor Agent

Đứng độc lập với `backend/` (RAG service) — chỉ gọi qua HTTP, không import code
của `backend/`.

Kiến trúc phiên: **mỗi tài liệu là một phiên (session) riêng biệt, với lịch sử
hội thoại riêng biệt** — không có chuyện nhiều tài liệu dùng chung một phiên,
và `doc_id` không bao giờ đổi giữa hội thoại. Vì vậy `doc_id` là tham số
session (do orchestrator gắn cứng khi phiên bắt đầu), KHÔNG phải thứ model tự
đọc/suy ra từ tin nhắn — loại bỏ hẳn lớp lỗi "model đoán sai/quên doc_id".
Model chỉ gọi `rag_query(query)`, `rag_summary()`, `note_capture()` — không đối
số định danh tài liệu; `apply_session_args()` (`tools/__init__.py`) tự điền
`doc_id` (và `conversation_turns` cho `note_capture`) trước khi hàm thật chạy.

Giao thức: agent gọi RAG qua `POST /chat` hoặc `GET /documents/{doc_id}/summary`,
rồi tổng hợp câu trả lời cuối cùng (trích trang nguồn) để gửi lại người dùng.

Cấu trúc mượn nguyên khung đã chạy được trong `example/` (agent.py / chat.py /
tools contract / run_eval.py) — chỉ thay tool và system prompt cho đúng domain
VLearn.

## Cấu trúc

```
agent/
  agent.py           một vòng gọi model + tool (dùng cho eval routing)
  chat.py            vòng lặp đầy đủ: gọi tool -> feed kết quả lại model -> câu trả lời cuối, có transcript
  run_eval.py         eval độ chính xác routing tool + args (giống backend, tách file riêng)
  eval_guardrail.py   eval hành vi cuối: chống prompt-injection cấy trong tài liệu, chống bịa khi RAG rỗng
  tools/
    rag_query/        gọi POST {VLEARN_BACKEND_URL}/chat (doc_id do session gắn)
    rag_summary/       gọi GET {VLEARN_BACKEND_URL}/documents/{doc_id}/summary (doc_id do session gắn)
    note_capture/       lọc lịch sử hội thoại thành note (loại off-topic + tóm tắt toàn slide)
    clarify/            hỏi lại, dừng chờ user (không gọi RAG)
  artifacts/
    system_prompt.md   routing rules + guardrail + trust boundary
    tools.yaml          khai báo tool cho model (OpenAI function-calling schema — không có doc_id)
  data/
    eval_base.json      case routing/clarify/out-of-scope/multi-turn (trong CÙNG 1 phiên/tài liệu)
    eval_guardrail.json case guardrail (mock tool result, chấm câu trả lời cuối)
  export/
    anki_export.py      note_capture output -> file .apkg (genanki, offline, không cần Anki app)
    notion_export.py     note_capture output -> ý chính, append vào 1 trang Notion có sẵn (Notion API thật)
    obsidian_export.py   note_capture output -> file .md (frontmatter + ý chính + Q&A), không API/auth
  export_api.py        FastAPI: 3 endpoint cho nút "Lưu Anki"/"Lưu Notion"/"Lưu Obsidian" trên UI — KHÔNG qua agent/LLM
  tests/               test không cần API key (mock HTTP call tới backend/Notion)
```

## Setup

```bash
cd agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env   # điền OPENAI_API_KEY; VLEARN_BACKEND_URL trỏ tới backend đang chạy
```

## Chạy thử (cần backend đang chạy ở VLEARN_BACKEND_URL)

```bash
python chat.py --version v0 --doc-id <doc_id thật đã ingest ở backend>
```

`--doc-id` cố định cho suốt phiên chat này (đúng 1 tài liệu). Gõ câu hỏi bình
thường, không cần tự chèn context — ví dụ: "Tóm tắt tài liệu này giúp mình."
Transcript lưu ở `transcripts/*.transcript.json`.

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

`note_capture` chỉ lọc + trả note có cấu trúc. Export ra Anki/Notion là hành
động người dùng bấm nút trên UI, gọi thẳng `export_api.py` với đúng list note
đó — không để model tự quyết định ghi ra hệ thống ngoài.

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
- `POST /export/obsidian` — cùng body → trả file `.md` tải về (frontmatter
  `doc_id`/`created`/`tags` + mục "Ý chính" tổng hợp giống Notion + mục "Chi
  tiết câu hỏi & trả lời" đầy đủ Q&A kèm trích trang). Không API, không auth,
  không network call ngoài (trừ 1 lần gọi OpenAI để tổng hợp ý chính, cùng
  fallback như Notion nếu thiếu key). User tự kéo file vào vault Obsidian của
  họ — đây là cách export ít setup nhất trong 3 cái.

## Test không cần API key

```bash
pytest
```
Mock HTTP call bằng `unittest.mock.patch`, kiểm tra: tool registry khớp
`tools.yaml`, `eval_base.json`/`eval_guardrail.json` đúng shape, `rag_query`/
`rag_summary` không bao giờ raise exception (luôn trả dict lỗi) khi backend
sập, logic lọc của `note_capture` (giữ đúng câu hỏi chi tiết, loại whole-doc
summary + off-topic), `anki_export` sinh file `.apkg` hợp lệ (zip thật, deck_id
ổn định theo `doc_id`), `notion_export` gọi đúng payload và không raise khi
Notion API lỗi/thiếu config.

## Nhật ký eval thật đã chạy (tham khảo cách điều chỉnh prompt từ kết quả)

- v0: 8/11 case routing pass (72.7%) — do lúc đó `doc_id` còn được nhúng vào
  text mỗi lượt (`NGỮ CẢNH: doc_id=...`), model xử lý multi-turn không ổn định.
- v1: sau khi vá system_prompt (rule carryover/không-gọi-lại-summary) -> 10/11
  (90.9%), nhưng vẫn còn 1 case nhạy cảm với cách eval dồn nhiều turn vào 1
  message.
- Kiến trúc hiện tại (tài liệu này) loại bỏ hẳn nguyên nhân gốc: `doc_id`
  không còn là thứ model phải đọc/carry/suy đoán từ text nữa — nó là hằng số
  của phiên, do orchestrator gắn. Cần chạy lại `run_eval.py`/`eval_guardrail.py`
  với bộ case mới để có số liệu mới nhất (chưa chạy tại thời điểm viết dòng
  này — chạy `python run_eval.py --version v2` để lấy kết quả).

## Việc còn lại / TODO cho version sau

- `eval_guardrail.py` và `run_eval.py` đều cần `OPENAI_API_KEY` thật để chạy —
  chỉ `pytest` chạy được hoàn toàn offline.
- Obsidian export chưa làm — dự kiến sau MVP, chỉ ghi `.md` vào vault, không
  cần API/auth.
- `export/notion_export.py` gọi Notion API tuần tự từng note (không batch) —
  đủ nhanh cho demo vài chục note, nếu về sau nhiều note nên cân nhắc song song
  hoá hoặc rate-limit backoff.
- `tools/_shared.py` dùng `requests` đồng bộ, timeout cố định 30s — nếu
  backend RAG chậm (map-reduce summary dài), có thể cần tăng timeout hoặc
  polling job riêng.
- Backend/API thật cần đảm bảo mỗi phiên chat (mỗi tài liệu) có `doc_id` cố
  định được truyền vào lúc khởi tạo agent (giống `--doc-id` của `chat.py`),
  không phải lấy từ nội dung tin nhắn.
