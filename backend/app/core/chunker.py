"""Split page text into overlapping token-based chunks, keeping page provenance."""
from dataclasses import dataclass

import tiktoken

from app.core.pdf_loader import PageText

_ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    page_start: int
    page_end: int


def _tokenize(text: str) -> list[int]:
    return _ENCODING.encode(text)


def _detokenize(tokens: list[int]) -> str:
    return _ENCODING.decode(tokens)


def chunk_pages(
    doc_id: str,
    pages: list[PageText],
    chunk_size_tokens: int = 500,
    overlap_tokens: int = 80,
) -> list[Chunk]:
    """Flatten pages into one token stream (tracking page boundaries by token offset),
    then slide a window over it so a chunk can span page breaks without losing context.
    """
    token_stream: list[int] = []
    token_page_map: list[int] = []  # page number owning each token

    for page in pages:
        if not page.text:
            continue
        tokens = _tokenize(page.text)
        token_stream.extend(tokens)
        token_page_map.extend([page.page_number] * len(tokens))

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    step = max(chunk_size_tokens - overlap_tokens, 1)

    while start < len(token_stream):
        end = min(start + chunk_size_tokens, len(token_stream))
        window_tokens = token_stream[start:end]
        window_pages = token_page_map[start:end]

        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}::chunk_{idx}",
                text=_detokenize(window_tokens),
                page_start=window_pages[0],
                page_end=window_pages[-1],
            )
        )

        idx += 1
        if end == len(token_stream):
            break
        start += step

    return chunks
