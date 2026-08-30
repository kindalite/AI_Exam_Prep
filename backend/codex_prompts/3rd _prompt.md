# Codex Prompt 7: Conda Environment, Per-User Memory/RAG Isolation, 128K Token Budget, Timed Quiz/Exam Modes, UI/Docs Upgrade

## Current Project Context

You are working on **Alim Study Assistant**, a locally hosted Streamlit exam-preparation AI web app. The current repository uses a modular Python architecture under `Code/` and builds on the previous prompt:

```text
06_codex_gemma3_multimodal_web_adaptive_rag_prompt_comprehensive.md
```

That previous prompt already required:

- local-first Streamlit app behavior;
- Ollama as the intelligence layer;
- `gemma3:4b` as the default local model;
- multimodal OneNote-PDF ingestion;
- chatbot image/audio input;
- official Kantonsschule Alpenquai/Lucerne syllabus retrieval;
- optional public web retrieval;
- adaptive learning from performance history;
- extensive unit, feature, smoke, and dry-run tests.

This prompt is the **next implementation prompt**. Do not remove or weaken the previous requirements. Extend the current codebase carefully.

## Non-Negotiable Rule

Do **not** rewrite the whole app from scratch. Inspect the existing repository first, preserve useful working code, keep the project beginner-readable, and implement the new features incrementally.

Before making changes, run from the repository root or from `Code/` as appropriate:

```bash
pytest
python scripts/smoke_test.py
python scripts/dry_run_pipeline.py
```

If these fail before your changes, record the exact failure in your notes and fix only what is necessary before continuing.

---

# New Requirements to Implement

Implement the following new requirements on top of all previous prompts.

## 1. Update the Conda Environment at the Exact Target Path

The target conda environment path on the real machine is:

```text
~/anaconda3/envs/alim_study_assistant
```

This path is authoritative.

The repository may currently contain an environment name such as `alim-study-assistant` with hyphens. Update documentation and environment metadata so the app consistently supports the target environment:

```text
alim_study_assistant
```

### Required behavior

- Update `environment.yml` and `requirements.txt` according to the current code requirements.
- Keep package versions pinned where practical.
- Ensure Python version compatibility. Default target: Python 3.11 unless the current working code truly requires a different version.
- Do not invent impossible package versions. Use versions that can actually install.
- Keep `requirements.txt` and `environment.yml` consistent.
- Add a generated lock/snapshot file after successful installation, for example:

```text
requirements.lock.txt
ENVIRONMENT_SNAPSHOT.md
```

The snapshot should record:

- Python version;
- conda environment path;
- important package versions;
- Ollama model configuration;
- date/time of verification;
- exact commands used.

### Required environment commands to document and verify

Codex must update the docs so a user can run:

```bash
conda env update -p ~/anaconda3/envs/alim_study_assistant -f environment.yml --prune
conda activate ~/anaconda3/envs/alim_study_assistant
python --version
python -m pip check
python scripts/verify_environment.py
```

Also document the fallback creation path:

```bash
conda create -p ~/anaconda3/envs/alim_study_assistant python=3.11
conda activate ~/anaconda3/envs/alim_study_assistant
python -m pip install -r requirements.txt
python scripts/verify_environment.py
```

### Add script: `scripts/verify_environment.py`

Create a beginner-readable environment verification script that checks:

- Python version;
- current executable path contains `alim_study_assistant` or clearly warns if not;
- core packages import correctly;
- optional packages import where installed;
- Ollama Python package is installed;
- `.env.example` has `OLLAMA_MODEL=gemma3:4b`;
- the app can import without syntax errors.

It must print clear `PASS`, `WARN`, and `FAIL` lines. It must exit non-zero only for required failures.

---

## 2. Store All Chat Prompts, Media Inputs, Generated Practice, Answers, and Reports for RAG

The app must persist all important learning interactions locally so the RAG system can retrieve them later.

This includes:

