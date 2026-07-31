---
name: note_capture
track: core
kind: deterministic_analysis
requires_env: []
inputs: []
outputs: [notes, excluded, kept_count, excluded_count]
side_effect: false
---
# note_capture

Filters the current session's Q&A history down to note-worthy items and
returns them structured — it does **not** write to Anki/Notion/Obsidian
itself. Export (`side_effect: local_file_write` or an external API call) is a
separate tool to add once the backend decides the export format; this tool
only decides *what* is worth keeping.

## Contract

Takes no model-facing arguments. `doc_id` (fixed for the session) and
`conversation_turns` are both injected by the orchestrator before the
underlying function runs. `conversation_turns` is a list of exchange records,
each shaped like:

```json
{"question": "...", "answer": "...", "tool_used": "rag_query", "sources": [{"page_number": 3}, {"page_number": 4}]}
```

**Important: the model must not author this list from memory.** The calling
orchestrator (`chat.py`'s tool-loop, or the future API layer) is responsible
for building the real `conversation_turns` mechanically from the transcript
already recorded per turn — not retyped by the model. This avoids the model
silently dropping or misremembering earlier answers when it "writes notes
from memory."

## What gets kept

An exchange is note-worthy only if **all** of:

- `tool_used == "rag_query"` — it was answered by looking up specific slide
  content. `rag_summary` exchanges (whole-document summaries) are always
  excluded — the note is about what the learner asked, not the deck.
- The question isn't a broad/whole-slide request. Exchanges whose question
  matches broad-scope markers (tóm tắt, tổng quan, khái quát, nói chung, toàn
  bộ, cả slide/tài liệu, overview, summary, ...) are excluded even if
  `rag_query` happened to answer them.

Everything else — off-topic exchanges, refusals, meta questions
(`tool_used` is null/`clarify`) — is excluded and reported under `excluded`
with a `reason` so the caller can show the learner what got skipped and why.

## Do not use when

- No `rag_query` exchange has happened yet this session (nothing to note).
- The learner asks to "note lại toàn bộ slide" — that's the exact broad
  request this tool is designed to exclude from notes; explain the scope
  limit instead of calling this tool.
