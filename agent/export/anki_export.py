"""Turn note_capture's filtered notes into a downloadable Anki .apkg deck.

Pure offline generation via genanki — no Anki desktop / AnkiConnect required,
so it works on any demo machine regardless of what's installed there.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import genanki

# Fixed IDs (not random per run) so re-exporting the same doc_id updates the
# existing Anki deck/note-type on import instead of creating duplicates.
_SEED = random.Random("vlearn-tutor-anki")
_MODEL_ID = _SEED.getrandbits(31)
_DECK_ID_BASE = _SEED.getrandbits(31)

_MODEL = genanki.Model(
    _MODEL_ID,
    "VLearn Tutor Q&A",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Front}}",
        "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
    }],
)


def _deck_id_for(doc_id: str) -> int:
    # Stable per doc_id, distinct from other docs, still fixed across runs.
    return abs(hash((_DECK_ID_BASE, doc_id))) % (2**31)


def _format_back(note: dict[str, Any]) -> str:
    answer = str(note.get("answer") or "")
    sources = note.get("sources") or []
    page_numbers = sorted({s["page_number"] for s in sources if "page_number" in s})
    if not page_numbers:
        return answer
    pages = ", ".join(str(p) for p in page_numbers)
    return f"{answer}<br><br><i>Nguồn: tr.{pages}</i>"


def build_anki_deck(notes: list[dict[str, Any]], *, doc_id: str, deck_name: str | None = None) -> genanki.Deck:
    if not notes:
        raise ValueError("No notes to export.")

    deck = genanki.Deck(_deck_id_for(doc_id), deck_name or f"VLearn - {doc_id}")
    for note in notes:
        deck.add_note(genanki.Note(
            model=_MODEL,
            fields=[str(note.get("question") or ""), _format_back(note)],
        ))
    return deck


def export_anki_to_file(notes: list[dict[str, Any]], *, doc_id: str, out_path: Path, deck_name: str | None = None) -> Path:
    deck = build_anki_deck(notes, doc_id=doc_id, deck_name=deck_name)
    genanki.Package(deck).write_to_file(str(out_path))
    return out_path
