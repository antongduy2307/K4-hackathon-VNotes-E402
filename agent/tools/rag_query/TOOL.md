---
name: rag_query
track: core
kind: live_api
provider: vlearn-rag-backend
requires_env: [VLEARN_BACKEND_URL]
inputs: [query]
outputs: [answer, sources]
side_effect: false
---
# rag_query

Calls the RAG backend's `POST /chat` with `{doc_id, question}` and returns a
grounded answer plus source page ranges for the document open in this
session.

`doc_id` is fixed for the whole session (one document per session — it never
changes mid-conversation) and is injected by the orchestrator
(`agent.py`/`chat.py`), never supplied by the model. The model only ever
passes `query`.

The `answer` field is already grounded by the backend (it refuses or says the
document doesn't cover something when retrieval is empty); still treat
`sources` as citations to surface to the learner, not the whole truth.
