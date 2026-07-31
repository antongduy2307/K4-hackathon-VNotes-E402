from __future__ import annotations

import sys
from pathlib import Path

from anyio import to_thread

from app.core.exceptions import SlideNotFoundError, SlideNotReadyError
from app.models.domain import RetrievedChunk
from app.repositories.slide_repository import SlideRepository
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = REPO_ROOT / "agent"
for path in (str(REPO_ROOT), str(AGENT_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


class RAGService:
    def __init__(
        self,
        *,
        repository: SlideRepository,
        embedder: EmbeddingService,
        chroma: ChromaService,
        default_top_k: int,
        max_top_k: int,
    ) -> None:
        self.repository = repository
        self.embedder = embedder
        self.chroma = chroma
        self.default_top_k = default_top_k
        self.max_top_k = max_top_k

    async def retrieve(
        self,
        *,
        user_id: str,
        slide_id: str,
        question: str = "",
        top_k: int | None,
    ) -> list[RetrievedChunk]:
        slide = self.repository.get_owned(slide_id, user_id)
        if slide is None:
            raise SlideNotFoundError("Không tìm thấy slide của người dùng")
        if slide.status != "ready":
            raise SlideNotReadyError(f"Slide đang ở trạng thái: {slide.status}")

        if question and question.strip():
            limit = min(top_k or self.default_top_k, self.max_top_k)
            return await to_thread.run_sync(
                self._retrieve_with_question_sync,
                user_id,
                slide_id,
                question,
                limit,
            )

        limit = min(top_k or self.default_top_k, self.max_top_k)
        return await to_thread.run_sync(
            self._retrieve_sync,
            user_id,
            slide_id,
            limit,
        )

    async def retrieve_all_chunks(
        self,
        *,
        user_id: str,
        slide_id: str,
    ) -> list[RetrievedChunk]:
        slide = self.repository.get_owned(slide_id, user_id)
        if slide is None:
            raise SlideNotFoundError("Không tìm thấy slide của người dùng")
        if slide.status != "ready":
            raise SlideNotReadyError(f"Slide đang ở trạng thái: {slide.status}")

        return await to_thread.run_sync(
            self._retrieve_all_chunks_sync,
            user_id,
            slide_id,
        )

    def _retrieve_sync(
        self,
        user_id: str,
        slide_id: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        return self.chroma.get_slide_chunks(
            user_id=user_id,
            slide_id=slide_id,
            top_k=top_k,
        )

    def _retrieve_with_question_sync(
        self,
        user_id: str,
        slide_id: str,
        question: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        query_embedding = self.embedder.encode([question])[0]
        return self.chroma.search(
            user_id=user_id,
            slide_id=slide_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )

    def _retrieve_all_chunks_sync(
        self,
        user_id: str,
        slide_id: str,
    ) -> list[RetrievedChunk]:
        return self.chroma.get_slide_chunks(
            user_id=user_id,
            slide_id=slide_id,
            top_k=None,
        )

    async def answer(
        self,
        *,
        user_id: str,
        slide_id: str,
        question: str = "",
        top_k: int | None = None,
    ) -> tuple[str, list[RetrievedChunk]]:
        if question and question.strip():
            sources = await self.retrieve(
                user_id=user_id,
                slide_id=slide_id,
                question=question,
                top_k=top_k,
            )
        else:
            sources = await self.retrieve_all_chunks(
                user_id=user_id,
                slide_id=slide_id,
            )

        if not sources:
            return "Slide này hiện chưa có nội dung để trả lời.", sources

        try:
            answer = await to_thread.run_sync(
                self._answer_with_agent,
                question or "Tóm tắt nội dung slide này bằng tiếng Việt, ngắn gọn, rõ ràng, có thể dùng cho học tập.",
                sources,
                user_id,
                slide_id,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
        return answer, sources

    async def summarize(
        self,
        *,
        user_id: str,
        slide_id: str,
    ) -> tuple[str, list[RetrievedChunk]]:
        return await self.answer(user_id=user_id, slide_id=slide_id)

    def _answer_with_agent(
        self,
        question: str,
        sources: list[RetrievedChunk],
        user_id: str,
        slide_id: str,
    ) -> str:
        import importlib.util
        import sys

        agent_module_path = AGENT_ROOT / "agent.py"
        spec = importlib.util.spec_from_file_location("agent_module", agent_module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        VLearnAgent = module.VLearnAgent

        provider_path = AGENT_ROOT / "providers" / "openai_provider.py"
        provider_spec = importlib.util.spec_from_file_location("agent_providers_openai", provider_path)
        provider_module = importlib.util.module_from_spec(provider_spec)
        sys.modules[provider_spec.name] = provider_module
        assert provider_spec.loader is not None
        provider_spec.loader.exec_module(provider_module)
        OpenAIProvider = provider_module.OpenAIProvider

        context = "\n\n".join(
            f"[Nguồn {index} | Trang {source.page_number}]\n{source.text}"
            for index, source in enumerate(sources, start=1)
        )

        agent = VLearnAgent(
            OpenAIProvider(),
            system_prompt=(
                "Bạn là trợ lý học tập. Chỉ trả lời dựa trên CONTEXT được cung cấp. "
                "Nếu context không đủ, nói rõ rằng slide không có đủ thông tin. "
                "Không tự tạo dữ kiện. Khi sử dụng thông tin, ghi nguồn theo dạng [Trang X]."
            ),
            model="gpt-4o-mini",
            session={"user_id": user_id, "slide_id": slide_id},
        )

        result = agent.run(
            [
                {
                    "role": "user",
                    "content": (
                        "CONTEXT:\n"
                        f"{context}\n\n"
                        "CÂU HỎI:\n"
                        f"{question}"
                    ),
                }
            ]
        )
        return (result.text or "Không tạo được câu trả lời.").strip()
