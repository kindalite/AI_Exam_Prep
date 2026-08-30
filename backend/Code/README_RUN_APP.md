# AI_Exam_Prep / Alim Study Assistant

Alim Study Assistant is a local-first Streamlit app for high-school exam preparation. It supports per-user accounts, isolated notes and memory, multimodal study material, official syllabus fallback, timed quiz/exam modes, grading, and adaptive study suggestions.

## Conda Setup

The target environment path is:

```bash
~/anaconda3/envs/alim_study_assistant
```

Update or create it from the repository root:

```bash
conda env update -p ~/anaconda3/envs/alim_study_assistant -f environment.yml --prune
conda activate ~/anaconda3/envs/alim_study_assistant
python --version
python -m pip check
cd Code
python scripts/verify_environment.py
```

Fallback creation path:

```bash
conda create -p ~/anaconda3/envs/alim_study_assistant python=3.11
conda activate ~/anaconda3/envs/alim_study_assistant
cd /home/kindalite/AI_Exam_Prep/Code
python -m pip install -r requirements.txt
python scripts/verify_environment.py
```

Optional Linux packages for OCR/audio:

```bash
sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng tesseract-ocr-fra ffmpeg
```

## Local Model

The default local model is Ollama `gemma3:4b`.

```bash
ollama --version
ollama pull gemma3:4b
ollama run gemma3:4b
ollama list
python scripts/ensure_ollama_model.py
```

## Optional remote OpenAI-compatible/vLLM model

Generation can instead use a backend-only OpenAI-compatible endpoint. Embeddings
remain independently configured by `EMBEDDING_MODEL`.

```bash
MODEL_PROVIDER=vllm
REMOTE_LLM_BASE_URL=http://100.x.y.z:8000/v1
REMOTE_LLM_API_KEY=your-backend-only-token
REMOTE_LLM_MODEL=your-served-model
REMOTE_LLM_TIMEOUT_SECONDS=120
```

The address may be a private Tailscale address, but networking/Tailscale setup is
an operator concern. The browser never receives the endpoint token and the app
does not configure Tailscale or expose a public listener. Keep the FastAPI bind
address at `127.0.0.1` unless a separately secured deployment explicitly proxies
it.

## Run Streamlit

```bash
conda activate ~/anaconda3/envs/alim_study_assistant
cd /home/kindalite/AI_Exam_Prep/Code
streamlit run app.py
```

The app starts with local login/register. User data is stored under `Code/data/users/<user_id>/` and remains isolated per user.

## Run the local FastAPI backend

The API is a separate process and is intentionally bound to loopback:

```bash
conda activate ~/anaconda3/envs/alim_study_assistant
cd /home/kindalite/development/AI_Exam_Prep/Code
uvicorn src.api.main:app --host 127.0.0.1 --port 8001
```

Health is available at `http://127.0.0.1:8001/health`, Swagger at `/docs`, and
OpenAPI at `/openapi.json`. The supported local frontend origins are
`http://localhost:8080` and `http://127.0.0.1:8080`.
