---
name: clarify
track: core
kind: control
requires_env: []
inputs: [question, response_type, options]
outputs: [question, response_type, options, awaiting_user]
side_effect: false
---
# clarify

Returns a question to the user and pauses until the next user turn.
`response_type` is free text, yes/no, or a choice from `options`.

Use when the learner's question is too ambiguous to route (e.g. a deictic
reference like "chỗ đó"/"cái vừa nói" with no established referent), or before
any action that needs explicit confirmation. The document itself is never
ambiguous — it's fixed per session — so this is not for "which document."
