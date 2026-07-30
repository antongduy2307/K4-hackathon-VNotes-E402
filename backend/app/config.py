from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    chroma_persist_dir: str = "./storage/chroma_db"
    upload_dir: str = "./storage/uploads"
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 80
    retrieval_top_k: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
