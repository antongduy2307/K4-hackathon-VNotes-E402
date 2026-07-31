# GitiNote RAG với ChromaDB

Backend FastAPI cho workflow:

```text
Upload PDF/PPTX
  -> Extract text theo trang
  -> Chunking
  -> Sentence-Transformers embedding
  -> ChromaDB PersistentClient
  -> Filter user_id + slide_id
  -> Retrieve Top-K
  -> LLM trả lời theo context
```

## 1. Cài đặt

Khuyến nghị Python 3.11 hoặc 3.12.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Điền `OPENAI_API_KEY` trong `.env` nếu muốn dùng endpoint sinh câu trả lời.

## 2. Chạy server

```bash
uvicorn app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

Lần chạy embedding đầu tiên sẽ tải model multilingual về máy.

## 3. Upload slide

```bash
curl -X POST "http://localhost:8000/api/v1/slides/upload" \
  -F "user_id=khoa" \
  -F "title=Machine Learning" \
  -F "file=@slides.pdf"
```

Output chính:

```json
{
  "slide_id": "uuid",
  "status": "ready",
  "chunk_count": 24,
  "message": "Tạo RAG thành công"
}
```

## 4. Retrieve context đúng slide

```bash
curl -X POST "http://localhost:8000/api/v1/rag/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "khoa",
    "slide_id": "SLIDE_ID",
    "question": "Gradient descent là gì?",
    "top_k": 5
  }'
```

Đây là interface Khoa có thể cung cấp cho phần Chat Agent của An.

## 5. RAG answer

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "khoa",
    "slide_id": "SLIDE_ID",
    "question": "Gradient descent là gì?",
    "top_k": 5
  }'
```

## 6. List và xóa slide

```bash
curl "http://localhost:8000/api/v1/slides?user_id=khoa"
```

```bash
curl -X DELETE \
  "http://localhost:8000/api/v1/slides/SLIDE_ID?user_id=khoa"
```

## 7. Test

```bash
pytest -q
```

## Lưu ý

- ChromaDB được lưu tại `data/chroma`.
- Metadata slide được lưu tại `data/slides.db`.
- File gốc được lưu tại `data/uploads/<slide_id>`.
- Query luôn lọc đồng thời `user_id` và `slide_id`.
- PDF/PPTX dạng ảnh chưa có text sẽ cần thêm OCR.
