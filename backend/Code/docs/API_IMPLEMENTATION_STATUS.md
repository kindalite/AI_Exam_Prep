# API Implementation Status

All Stage-1 Lovable backend routes are implemented under `src.api.main:app`.

| Endpoint | Route module | Framework-neutral service | Primary tests |
| --- | --- | --- | --- |
| `GET /health` | `src/api/routes/health.py` | `services/health_service.py` | `test_api_foundation.py`, `tests/api` |
| `GET /api/model/status` | `src/api/routes/health.py` | `health_service.py`, `model_providers.py` | `test_model_providers.py` |
| `GET /api/subjects` | `src/api/routes/subjects.py` | `subject_service.py` | `test_api_subject_reads.py` |
| `GET /api/subjects/{subject_id}` | `subjects.py` | `subject_service.py` | `test_api_subject_reads.py` |
| `GET .../learning-goals` | `subjects.py` | `subject_service.py` | `test_api_subject_reads.py` |
| `GET .../materials` | `subjects.py` | `material_service.py` | `test_api_subject_reads.py` |
| `POST /api/import/document` | `src/api/routes/materials.py` | `upload_service.py` | `test_api_document_import.py`, `test_upload_service.py` |
| `POST /api/chat` JSON/SSE | `src/api/routes/chat.py` | `chat_service.py` | `test_api_chat.py`, `test_api_chat_streaming.py` |
| `POST /api/quiz/generate` | `src/api/routes/study_tools.py` | `quiz_service.py` | `test_api_study_tools.py` |
| `POST /api/mock-exam/generate` | `study_tools.py` | `mock_exam_service.py` | `test_api_study_tools.py` |
| `POST /api/study-plan/generate` | `study_tools.py` | `study_plan_service.py` | `test_api_study_tools.py` |
| `POST /api/grade` | `study_tools.py` | `grading_service.py` | `test_api_study_tools.py` |
| `POST /api/feedback` | `src/api/routes/feedback.py` | `feedback_service.py` | `test_api_feedback_metadata.py` |

Cross-cutting contracts—OpenAPI inventory, snake_case, API errors, request IDs,
CORS, UTC timestamps, subject count, and response refs—are asserted in
`tests/api/`. The complete result is recorded in `LOVABLE_API_TEST_REPORT.md`.

Stage-1 boundaries remain deliberate: Supabase owns auth/chat transcripts;
Lovable owns real grades, planner CRUD, profile/display state, and localStorage;
Python owns AI inference, retrieval/indexes, generated practice, grading
evaluation, feedback, and non-authoritative AI provenance.
