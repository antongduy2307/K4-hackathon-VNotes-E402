from __future__ import annotations

from contextlib import asynccontextmanager

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
    # pdfjs (react-pdf) streams the PDF from GET /slides/{id}/file using HTTP
    # Range requests and inspects these response headers to manage that —
    # none of them are on the CORS default-exposed list, so without this the
    # browser silently hides them from JS on a cross-origin request (frontend
    # dev server on a different port than the API) and the PDF fails to load.
    expose_headers=["Content-Range", "Content-Length", "Accept-Ranges"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    status_code = 404 if "không tìm thấy" in str(exc).lower() else 400
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


app.include_router(api_router, prefix=settings.api_prefix)
