# Run Alim Study Assistant

This guide explains how to install, configure, and start the local web app from a Linux shell or VS Code Remote-SSH terminal.

## 1. What You Need Before Starting

- Linux shell or VS Code Remote-SSH terminal.
- Conda installed.
- Git installed.
- Ollama installed separately.
- A local DeepSeek Distilled model pulled in Ollama.
- This repository opened on the local or remote machine.

Ollama is a separate local runtime. It is not installed by Python packages.

## 2. Create the Conda Environment

From the `Code` folder:

```bash
conda env create -f environment.yml
conda activate alim-study-assistant
```

The first command creates the Python environment. The second command activates it so Python uses the app's packages.

If `environment.yml` is not available, use this fallback:

```bash
conda create -n alim-study-assistant python=3.11
conda activate alim-study-assistant
pip install -r requirements.txt
```

## 3. Install or Check Ollama

Check that Ollama is installed:

```bash
ollama --version
ollama list
```

If these commands fail, install Ollama first from the official Ollama instructions for your system.

## 4. Pull or Confirm the Local Model

Choose a model that fits your machine and stays within roughly 16 GB VRAM occupancy.

```bash
ollama pull <deepseek-distilled-model-name>
```

Then confirm it is available:

```bash
ollama list
```

## 5. Configure `.env`

Create a private local config file:

```bash
cp .env.example .env
```

Example content:

```env
MODEL_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=<deepseek-distilled-model-name>
CHROMA_DB_DIR=vector_db
```

Do not commit `.env` to GitHub because it is local machine configuration.

## 6. Start the App

From the `Code` folder:

```bash
streamlit run app.py
```

Streamlit should print a local URL similar to:

```text
http://localhost:8501
```

Open that URL in your browser.

## 7. Add Subject Material

Put school material in the subject folders:

```text
data/subjects/<subject_key>/notes/
data/subjects/<subject_key>/syllabus/
data/subjects/<subject_key>/criteria/
```

Supported formats:

- DOCX
- PDF
- MD
- TXT

## 8. Build or Rebuild Subject Database

Use the app:

1. Select the subject in the sidebar.
2. Open `Notes Ingestion`.
3. Upload files or place files in the subject folder.
4. Click `Build or rebuild subject database`.

This creates or refreshes the local Chroma subject collection under `vector_db/`.

## 9. Troubleshooting

- Conda environment not activated: run `conda activate alim-study-assistant`.
- Package import error: run `pip install -r requirements.txt`.
- Ollama not running: start Ollama and try `ollama list`.
- Model not found: check `OLLAMA_MODEL` in `.env` and run `ollama list`.
- No subject notes found: add files to the subject `notes/`, `syllabus/`, or `criteria/` folders.
- Chroma/vector DB missing: rebuild the subject database from the app.
- Port already in use: run Streamlit on another port:

```bash
streamlit run app.py --server.port 8502
```

## 10. Safety and Privacy Notes

This is a local educational app. It is not an official grading system and should not be used for medical, legal, or other high-stakes advice.

Keep private notes, `.env`, and vector database files out of GitHub.