- all text prompts/questions typed into the chatbot;
- image uploads used in the chatbot;
- audio uploads or recordings used in the chatbot;
- audio transcripts;
- image OCR text;
- image/page descriptions;
- generated quiz question sets;
- generated exam question sets;
- hidden solution sets;
- submitted student answers;
- grading results;
- performance reports;
- study recommendations;
- chat answers produced by the model;
- sources retrieved for each answer.

### Required storage structure

Use a clear local folder structure like this:

```text
data/
  users/
    <user_id>/
      profile.json
      subjects/
        <subject_key>/
          notes/
          syllabus/
          criteria/
          learning_goals.md
          exam_criteria.md
      chat_history/
        sessions.jsonl
        messages.jsonl
      chat_media/
        images/
        audio/
        transcripts/
        image_descriptions/
      generated_practice/
        quizzes/
        exams/
        solution_sets/
      attempts/
        quiz_attempts.jsonl
        exam_attempts.jsonl
        grader_attempts.jsonl
      reports/
        performance_reports.jsonl
        topic_mastery.json
      rag_exports/
        chat_chunks.jsonl
        practice_chunks.jsonl
        performance_chunks.jsonl
  auth/
    users.json
  shared_templates/
    default_student_material/
```

The exact layout may vary, but it must be:

- easy to understand;
- local;
- per-user isolated;
- safe for retrieval;
- documented.

### Required metadata

Every stored item that can enter RAG must include metadata:

```text
user_id
session_id
subject_key
feature
source_layer
source_type
timestamp
language
topic
learning_goal
file_name
file_path_or_relative_path
page_number if applicable
modality: text | audio_transcript | image_ocr | image_description | quiz | exam | solution | report | performance
visibility: user_visible | hidden_until_finished | internal
```

### Required source layers

Use source layers consistently:

```text
local_material
official_syllabus
public_web
chat_history
generated_quiz
generated_exam
solution_set
student_answer
performance_report
adaptive_memory
```

### Required modules

Create or update:

```text
src/user_data_paths.py
src/chat_history_store.py
src/practice_store.py
src/rag_memory_indexer.py
```

Suggested functions:

```python
def get_user_root(user_id: str, config) -> Path: ...
def get_user_subject_root(user_id: str, subject_key: str, config) -> Path: ...
def save_chat_message(record: ChatMessageRecord, config) -> dict: ...
def save_chat_media(file_bytes: bytes, original_name: str, user_id: str, modality: str, config) -> Path: ...
def save_generated_quiz(record: GeneratedPracticeRecord, config) -> dict: ...
def save_generated_exam(record: GeneratedPracticeRecord, config) -> dict: ...
def save_solution_set(record: SolutionSetRecord, config) -> dict: ...
def save_performance_report(record: PerformanceReportRecord, config) -> dict: ...
def build_rag_documents_from_user_history(user_id: str, config) -> list[LoadedDocument]: ...
def index_user_memory_for_subject(user_id: str, subject_key: str, config) -> dict: ...
```

### Important privacy and UX rule

Hidden solution sets must be stored server-side/local-disk only and must not be displayed before the quiz/exam is finished and grading is complete.

---

## 3. Prevent RAG/Prompt Context from Ever Exceeding 128K Tokens

`gemma3:4b` must never receive more than a 128K token prompt context. Treat 128K tokens as the absolute hard upper limit.

### Required settings

Add config values similar to:

```env
GEMMA_MAX_CONTEXT_TOKENS=128000
MAX_PROMPT_INPUT_TOKENS=110000
RESERVED_OUTPUT_TOKENS=8192
TOKEN_SAFETY_MARGIN=4096
MAX_RETRIEVED_CHUNKS_PER_LAYER=12
MAX_CHARS_PER_CHUNK_IN_PROMPT=2500
ENABLE_CONTEXT_COMPRESSION=true
```

### Required module: `src/token_budget.py`

Implement a token-budget manager.

Suggested functions:

