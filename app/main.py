from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Must run before anything below reads OPENAI_API_KEY from the process
# environment — Settings (app/core/config.py) has no such field, and
# agent.py's OpenAIProvider calls os.getenv() directly, so a .env file sitting
# next to the code does nothing on its own unless something loads it in.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.dependencies import get_slide_repository


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.ensure_directories()
    get_slide_repository().initialize()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    status_code = 404 if "không tìm thấy" in str(exc).lower() else 400
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


app.include_router(api_router, prefix=settings.api_prefix)
