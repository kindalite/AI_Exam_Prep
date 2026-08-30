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

## Run

```bash
conda activate ~/anaconda3/envs/alim_study_assistant
cd /home/kindalite/AI_Exam_Prep/Code
streamlit run app.py
```

The app starts with local login/register. User data is stored under `Code/data/users/<user_id>/` and remains isolated per user.
