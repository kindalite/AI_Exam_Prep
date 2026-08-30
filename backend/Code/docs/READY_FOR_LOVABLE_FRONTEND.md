# Ready for Lovable Frontend

- Base URL: `http://127.0.0.1:8001`.
- FastAPI import: `src.api.main:app`.
- Allowed origins: `http://localhost:8080`, `http://127.0.0.1:8080`.
- Send `X-Student-Id` on every user-scoped operation. It is the Stage-1 local
  identity bridge, not a replacement for Supabase authentication.
- Check `/health` for backend/dependency state and `/api/model/status` for the
  selected local/remote generation provider. Model outage degrades AI routes;
  process health and documentation remain available.
- Chat supports unchanged JSON with `stream:false` and SSE `token`, `done`, and
  post-start `error` events with `stream:true`.
- Implemented: health/model status; subject catalogue/detail/goals/materials;
  document import; chat JSON/SSE; quiz; mock exam; study-plan proposal; exact AI
  grading; feedback.
- Supabase remains authoritative for authentication and chat threads/messages.
  Python does not store an authoritative transcript. The frontend remains
  authoritative for real grades, averages, planner CRUD, profile/display state,
  colours, and localStorage.
- Python stores user-scoped material/index data, generated practice and hidden
  solutions, AI grading reports, feedback, and metadata-only AI provenance.
- Conversation requests contain only the current question/thread ID. Continuity
  is limited to already indexed student memory until the frontend supplies prior
  messages or a secure transcript bridge.
- OpenAPI file: `Code/docs/openapi.json`; live spec: `/openapi.json`; Swagger:
  `/docs`.