```python
def estimate_tokens(text: str) -> int: ...
def trim_text_to_token_budget(text: str, max_tokens: int) -> str: ...
def budget_context_sections(sections: list[ContextSection], config) -> BudgetedContext: ...
def assert_prompt_under_limit(prompt: str, config) -> None: ...
def build_token_budget_report(prompt: str, sections: list[ContextSection], config) -> dict: ...
```

Because the exact Gemma tokenizer may not be available locally, use a conservative estimate by default. For example:

```text
estimated_tokens = max(ceil(len(text) / 3.2), ceil(number_of_words * 1.4))
```

If a reliable local tokenizer is available, it may be used, but the conservative fallback must remain.

### Required RAG behavior

The RAG context builder must:

1. reserve output tokens;
2. reserve safety margin;
3. rank chunks by source priority and relevance;
4. include high-priority sources first;
5. trim low-priority/context-heavy sections first;
6. compress or summarize long chat history/performance history before final prompt assembly;
7. hard-fail gracefully before calling Ollama if the prompt would exceed 128K;
8. show a warning to the user that some context was omitted because of the token limit.

### Source-priority order for token budget

Keep this priority:

```text
1. current user question, current uploaded image/audio transcript/OCR
2. teacher/user learning material and exam criteria
3. learning goals
4. official KSA/Lucerne syllabus
5. relevant previous performance and weak topics
6. generated quizzes/exams and previous answers
7. public web sources
8. general background instructions
```

No prompt-building function may bypass `token_budget.py`.

---

## 4. Dedicated Timed Quiz and Exam Interfaces

The app needs separate, easily accessible interfaces for:

- generating quiz question sets;
- generating exam question sets.

These must be available from the main navigation and from each subject page.

### Required UX

Add clear buttons/cards:

```text
Generate Quiz Set
Generate Exam Question Set
```

When selected, each option should open a separate focused mode page, screen, or browser-tab-like view:

```text
Quiz Mode
Exam Mode
```

In Streamlit, this can be implemented with dedicated pages, query parameters, navigation state, or a focused full-width mode. If true separate browser windows are not possible, use a dedicated route/page that behaves like a separate test-taking screen.

### Required setup before start

Before the quiz/exam begins, the user must configure:

- subject;
- topic or learning goal;
- difficulty: adaptive/easy/medium/hard;
- number of questions;
- total points for exam if relevant;
- timer duration in minutes;
- language: High German, English, or French;
- whether to include syllabus fallback;
- whether to include public web sources.

### Required running behavior

Once the user presses `Start Quiz` or `Start Exam`:

1. generate the question set;
2. generate the solution set in the background;
3. store both locally;
4. show only the questions to the user;
5. start the timer;
6. prevent editing setup options during the attempt;
7. auto-submit or clearly warn when time is over;
8. collect answers;
9. grade answers after submission;
10. only then show the solution set;
11. store the attempt, grading result, and performance report;
12. index the relevant interaction/report into the user's RAG memory.

### Required modules

Create or update:

```text
src/attempt_session.py
src/timed_practice.py
src/quiz_mode.py
src/exam_mode.py
```

Suggested dataclasses:

```python
@dataclass
class TimedAttemptSession:
    attempt_id: str
    user_id: str
    subject_key: str
    mode: str  # quiz or exam
    started_at: str
    ends_at: str
    duration_seconds: int
    status: str  # setup | running | submitted | graded | expired
    question_set_path: str
    solution_set_path: str
    submitted_answers_path: str | None
    grading_report_path: str | None
```

### Timer implementation rule

Streamlit reruns often. Store timer state in `st.session_state` and on disk, not only in local variables.

If using an auto-refresh helper, keep it optional. The app must still work without it.

---

## 5. Login, Passwords, and Per-User Data Isolation

Earlier prompts avoided authentication for simplicity. This new requirement explicitly supersedes that limitation. Add simple **local-only authentication**.

The app must show a login/register screen as the first screen after startup.

### Required behavior

