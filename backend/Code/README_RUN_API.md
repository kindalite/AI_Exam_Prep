# Run the Alim FastAPI Backend

## Start

```bash
conda activate /home/kindalite/anaconda3/envs/alim_study_assistant
cd /home/kindalite/development/AI_Exam_Prep/Code
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001
```

The API is intentionally loopback-only by default.

- Base URL: `http://127.0.0.1:8001`
- Health: `http://127.0.0.1:8001/health`
- Model status: `http://127.0.0.1:8001/api/model/status`
- Swagger: `http://127.0.0.1:8001/docs`
- OpenAPI: `http://127.0.0.1:8001/openapi.json`

Verify from another terminal:

```bash
curl -fsS http://127.0.0.1:8001/health
curl -fsS http://127.0.0.1:8001/api/model/status
```

User-scoped routes require `X-Student-Id`:

```bash
curl -fsS -H 'X-Student-Id: local-student' \
  http://127.0.0.1:8001/api/subjects/history/materials
```

## Provider configuration

The default is local Ollama `gemma3:4b`. To use a backend-only
OpenAI-compatible/vLLM server, set `MODEL_PROVIDER=openai_compatible` or
`MODEL_PROVIDER=vllm` plus `REMOTE_LLM_BASE_URL`, `REMOTE_LLM_MODEL`, and the
optional `REMOTE_LLM_API_KEY`. Never put the API key in browser configuration.

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| Browser CORS rejection | Use frontend origin `http://localhost:8080` or `http://127.0.0.1:8080`; do not change the API to a public wildcard. |
| `student_identity_required` | Send a non-empty `X-Student-Id` on upload, chat, generation, grading, and feedback requests. |
| `model_unavailable` / degraded model status | For Ollama, start it and pull the configured model. For remote mode, verify the private URL, model name, API key, and network route. |
| Empty retrieval/source list | Import material for the same student/subject and confirm the material status is `indexed`; SPF uploads require a component. |
| `parse_failed` | Verify file content matches its supported extension/MIME; inspect the student's material manifest for the `needs_review` warning. |
| `unsupported_media_type` / HTTP 415 | Upload PDF, DOCX, MD, TXT, PNG, JPEG, or SVG with a matching MIME type. |
| Remote model unreachable | Check the backend host/Tailscale route and `REMOTE_LLM_BASE_URL`; the frontend never contacts the remote model directly. |
| SSE stops with `event: error` | Treat the partial answer as incomplete, show the event error, and allow retry. |

## Verification

```bash
python scripts/verify_environment.py
python -m pytest -q tests/api
python scripts/api_smoke_test.py
python scripts/dry_run_lovable_contract.py
```
