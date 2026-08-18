# Code Handoff — Alim Study Assistant

This documentation describes the code under `AI_Exam_Prep/Code` as it exists
today. It is intended for developers maintaining the Streamlit app, extracting
an API backend, changing the RAG pipeline, or integrating the separate
`study-swiss-star` frontend.

Documentation only: this pack does not change runtime behavior.

## Read first

1. [`CODEBASE_ARCHITECTURE.md`](CODEBASE_ARCHITECTURE.md) — runtime shape,
   major layers, dependencies, and architectural boundaries.
2. [`MODULE_REFERENCE.md`](MODULE_REFERENCE.md) — responsibility and public
   entry points for every Python module and script group.
3. [`DATA_AND_USER_FLOWS.md`](DATA_AND_USER_FLOWS.md) — ingestion, chat,
   practice, authentication, persistence, and RAG flows.
4. [`OPERATIONS_AND_TESTING.md`](OPERATIONS_AND_TESTING.md) — configuration,
   startup, verification, tests, failure modes, and extension guidance.

## Who reads what

| Audience | Recommended files |
| --- | --- |
| New Python maintainer | All four files, in order |
| Frontend/API integrator | Architecture, data flows, and "HTTP API status" below |
| RAG/model developer | Architecture, module reference, data flows |
| Security/data reviewer | Architecture and data flows |
| Test/operations owner | Operations and testing |

## Existing focused guides

| File | Purpose |
| --- | --- |
| `../Code/README_RUN_APP.md` | Conda setup, Ollama model, and Streamlit launch |
| `../Code/README_TESTING.md` | Command list for tests, smoke tests, and dry runs |
| `../Code/README_USER_ACCOUNTS_AND_DATA.md` | Concise account and per-user storage overview |
| `../Code/README_MULTIMODAL_AND_WEB.md` | Concise multimodal/web overview |
| `../Code/ENVIRONMENT_SNAPSHOT.md` | Captured environment information |
| `../Code/PROGRESS_REPORT_2026-07-08.md` | Historical implementation progress; not the current contract |

## Repository scope

```text
AI_Exam_Prep/
├── Code/                    # executable application documented here
│   ├── app.py               # Streamlit composition root and page routing
│   ├── src/                 # domain, storage, RAG, model, and UI modules
│   ├── tests/               # unit and feature tests
│   ├── scripts/             # verification, smoke, migration, and dry runs
│   ├── data/                # local runtime state (partly generated)
│   └── vector_db/           # generated persistent Chroma data
├── learning_material/       # external course PDFs/DOCX files, by subject
├── codex_prompts/           # historical implementation prompts
└── preliminary_codex_prompts/
```

`codex_prompts/` and `preliminary_codex_prompts/` explain project history but
are not executable code or an authoritative runtime specification. Prefer the
implementation, tests, `.env.example`, and this documentation.

## Important architectural fact: no HTTP backend yet

The Python code is a local Streamlit monolith. `app.py` imports `src/*` and
calls Python functions in-process. There is currently:

- no FastAPI application;
- no REST/SSE endpoint;
- no request/response schema layer;
- no CORS or bearer-token verification;
- no independently deployable backend server.

The API described in `study-swiss-star/docs/API_EXPECTATIONS.md` is a planned
integration contract, not an implemented interface in this directory. An API
adapter should call the service functions documented here rather than copy
their business logic into route handlers.

## Current implementation boundaries to understand

- Authentication is local JSON-file authentication, not Supabase.
- Ollama `gemma3:4b` is the expected text and vision model.
- Persistent retrieval uses Chroma when available; code falls back to an
  in-memory store in some paths.
- `render_chat()` currently uses the shared subject collection through
  `retrieve_study_context()`. User-scoped indexing/retrieval exists separately
  (`build_user_subject_index`, `retrieve_for_user_subject`, and
  `rag_memory_indexer.py`) but is not the path used by that chat screen.
- Chat history/media and generated practice can be stored per user; the legacy
  performance and feedback defaults are shared files unless callers/config
  provide user-specific paths.
- Optional OCR, vision, audio, web, and PDF-rendering dependencies degrade with
  warnings rather than making the whole app fail.

## Source-of-truth order

When documentation and behavior disagree, use this order:

1. Tests that express an intentional invariant.
2. Current code in `app.py` and `src/`.
3. `.env.example`, `requirements.txt`, and `environment.yml`.
4. This documentation pack and focused READMEs.
5. Historical progress reports and Codex prompts.