- A user must log in with username and password before accessing the app.
- A new user can be created from the first screen.
- Passwords must never be stored in plaintext.
- Use local password hashing with salt. Prefer a well-known library if already available, but the Python standard library `hashlib.pbkdf2_hmac` is acceptable and beginner-readable.
- Keep authentication local. No cloud auth and no external identity provider.
- Keep session state simple through Streamlit `st.session_state`.
- Add logout.
- Sanitize usernames before using them in file paths.

### Required modules

Create or update:

```text
src/auth.py
src/user_manager.py
src/user_data_paths.py
```

Suggested functions:

```python
def sanitize_username(username: str) -> str: ...
def create_password_hash(password: str) -> dict: ...
def verify_password(password: str, password_record: dict) -> bool: ...
def create_user(username: str, password: str, config, template_user_id: str | None = None) -> dict: ...
def authenticate_user(username: str, password: str, config) -> dict | None: ...
def list_users(config) -> list[dict]: ...
def copy_template_material_to_new_user(new_user_id: str, template_user_id: str | None, config) -> dict: ...
```

### Per-user isolation rules

Each user's data must be stored separately and retrieved separately.

A user must never retrieve another user's:

- chat history;
- uploaded images/audio;
- generated exams/quizzes;
- hidden solution sets;
- submitted answers;
- performance reports;
- vector/RAG memory chunks.

Every vector/RAG chunk must contain `user_id` metadata. Retrieval must filter by `user_id`. Collection names should also include or be scoped by user ID, for example:

```text
user_<safe_user_id>__subject_<subject_key>
user_<safe_user_id>__memory_<subject_key>
```

Do not rely only on UI hiding. Enforce isolation in storage and retrieval functions.

### New-user material cloning rule

When a new user is created, copy baseline study setup from a previous/template user:

Copy to the new user:

- study material;
- syllabus;
- grading criteria;
- learning goals;
- subject folder structure;
- optionally cached official public syllabus sources.

Do **not** copy:

- past quiz/exam attempts;
- performance reports;
- grades;
- chat history;
- uploaded personal media;
- hidden solution sets generated for another user;
- personal feedback.

If there is no previous user yet, create the new user with the default subject folder structure and any shared template material available under:

```text
data/shared_templates/default_student_material/
```

If multiple previous users exist, let the creator choose a template user or use a clearly documented default such as the first created user. Do not silently copy private performance data.

### Migration requirement

If the current app already has single-user data under `data/subjects`, `data/performance`, `vector_db`, or similar, add a safe migration script:

```text
scripts/migrate_single_user_to_user_storage.py
```

The script should:

- create a default user such as `alim` if no users exist;
- copy existing subject material into that user's storage;
- copy existing performance data only into that same user's performance folder;
- rebuild or mark vector indexes for rebuilding;
- never delete original data automatically.

---

## 6. Update All README Files and Add In-App Documentation

Update all existing README files to match the latest code.

Required docs:

```text
README.md
README_RUN_APP.md
README_TESTING.md
README_APP_DESCRIPTION.md
README_MULTIMODAL_AND_WEB.md
README_USER_ACCOUNTS_AND_DATA.md
README_ARCHITECTURE.md
```

If some already exist, update them instead of duplicating confusing information.

### README content must include

- what the app does;
- system architecture;
- folder structure;
- conda setup using `~/anaconda3/envs/alim_study_assistant`;
- environment update instructions;
- `gemma3:4b` setup through Ollama;
- login/register behavior;
- per-user data isolation;
- new-user material cloning rules;
- where chat history/media/practice reports are stored;
- how RAG uses chat/practice/performance memory;
- 128K token-window safety behavior;
- how timed quiz/exam modes work;
- how solution sets are hidden until after grading;
- how to index learning material;
- how to fetch syllabus material;
- privacy rules;
- testing commands;
- troubleshooting.

### In-app documentation section

Add a documentation/help page inside the Streamlit app.

It should explain in simple language:

