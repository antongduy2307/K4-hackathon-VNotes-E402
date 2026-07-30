from fastapi import FastAPI

from app.api.routes import chat, documents

app = FastAPI(title="VLearn RAG API")

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
