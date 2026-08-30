# Stage-1 Chat Ownership and Limits

`POST /api/chat` supports JSON (`stream:false`) and SSE (`stream:true`). It combines
only the identified student's private subject and memory collections with the
approved canonical subject collections. SPF requests resolve to one selected
component or both component corpora. Material restrictions and learning-goal
scope are applied explicitly.

Supabase remains the authoritative owner of chat threads and messages. Python
does not write a duplicate transcript from this endpoint. The returned
`message_id` is a Python AI-result correlation ID; the frontend may map it to a
Supabase assistant-message ID.

Python stores a separate, per-student provenance row keyed by `thread_id` and
that Python `message_id`. It contains model/provider, source/material IDs,
retrieval counts, subject scope, and generation time only. It is explicitly
non-authoritative and contains neither the question nor the answer.

The current request sends only `thread_id` and the current `question`. Python
does not infer or fetch the Supabase transcript, so conversational continuity is
limited to already indexed, student-scoped performance/history memory. A future
contract must supply prior messages or a secure transcript bridge.
Provenance metadata is never treated as transcript or converted into memory.

Public-web retrieval is not performed with the private question in Stage 1.
Existing local privacy settings remain authoritative: private notes are never
sent to public search by default. Canonical indexed syllabus content remains
available through the shared subject collection.

SSE emits ordered `token` events followed by one `done` metadata event. Retrieval
and the first provider token are prepared before the streaming response starts,
so early failures can still return HTTP 503 `model_unavailable`. Failures after
the first token use a structured `error` event. Client disconnects close the
downstream iterator. Providers without streaming capability fail predictably;
the backend never disguises a buffered response as token streaming.

The normal suite uses a fake model. To run the opt-in live path:

```bash
RUN_LIVE_OLLAMA_CHAT=1 pytest -q tests/test_live_ollama_chat.py
```