- how to log in/register;
- how to choose a subject;
- how to upload or index material;
- how to use the chatbot;
- how to use image/audio input;
- how to generate a quiz;
- how to generate an exam;
- how the timer works;
- when solutions become visible;
- how grading works;
- how performance memory affects difficulty;
- how to interpret sources;
- how to troubleshoot missing Ollama/model/OCR/audio/web features.

---

## 7. Improve Modularity, Navigation, and UI Smoothness

Keep the UI beginner-friendly and more colorful without making the app complex.

### UI requirements

- Smooth navigation.
- Clear sidebar or top navigation.
- Subject dashboard.
- Dedicated Quiz Mode and Exam Mode.
- Performance dashboard.
- Documentation/help section.
- Login/logout UI.
- Colorful cards or sections for major actions.
- Clear warnings and status messages.
- Friendly labels in High German, English, or French depending on selected UI language.

### Do not over-engineer

Do not add React, FastAPI, Docker, PostgreSQL, Supabase, Firebase, cloud hosting, or cloud authentication.

Use Streamlit components and clean CSS where helpful.

### Suggested UI modules

Create or update:

```text
src/ui_components.py
src/ui_navigation.py
src/ui_docs.py
src/ui_auth.py
src/ui_subject_dashboard.py
src/ui_practice_modes.py
```

Keep `app.py` small. It should mostly orchestrate pages and call functions from `src/`.

---

# Required Implementation Details

## Configuration additions

Add or update `.env.example`:

```env
# Conda / runtime documentation helper
EXPECTED_CONDA_ENV_PATH=~/anaconda3/envs/alim_study_assistant

# Local model
MODEL_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_REQUIRED_MODEL=gemma3:4b
OLLAMA_VISION_MODEL=gemma3:4b

# User storage
USER_DATA_ROOT=data/users
AUTH_DB_FILE=data/auth/users.json
SHARED_TEMPLATE_ROOT=data/shared_templates/default_student_material
DEFAULT_TEMPLATE_USER_ID=
ENABLE_USER_ACCOUNTS=true

# Token budget
GEMMA_MAX_CONTEXT_TOKENS=128000
MAX_PROMPT_INPUT_TOKENS=110000
RESERVED_OUTPUT_TOKENS=8192
TOKEN_SAFETY_MARGIN=4096
MAX_RETRIEVED_CHUNKS_PER_LAYER=12
MAX_CHARS_PER_CHUNK_IN_PROMPT=2500
ENABLE_CONTEXT_COMPRESSION=true

# Practice modes
DEFAULT_QUIZ_TIMER_MINUTES=20
DEFAULT_EXAM_TIMER_MINUTES=45
ALLOW_AUTO_SUBMIT_ON_TIMER_END=true
HIDE_SOLUTIONS_UNTIL_GRADED=true

# Existing multimodal/web/performance settings remain
LEARNING_MATERIAL_ROOT=/home/kindalite/AI-App/AI_Exam_Prep/learning_material
ALLOW_INTERNET=true
ALLOW_WEB_FOR_PRIVATE_QUERIES=false
PERFORMANCE_LOG_FILE=data/performance/attempts.jsonl
```

Update `src/config.py` accordingly.

## Data models

Use dataclasses where helpful. Keep models simple.

Suggested records:

```python
@dataclass
class UserRecord:
    user_id: str
    username: str
    created_at: str
    password_hash: dict
    template_source_user_id: str | None
    role: str = "student"

@dataclass
class ChatMessageRecord:
    message_id: str
    session_id: str
    user_id: str
    subject_key: str
    timestamp: str
    language: str
    user_text: str
    audio_transcript: str | None
    image_ocr: str | None
    image_description: str | None
    assistant_answer: str | None
    source_chunk_ids: list[str]
    source_layers: list[str]

@dataclass
class GeneratedPracticeRecord:
    practice_id: str
    user_id: str
    subject_key: str
    mode: str  # quiz or exam
    timestamp: str
    language: str
    topic: str
    learning_goal: str | None
    difficulty_requested: str
    difficulty_used: str
    timer_seconds: int
    question_set: str
    solution_set_path: str
    visibility: str
    sources: list[dict]

@dataclass
class PerformanceReportRecord:
    report_id: str
    user_id: str
    subject_key: str
    practice_id: str
    timestamp: str
    points_achieved: float
    maximum_points: float
    grade: float
    strengths: list[str]
    weaknesses: list[str]
    recommended_actions: list[str]
    source_layers_used: list[str]
```

