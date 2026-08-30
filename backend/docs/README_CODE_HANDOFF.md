# Code Handoff — Alim Study Assistant

This documentation describes the code under `AI_Exam_Prep/Code` as it exists
today. It is intended for developers maintaining the Streamlit app and FastAPI
backend, changing the RAG pipeline, or integrating the separate
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
| `../Code/README_RUN_API.md` | FastAPI startup, provider setup, and troubleshooting |
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

## HTTP backend migration status

The Streamlit app remains available, and the completed Stage-1 FastAPI adapter
runs beside it from `src/api/main.py`. Health/model, subject reads, document
import, chat JSON/SSE, quiz, mock exam, study plan, grading, and feedback routes
call framework-neutral services. The generated contract is
`Code/docs/openapi.json`; test results are in `Code/docs/LOVABLE_API_TEST_REPORT.md`.

## Current implementation boundaries to understand

- Streamlit retains local JSON login; the API accepts sanitized `X-Student-Id`
  behind frontend/Supabase auth in Stage 1.
- Generation supports local Ollama and remote OpenAI-compatible/vLLM providers;
  embeddings remain independently configured.
- Persistent retrieval uses Chroma when available; code falls back to an
  in-memory store in some paths.
- API chat uses isolated user collections plus approved canonical collections.
  Supabase owns its transcript; Python stores metadata-only provenance.
- The former 12-versus-15 subject mismatch is resolved in the registry. The
  public model has 15 top-level IDs; SPF Biology/Chemistry are nested component
  corpora behind a virtual combined parent.
- Generated practice, grading reports, API feedback, and AI provenance are
  stored per user. Legacy Streamlit feedback/performance helpers remain for
  compatibility and are not used by the API routes.
- Optional OCR, vision, audio, web, and PDF-rendering dependencies degrade with
  warnings rather than making the whole app fail.

## Source-of-truth order

When documentation and behavior disagree, use this order:

1. Tests that express an intentional invariant.
2. Current code in `app.py` and `src/`.
3. `.env.example`, `requirements.txt`, and `environment.yml`.
4. This documentation pack and focused READMEs.
5. Historical progress reports and Codex prompts.
