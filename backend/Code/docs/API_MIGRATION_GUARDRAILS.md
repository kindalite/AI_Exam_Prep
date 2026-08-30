# API Migration Guardrails

These invariants apply to every later compatibility work package unless a
later prompt explicitly replaces one.

1. Keep `app.py` and the Streamlit application working throughout migration.
   The FastAPI entry point belongs at `src/api/main.py`; do not create an
   `app/` package that conflicts with `app.py`.
2. Match the Lovable contract with `snake_case` JSON and thin route handlers.
   Put orchestration in framework-neutral services and reuse existing RAG,
   generation, grading, storage, prompt, and model code.
3. Return exactly 15 public top-level subjects. Keep `spf_biology` and
   `spf_chemistry` as nested component/corpus IDs and preserve legacy
   Streamlit aliases during migration.
4. Treat `X-Student-Id` as the Stage 1 identity bridge only after sanitizing it
   with `user_data_paths` helpers. Raw identity must never form paths,
   filenames, Chroma collections, filters, or log fields.
5. All private material ingestion, indexing, retrieval, feedback, generated
   artifacts, and AI metadata must be user-scoped. Never expose the current
   shared `retrieve_study_context()` chat path as a multi-user API.
6. Supabase owns authentication and chat transcripts in Stage 1. Python
   returns AI results/source metadata but must not become a second transcript
   authority.
7. Frontend/localStorage owns real grades, averages, colours, 0.5 grade display
   rounding, planner CRUD/state, profile/prototype state, the static UI card
   model, and SPF combined-grade display logic.
8. Python owns AI inference, RAG, document parsing/indexing, learning goals,
   criteria, AI study tools, exact grading evaluation, feedback, sources, AI
   metadata, and model/provider health.
9. Compute API grades from `points_achieved / maximum_points * 5 + 1`, validate
   the point range, clamp to 1–6, and do not apply the frontend's 0.5 display
   rounding.
10. Keep private text out of public-web queries by default. Preserve explicit
    web permission, trusted-source policy, and local-first source priority.
11. Preserve hidden solutions until the grading/submission contract permits
    reveal. Errors and partial responses must never leak them.
12. Preserve graceful degradation for optional OCR, image, audio, PDF, web,
    embedding, and vector dependencies. Return actionable structured warnings
    or errors without exposing private paths/content.
13. Bind local development to `127.0.0.1` by default. Browser code must never
    call Chroma, Ollama, vLLM, or another model provider directly.
14. Use dependency injection/fakes for provider, retrieval, and storage tests.
    Tests must not touch the checkout's persistent `data/` or `vector_db/`.
15. After each work package, run focused tests first, then the full regression
    suite and the relevant offline smoke/dry run. Do not begin the next prompt
    unless the current package's required checks pass.