---

# Tests Codex Must Add

Preserve all old tests and all tests from Prompt 6. Add tests for this prompt.

## Unit tests

Create or update:

```text
tests/test_environment_verifier.py
tests/test_auth.py
tests/test_user_manager.py
tests/test_user_data_paths.py
tests/test_chat_history_store.py
tests/test_practice_store.py
tests/test_rag_memory_indexer.py
tests/test_token_budget.py
tests/test_timed_practice.py
tests/test_attempt_session.py
tests/test_ui_navigation_imports.py
```

Required unit test coverage:

1. `environment.yml` and `requirements.txt` are consistent for required packages.
2. `scripts/verify_environment.py` can run in dry/mock mode.
3. password hashes are salted and not equal to plaintext passwords.
4. correct password authenticates; wrong password fails.
5. usernames are sanitized before path use.
6. creating a user creates isolated folder structure.
7. creating a second user copies subject material/syllabus/criteria from a template user.
8. creating a second user does not copy chat history, attempts, reports, hidden solution sets, or personal media.
9. retrieval/vector collection names are scoped by `user_id`.
10. retrieval filters include `user_id` and cannot return another user's chunks.
11. chat text prompts are saved and can be converted into RAG documents.
12. image/audio metadata records are saved without requiring real OCR/Whisper.
13. generated quiz/exam records are saved.
14. hidden solution sets are stored but not marked visible before grading.
15. submitted answers and grading reports are saved.
16. `token_budget.estimate_tokens` is conservative.
17. prompt builders call token-budget checks before returning prompts.
18. fake 150K-token context is trimmed below the 128K hard limit.
19. when context is too large, lower-priority sections are trimmed first.
20. timed attempt sessions persist state across simulated Streamlit reruns.
21. timer expiration marks attempts expired or auto-submitted according to config.
22. solution set becomes visible only after submitted and graded.
23. old Swiss grade formula still works exactly.
24. UI modules import without requiring Streamlit server startup.
25. docs files exist after update.

Run:

```bash
pytest
```

## Feature tests

Create:

```text
tests/features/test_user_isolated_rag_and_practice_flow.py
tests/features/test_timed_quiz_exam_flow.py
tests/features/test_token_budget_context_packing.py
```

### Feature test 1: user-isolated RAG and practice flow

Test this with temporary folders and fake data:

```text
create template user A
→ add subject material, syllabus, criteria
→ create user B from user A template
→ verify B received material/syllabus/criteria
→ verify B did not receive A's attempts/chat/history/reports/media
→ create separate vector chunks for A and B
→ query as B
→ assert only B chunks are returned
→ save B chat prompt with fake image/audio metadata
→ index B history into RAG memory
→ query B memory
→ assert B history is retrievable and A history is not
```

### Feature test 2: timed quiz/exam flow

Test this with mocked LLM responses:

```text
login as a user
→ choose subject
→ configure quiz timer
→ start quiz
→ question set and hidden solution set are saved
→ only questions are visible
→ submit answers
→ grade answers
→ solution set becomes visible
→ performance report is saved
→ report is indexed into user RAG memory
→ repeat same pattern for exam mode
```

### Feature test 3: token budget context packing

Test this with synthetic huge context:

```text
create current question
→ create huge local material context
→ create huge syllabus context
→ create huge web context
→ create huge chat history context
→ build final prompt
→ assert estimated prompt tokens < 128000
→ assert current question remains
→ assert local material retained before web sources
→ assert warning lists omitted/trimmed sections
```

