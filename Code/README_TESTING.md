# Testing Alim Study Assistant

This guide explains how to run unit tests, smoke tests, and dry-run checks.

## 1. Purpose of Testing

- Unit tests check small pieces of code.
- Smoke tests check whether the app and main modules basically start.
- Dry-run tests check the retrieval and prompt pipeline without calling the real LLM.
- Integration tests may check Chroma or Ollama, but Ollama is optional for this MVP.

## 2. Activate the Environment

Run tests from the `Code` folder:

```bash
conda activate alim-study-assistant
```

## 3. Run Unit Tests

```bash
pytest
```

Verbose mode shows each test name:

```bash
pytest -v
```

## 4. Run a Specific Test File

```bash
pytest tests/test_grader.py
pytest tests/test_chunking.py
pytest tests/test_document_loaders.py
```

## 5. Run Smoke Test

```bash
python scripts/smoke_test.py
```

Expected result: clear `PASS` messages and exit code `0`.

## 6. Run Dry Run Pipeline

```bash
python scripts/dry_run_pipeline.py
```

This does not require Ollama and does not call the local LLM. It loads sample notes, chunks them, retrieves context, and builds prompts.

## 7. Optional Ollama Integration Test

No required Ollama integration test is included yet. When added later, it should be marked separately, for example:

```bash
pytest tests/test_ollama_integration.py -m integration
```

Ollama must be running and the configured model must be available for that optional test.

## 8. Test Data

Tests use sample data only. They do not require private school notes.

Sample fixtures live in:

```text
test_data/
```

## 9. What to Do When Tests Fail

- Environment not activated: run `conda activate alim-study-assistant`.
- Missing package: run `pip install -r requirements.txt`.
- Wrong working directory: run commands from `Code`.
- Missing sample files: check `test_data/`.
- Chroma temporary directory issue: rerun tests or delete the temporary test folder.
- Ollama not running: only optional Ollama integration tests should need it.

## 10. Testing Checklist Before Changing Code

```text
[ ] Conda environment is activated
[ ] App imports successfully
[ ] Unit tests pass
[ ] Smoke test passes
[ ] Dry run pipeline passes
[ ] Optional integration tests pass if Ollama is available
```

