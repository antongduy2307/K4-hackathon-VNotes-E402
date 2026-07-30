---
name: rag_summary
track: core
kind: live_api
provider: vlearn-rag-backend
requires_env: [VLEARN_BACKEND_URL]
inputs: []
outputs: [summary]
side_effect: false
---
# rag_summary

Calls the RAG backend's `GET /documents/{doc_id}/summary` and returns a
full-document summary (already map-reduced by the backend if the document is
long) for the document open in this session.

`doc_id` is fixed for the whole session and is injected by the orchestrator,
never supplied by the model — this tool takes no model-facing arguments.

Use this once, right after the learner opens the document, to produce the
NotebookLM-style auto-summary before any question is asked. Also use it if the
learner explicitly asks to "tóm tắt tài liệu này" / "summarize this doc". Do
not call it again for a document already summarized earlier in the same
session unless the learner explicitly asks to re-summarize.