Run:

```bash
pytest tests/features/test_user_isolated_rag_and_practice_flow.py -v
pytest tests/features/test_timed_quiz_exam_flow.py -v
pytest tests/features/test_token_budget_context_packing.py -v
```

## System smoke and dry-run scripts

Create or update:

```text
scripts/verify_environment.py
scripts/system_smoke_user_accounts.py
scripts/dry_run_user_isolated_rag.py
scripts/dry_run_timed_quiz_exam.py
scripts/dry_run_token_budget_128k.py
scripts/dry_run_full_student_system.py
```

### `scripts/system_smoke_user_accounts.py`

Must check:

- auth DB can be created in a temp folder;
- test user can register/login/logout;
- per-user folder structure is created;
- app imports;
- docs page modules import;
- no plaintext password is stored.

### `scripts/dry_run_user_isolated_rag.py`

Must demonstrate:

```text
fake user A and B
→ template material copy
→ isolated chat history
→ isolated vector/RAG memory
→ query only returns current user material
→ PASS summary
```

### `scripts/dry_run_timed_quiz_exam.py`

Must demonstrate without real Ollama:

```text
fake quiz generation
→ hidden solution set
→ timer state
→ answer submission
→ grading
→ solution reveal
→ performance report save
→ RAG memory indexing
→ PASS summary
```

### `scripts/dry_run_token_budget_128k.py`

Must demonstrate:

```text
fake overlarge context
→ context packing
→ prompt under 128K estimated tokens
→ warning for trimmed context
→ PASS summary
```

### `scripts/dry_run_full_student_system.py`

Must run with no internet, no Ollama, no Tesseract, and no Whisper by using fakes/mocks. It must demonstrate:

```text
environment config loads
→ user login/register
→ template material copy
→ subject dashboard available
→ chat text/image/audio metadata saved
→ RAG memory indexing
→ quiz mode
→ exam mode
→ grading
→ performance report
→ adaptive difficulty
→ token budget protection
→ docs page imports
→ PASS summary
```

---

# Required Verification Commands Before Codex Claims Completion

Codex must run these commands from the correct project root, usually `Code/`.

If the target conda path exists, use:

```bash
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/verify_environment.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/system_smoke_gemma3.py
conda run -p ~/anaconda3/envs/alim_study_assistant pytest
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_end_to_end_multimodal_adaptive_feature.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_user_isolated_rag_and_practice_flow.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_timed_quiz_exam_flow.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_token_budget_context_packing.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/smoke_test.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/system_smoke_user_accounts.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_pipeline.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_multimodal_adaptive_pipeline.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_full_system_no_external.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_user_isolated_rag.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_timed_quiz_exam.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_token_budget_128k.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_full_student_system.py
conda run -p ~/anaconda3/envs/alim_study_assistant python -m py_compile app.py src/*.py
```

If the exact conda environment is not available in Codex's execution environment, Codex must still run the equivalent commands with the active Python and clearly report that the target-path verification could not be performed in this environment.

Do not claim completion if tests were skipped without explanation.

---

# Required Completion Report Format

Codex's final message must include this exact structure:

