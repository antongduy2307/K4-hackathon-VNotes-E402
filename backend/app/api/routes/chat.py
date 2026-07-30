from fastapi import APIRouter

from app.core.rag import answer_question
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def ask(request: ChatRequest) -> ChatResponse:
    result = answer_question(request.doc_id, request.question)
    return ChatResponse(**result)
