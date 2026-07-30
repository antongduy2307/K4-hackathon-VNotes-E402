"""Extract text from PDF, page by page. Tables are rendered as pipe-delimited
rows and appended after the page's prose text so the LLM still sees them as
readable rows instead of losing them entirely to extract_text()'s reading order.
"""
from dataclasses import dataclass

import pdfplumber


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str


def _format_table(table: list[list[str | None]]) -> str:
    rows = [" | ".join(cell.strip() if cell else "" for cell in row) for row in table]
    return "\n".join(rows)


def load_pdf_pages(pdf_path: str) -> list[PageText]:
    pages: list[PageText] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            prose = (page.extract_text() or "").strip()

            tables = page.extract_tables()
            table_blocks = [_format_table(t) for t in tables if t]

            parts = [p for p in [prose, *table_blocks] if p]
            pages.append(PageText(page_number=i, text="\n\n".join(parts)))
    return pages