```text
Changed files:
- ...

Environment:
- target conda path: ~/anaconda3/envs/alim_study_assistant
- environment update: PASS/FAIL/SKIP with reason
- python version: ...
- dependency check: PASS/FAIL

Model verification:
- gemma3:4b configured: PASS/FAIL
- gemma3:4b pull/check: PASS/FAIL/SKIP with reason

User accounts and isolation:
- login/register: PASS/FAIL
- password hashing: PASS/FAIL
- per-user data isolation: PASS/FAIL
- new-user template material copy: PASS/FAIL

RAG memory:
- chat prompts saved: PASS/FAIL
- image/audio metadata saved: PASS/FAIL
- generated quizzes/exams saved: PASS/FAIL
- solution sets hidden until graded: PASS/FAIL
- performance reports indexed: PASS/FAIL

Token budget:
- 128K hard limit enforced: PASS/FAIL
- overlarge context dry run: PASS/FAIL

Practice modes:
- timed quiz mode: PASS/FAIL
- timed exam mode: PASS/FAIL
- timer persistence: PASS/FAIL
- solution reveal after grading: PASS/FAIL

Documentation/UI:
- README files updated: PASS/FAIL
- in-app docs page: PASS/FAIL
- smoother navigation/colorful UI: PASS/FAIL

Test results:
- python scripts/verify_environment.py: PASS/FAIL
- python scripts/system_smoke_gemma3.py: PASS/FAIL
- pytest: PASS/FAIL, number of tests
- pytest tests/features/test_end_to_end_multimodal_adaptive_feature.py -v: PASS/FAIL
- pytest tests/features/test_user_isolated_rag_and_practice_flow.py -v: PASS/FAIL
- pytest tests/features/test_timed_quiz_exam_flow.py -v: PASS/FAIL
- pytest tests/features/test_token_budget_context_packing.py -v: PASS/FAIL
- python scripts/smoke_test.py: PASS/FAIL
- python scripts/system_smoke_user_accounts.py: PASS/FAIL
- python scripts/dry_run_pipeline.py: PASS/FAIL
- python scripts/dry_run_multimodal_adaptive_pipeline.py: PASS/FAIL
- python scripts/dry_run_full_system_no_external.py: PASS/FAIL
- python scripts/dry_run_user_isolated_rag.py: PASS/FAIL
- python scripts/dry_run_timed_quiz_exam.py: PASS/FAIL
- python scripts/dry_run_token_budget_128k.py: PASS/FAIL
- python scripts/dry_run_full_student_system.py: PASS/FAIL
- python -m py_compile app.py src/*.py: PASS/FAIL

How to run:
- conda activate ~/anaconda3/envs/alim_study_assistant
- ollama pull gemma3:4b
- streamlit run app.py

Known limitations:
- ...
```

---

# Acceptance Criteria

This prompt is complete only when all of the following are true:

- The conda environment files match the current code requirements.
- The target environment path `~/anaconda3/envs/alim_study_assistant` is documented and verifiable.
- `scripts/verify_environment.py` exists and runs.
- Login/register appears before app access.
- Passwords are salted and hashed, never plaintext.
- Every user has isolated data folders.
- Retrieval and vector indexes are scoped by `user_id`.
- New users receive copied study material/syllabus/grading criteria from a template/previous user.
- New users do not receive another user's chats, attempts, reports, media, or hidden solutions.
- Chat text/image/audio prompts are stored locally.
- Generated quizzes, exams, solution sets, submitted answers, grading results, and performance reports are stored locally.
- Stored chat/practice/performance memory can be converted into RAG documents.
- Prompt builders enforce the 128K hard context limit before calling Ollama.
- Overlarge contexts are trimmed/compressed with warnings.
- Quiz Mode and Exam Mode are separate, accessible, timed, and user-configurable.
- Solution sets are generated in the background but hidden until submission and grading finish.
- Performance reports are saved and indexed into the correct user's RAG memory.
- READMEs are updated for the latest architecture and usage.
- The Streamlit app has a documentation/help section.
- Navigation is smoother and beginner-friendly.
- UI has tasteful colorful elements/cards/status sections.
- All old tests still pass.
- All new unit/feature/smoke/dry-run tests pass or failures are honestly reported and fixed before completion.

## Final Instruction to Codex

Implement this as the next careful upgrade to the existing app. Keep the system local-first, private, beginner-readable, and modular. The app is for 15-16 year old high school students, so reliability, clarity, data isolation, and smooth navigation matter more than flashy features.

Do not confirm that the task is done until the environment, login/user isolation, RAG memory storage, 128K token budget, timed quiz/exam modes, documentation, smoke tests, dry runs, and feature tests have all been implemented and verified.
