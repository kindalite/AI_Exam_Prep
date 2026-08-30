# Codex Prompt 8: Stability, Performance, Grounded Learning, Analytics, and UI Upgrade

## Context

Continue the current **Alim’s Study Assistant** repository. This prompt builds on all earlier prompts, especially Prompt 6 (`gemma3:4b`, multimodal RAG, syllabus/web retrieval, adaptive memory) and Prompt 7 (exact Conda environment, user accounts/data isolation, persistent history, 128K limit, timed Quiz/Exam modes, documentation, and mandatory tests).

Do not rewrite the app. Inspect the repository first, preserve working code and data, and extend it incrementally. Keep the Streamlit architecture, keep `app.py` small, and move logic into readable modules under `src/`.

## Non-negotiable rules

- Local Ollama `gemma3:4b` remains the default model.
- Private files, prompts, media, answers, grades, and feedback stay local.
- Every model call must use the existing token-budget layer and remain safely below the absolute 128K context ceiling.
- Per-user storage and retrieval isolation must remain enforced in storage and vector queries.
- Do not expose hidden quiz/exam solutions before submission and grading.
- Do not store passwords or third-party credentials in plaintext.
- Do not fake integrations or mark placeholder pages as complete.
- Do not claim completion until all applicable tests pass and reports are saved.

---

# 1. Baseline audit

Activate:

```bash
conda activate ~/anaconda3/envs/alim_study_assistant
```

Before changing code, run and save results under `bug_review/baseline/`:

```bash
python scripts/verify_environment.py
python -m pip check
pytest -q
python scripts/smoke_test.py
python scripts/dry_run_pipeline.py
```

Record current failures, startup/answering times, package versions, Ollama status, and repository architecture. Never delete older logs or reports.

---

# 2. Critical performance, dependency, freeze, and logging fixes

## 2.1 Fix Torchvision

`torchvision` is missing. Install and pin a version compatible with the current Python, `torch`, OS, and hardware. Keep `environment.yml`, `requirements.txt`, lock/snapshot files, and READMEs consistent. Add a test that detects Torch/Torchvision mismatches and prints an actionable message. Do not blindly mix CPU and incompatible CUDA builds.

## 2.2 Faster model startup and answers

Implement and measure:

- verify Ollama and `gemma3:4b` at startup;
- preload/warm the model after startup or login;
- use Ollama keep-alive where supported;
- reuse Ollama/HTTP clients;
- stream tokens to the UI;
- cache heavyweight local resources with `st.cache_resource`;
- lazy-load and cache embeddings, OCR, transcription, and vision resources;
- avoid rebuilding indexes on Streamlit reruns;
- use manifests and incremental indexing;
- cache deterministic parsing and approved web/syllabus results;
- retrieve fewer, better chunks and rerank them;
- add timeouts, bounded retries, and graceful recovery;
- persist operation state across Streamlit reruns.

Create/update:

```text
src/model_runtime.py
src/performance_monitor.py
src/operation_tracker.py
```

Measure cold startup, warm startup, model warm-up, time to first token, total answer time, retrieval time, indexing time, quiz generation, and grading. Report before/after measurements without inventing guarantees.

## 2.3 Progress indicators

Whenever the app is loading the model, retrieving, browsing, OCRing, transcribing, indexing, generating, grading, or saving, display a spinner/progress wheel with the current step and a clear success/warning/error result.

## 2.4 Verbose safe logs

Create `src/app_logging.py`. Store logs under:

```text
bug_review/
  app_runs/
  user_sessions/
  crashes/
  performance/
  test_reports/
```

Use one identifiable app-run log and one user-session log per instance. Log timestamps, anonymized IDs, selected feature/subject, parsing and retrieval counts, model request timing, token estimates, context trimming, cache hits, web permission, source counts, timeouts, retries, Streamlit reruns, warnings, exceptions, and stack traces.

Never log passwords, secrets, full documents, full private prompts, or full student answers. Redact previews, rotate/cap logs, and add a safe “Download diagnostic report” action.

Add watchdog-style warnings for operations exceeding configurable thresholds so freezes can be diagnosed. A failed operation must return the user to a usable state.

---

# 3. Grounded answering and controlled internet access

The model should give detailed, comprehensive answers appropriate for a Swiss Gymnasium student while remaining anchored in this order:

1. current user’s teacher/student material and grading criteria;
2. learning goals;
3. official Kantonsschule Alpenquai/Lucerne syllabus;
4. user-approved trusted public web sources;
5. clearly labelled model inference/general background.

Do not answer at university/PhD depth unless asked.

Before every new internet search, show a confirmation:

```text
The local material may be insufficient. Search trusted online sources?
[Search internet] [Use local material only]
```

A session-only “remember this choice” option is acceptable. Never send private document text, answers, names, or sensitive content in web queries; create sanitized topic queries.

Every answer must group evidence under:

```text
From your materials
From the official Lucerne/KSA syllabus
From approved online sources
Model inference/general background
```

Show file name, page, modality, title, URL/domain, and fetch date when available. Explicitly state missing/conflicting evidence.

Prefer official Swiss/KSA/Lucerne, government, university, museum, scientific, and reputable open educational sources. Reject pirated textbooks, answer farms, untrusted scraped content, and age-inappropriate material. Persist approved public sources per user/subject with provenance and licence notes.

Suggested modules:

```text
src/web_permission.py
src/source_policy.py
src/web_research.py
src/source_citations.py
```

---

# 4. Repair multimodal material ingestion and syllabus retrieval

Support and correctly index:

```text
PDF, DOCX, PNG, JPEG/JPG, SVG, TXT, MD
```

Retain originals, extracted text, OCR text, visual descriptions, embedded/extracted graphics, page previews, metadata, warnings, hashes, and indexing status.

## PDFs

For every PDF:

- extract selectable text page-by-page;
- render pages for OCR/vision where needed;
- extract embedded graphics when possible;
- preserve page numbers;
- detect blank, nearly empty, scanned, corrupted, encrypted, or unreadable files;
- warn when extraction is suspiciously low;
- give a post-upload content overview;
- let the user inspect page thumbnails/previews;
- avoid duplicate indexing using hashes.

Do not report successful indexing for empty or unreadable PDFs.

## DOCX and images

For DOCX, extract headings, paragraphs, lists, tables, captions, and embedded images in order.

For PNG/JPEG, run local OCR and local `gemma3:4b` image understanding. Identify visible text, diagrams, graphs, formulas, molecule structures, labels, and uncertainty.

For SVG, preserve the file, safely extract readable text/metadata, sanitize unsafe content before display, and render a preview for OCR/vision when useful.

Index image-derived descriptions with modality metadata so relevant graphics can be retrieved for explanations, quizzes, and exams.

## Local syllabus

Fix reading/indexing of locally stored syllabus PDFs/DOCX. Add tests proving the app can answer known questions from local syllabus fixtures and cite the correct page/section. Official web syllabus is a fallback/update source, not a replacement for working local ingestion.

## Material panel

On the right of every subject dashboard, add a Notion-like material panel showing:

- files/folders and type;
- date, size, pages, hash, and indexing status;
- detected text/OCR/images/descriptions;
- blank/unreadable warnings;
- expandable overview and page viewer;
- re-index, archive, remove-from-index, and delete actions with confirmation;
- missing learning-material/learning-goal warnings.

If no material or learning goals exist, offer:

1. upload PDF/DOCX/PNG/JPEG/SVG;
2. add a web link;
3. search by keywords after permission;
4. use official syllabus as a minimal fallback.

All uploaded data must be saved under the correct isolated user/subject and shared across that subject’s Chat, Knowledge Analysis, Quiz, Exam, Grader, and Study Plan modes.

---

# 5. Automatic subject languages and subject split

Remove the AI response-language selector. Determine language from subject:

```text
German:
SPF Chemistry, SPF Biology, German, Philosophy, Political Education,
Pedagogics and Psychology, Chemistry, Biology

English:
English, History, Mathematics, Physics

French:
French
```

French explanations must be simple French around CEFR B1. Keep technical words but explain them simply.

A separate interface-language setting for menus/help is allowed.

Split the existing `Maths/Physics` subject into separate `Mathematics` and `Physics` subjects. Add a safe migration for material, criteria, learning goals, vector indexes, attempts, grades, and history. Never delete old combined data automatically. Ask for manual assignment when classification is uncertain.

---

# 6. Useful subject dashboard and core learning modes

Use a three-column subject layout:

```text
Left: Chat, Knowledge Analysis, Quiz, Exam, Study Plan, Stats, Subject Tools
Middle: active mode
Right: Notes Ingestion and Material Viewer
```

Every subject card must open a useful interactive dashboard.

## Chat

- automatic subject language;
- text, image, audio, and file input;
- local material/syllabus first;
- internet permission when needed;
- grouped sources and inference labels;
- streamed answers and progress;
- upload overview/empty-file warning;
- persistent multimodal history and retrieval metadata.

## Knowledge Analysis

Create a mode that:

- selects topic/learning goal;
- asks diagnostic questions from material and syllabus;
- estimates mastery without generating an official grade;
- identifies strengths, misconceptions, and missing knowledge;
- saves mastery/uncertainty;
- allows Quiz Mode to target weak areas.

Exam Mode must remain neutral and must not be personalized to make it easier.

## Quiz Mode

Repair generation using a validated structured schema, not free-form prose.

Support short answer, matching, true/false, and MCQ. MCQs must have plausible non-duplicated options and exactly one correct answer unless marked multi-select. Support one or multiple questions, topic/goal, adaptive or selected difficulty, timers, optional relevant graphics, immediate score and explanations.

Quiz scores are practice only and must never enter school-grade or exam-performance averages.

Validate generated question JSON/schema before display. Retry safely or show a clear error. Never reveal answers early.

## Exam Mode

Generate complete neutral practice exams using subject, local/official syllabus, chosen topics, grading criteria, language, time, points, and Swiss German-speaking Gymnasium exam conventions where relevant.

Generate/store questions, solutions, and marking scheme before the attempt. Reveal solutions only after submission and grading. Exam attempts may enter exam-performance statistics.

## Exam Grader

Allow exactly:

```text
1, 3, or 5 generated questions
```

Generate them from the selected subject/topic and syllabus in the automatic subject language.

Grading must:

- use deterministic rubrics and points;
- use local material/syllabus first;
- request permission before web use;
- be somewhat lenient about wording when the core concept is correct;
- never reward an incorrect concept;
- explain awarded/missing points;
- show an improved answer;
- output only numeric Swiss grades from 1.0 to 6.0;
- never output letter grades.

Use one deterministic conversion across subjects:

```python
grade = 1.0 + 5.0 * (points_achieved / maximum_points)
grade = min(6.0, max(1.0, grade))
```

Store raw points and raw grade. Round only in the defined presentation function. Add edge-case tests.

## Study Plan

Ask for and respect:

- exams and deadlines;
- school hours;
- sleep;
- extracurricular activities;
- commute/travel;
- meals/breaks;
- fixed commitments;
- weekday/weekend availability;
- preferred session length;
- weak topics and learning goals.

Never schedule over fixed commitments. Use reliable study practices suitable for Swiss high-school students: spaced practice, retrieval practice, interleaving, realistic breaks, sleep protection, and mock-exam checkpoints. Ask permission before online research and cite the advice.

---

# 7. Stats and Planner

## Grade data

Support manual entry and transcript/report-card upload (PDF/PNG/JPEG) with OCR plus user review before saving.

Store subject, assessment title/type, date or month/year, raw points, maximum points, optional weight, and numeric Swiss grade. Every grade must remain between 1.0 and 6.0. No letter grades.

## School years

Support navigation from:

```text
Academic Year 2022–23 / 7th Grade
```

onward, with previous/next carousel arrows and a selector.

## Subject statistics

Each subject dropdown/page should show:

- all assessments/grades;
- raw points and conversion;
- monthly/yearly trends;
- average;
- strongest/weakest topics;
- exam versus practice performance;
- intuitive graphs and plain-language interpretations;
- suggested focus areas.

## Overall average

At the bottom of the School page:

1. calculate each subject average;
2. round each subject grade to the nearest 0.5 with one documented deterministic rule;
3. average the rounded subject grades;
4. clamp the displayed result to 1.0–6.0.

Add tests for rounding boundaries and missing subjects.

## Planner

The main title screen must have a separate Planner card. Planner supports exams, study sessions, extracurricular activities, recurring commitments, travel, reminders, completion states, calendar/list views, and generated Study Plan integration.

---

# 8. UI redesign

After login show the full title:

```text
Alim’s Study Assistant
```

Then two large cards:

```text
School
Planner
```

School page:

- evenly spaced subject cards;
- Stats panel on the right;
- current yearly average/trend at bottom;
- school-year carousel;
- material completeness, upcoming-exam, and weak-topic indicators.

Add persistent footer links on every page:

```text
Feedback
Help
```

Add a user-persistent appearance switch:

```text
Light: white background, dark text
Dark: black/dark-grey background, white text
```

Navigation must preserve safe state across Streamlit reruns, provide breadcrumbs/back actions, use accessible contrast and clear labels, and avoid empty placeholder pages.

---

# 9. Subject-specific tools

Keep these modular, local, and behind feature flags until tested. The main app must still run if optional dependencies are absent.

## Mathematics graphing

Build a safe interactive graphing tool similar in purpose to a basic Desmos-style viewer:

- multiple functions;
- zoom/pan;
- ranges;
- value table;
- roots/intersections/extrema where safely computable;
- image export;
- attach graph to explanations/quizzes.

Use safe expression parsing. Never use unrestricted `eval`.

## Chemistry/SPF Chemistry structure builder

Support educational creation/visualization of:

- Lewis structures;
- wedge/dash formulas;
- skeletal formulas;
- selectable atoms and bond editing;
- common molecule templates;
- ionic bonds, charges, colour legend, and simplified lattice/grid;
- simple metallic bonding representations.

Use reliable local chemistry libraries when feasible; otherwise provide a clearly labelled limited educational builder.

## Biology/biomolecules

Extend compatible visual tools for amino acids, proteins, carbohydrates, lipids, nucleotides/DNA, membranes, and other syllabus-relevant biomolecules.

## Mind maps/flowcharts

Create interactive subject mind maps:

- central term and connected concepts;
- hover/click descriptions;
- labelled connections;
- source references;
- editable nodes/edges;
- persistent save;
- export image and structured data;
- safe local rendering.

Draw.io export may be supported, but no cloud dependency is required.

---

# 10. Feedback and Help

## Feedback

Explain clearly:

- what is stored;
- exact local storage location;
- per-user isolation;
- how feedback affects later retrieval/prompts/recommendations;
- that this is not model training;
- how relevant feedback is selectively retrieved/compressed to protect the 128K limit;
- how to view/export/edit/delete it.

Support timestamped text, image, and audio feedback, transcript, feature/category, severity, and optional screenshot/log reference.

Add a controlled test comparing the same request before and after relevant feedback. Verify relevant feedback changes the prompt/behavior, unrelated feedback is not injected, users remain isolated, and token limits are respected. Save a concise feedback summary for the next Codex bug-fix cycle.

## Help

Create detailed English and German manuals covering login, privacy, School, Planner, subject dashboards, ingestion/viewing, chat/sources, Knowledge Analysis, Quiz, Exam, Grader/Swiss grades, Stats, Study Plans, feedback, subject tools, appearance, web permission, troubleshooting, logs, and data deletion.

---

# 11. Apple Reminders/iCloud integration

Treat this as security-sensitive.

- Never create a fake Apple login form.
- Never collect/store a normal Apple ID password.
- First document a feasibility/security review of supported Apple mechanisms.
- Use only a supported secure method such as a valid CalDAV/app-specific-password flow, official mechanism, local macOS bridge, Shortcuts bridge, or standards-based export where technically appropriate.
- Secure tokens/secrets using appropriate local secret storage.
- Add disconnect/revoke controls.
- Keep the app functional when integration is unavailable.
- Automated tests must use mocks and never real credentials.

Minimum safe fallback:

- `.ics` export;
- documented Apple Shortcuts/calendar/reminder import;
- recurring reminder generation;
- clear limitations.

Do not call this complete if it is only a decorative Apple button.

---

# 12. Suggested modules and documentation

Reuse equivalents where they already exist. Possible modules:

```text
src/app_logging.py
src/performance_monitor.py
src/operation_tracker.py
src/model_runtime.py
src/web_permission.py
src/source_policy.py
src/source_citations.py
src/material_quality.py
src/material_preview.py
src/multimodal_ingestion.py
src/knowledge_analysis.py
src/question_schema.py
src/quiz_validator.py
src/swiss_grading.py
src/school_years.py
src/grade_transcript_parser.py
src/study_schedule_constraints.py
src/subject_languages.py
src/math_graphing.py
src/chemistry_structures.py
src/biology_visuals.py
src/mind_maps.py
src/reminders_integration.py
src/ui_home.py
src/ui_school.py
src/ui_subject.py
src/ui_planner.py
src/ui_feedback.py
src/ui_help.py
```

Update environment/configuration and all current READMEs, including architecture, running, testing, multimodal/web, user data, troubleshooting, and in-app manuals.

---

# 13. Implementation priority

## Phase 1 — Critical

1. Baseline and verbose safe logging.
2. Fix Torchvision compatibility.
3. Warm model, keep alive, stream, cache, add timeouts/progress.
4. Diagnose/recover from freezes.
5. Run focused and full tests.

## Phase 2 — Correctness

1. Fix PDF/DOCX/image/SVG ingestion and material viewer.
2. Fix local syllabus indexing/retrieval.
3. Automatic language mapping.
4. Split Mathematics/Physics with migration.
5. Repair Swiss grading, Quiz MCQs, Grader 1/3/5 flow.
6. Run regression and system tests.

## Phase 3 — UX and learning

1. Functional subject dashboards.
2. Knowledge Analysis.
3. Study Plan constraints/advice.
4. Stats, transcript import, school-year history, Planner.
5. Full UI redesign, appearance, Help/Feedback.
6. Run feature/system tests.

## Phase 4 — Advanced

1. Math graphing.
2. Chemistry/Biology visual tools.
3. Mind maps.
4. Persistent trusted-source library.
5. Safe Apple integration or secure fallback.
6. Keep behind feature flags until tested.

---

# 14. Mandatory tests

Every reported bug and implemented feature needs a focused regression test.

At minimum add unit tests for:

- Torch/Torchvision compatibility;
- logging/redaction/rotation;
- timeout/watchdog/state recovery;
- warm-up/keep-alive/streaming/cache;
- progress states;
- normal/scanned/empty/corrupt PDFs;
- DOCX paragraphs/tables/images;
- PNG/JPEG OCR/vision and safe SVG;
- material warnings/view metadata;
- local syllabus retrieval/citations;
- internet permission/query sanitization/source grouping;
- language mapping/French B1 instruction;
- Math/Physics migration;
- quiz schema/MCQs;
- Grader 1/3/5;
- deterministic 1.0–6.0 grading;
- lenient wording rubric without rewarding wrong concepts;
- Study Plan scheduling constraints;
- transcript review;
- school-year/0.5 rounding;
- Quiz exclusion from official grade stats;
- Knowledge Analysis persistence;
- Exam neutrality;
- feedback effectiveness/isolation/token safety;
- appearance persistence;
- safe graph expression parsing;
- chemistry/mind-map persistence;
- Apple credential safety/fallback;
- all existing authentication, user-isolation, solution-visibility, and 128K tests.

Add feature tests:

```text
tests/features/test_grounded_subject_chat.py
tests/features/test_material_upload_preview_and_rag.py
tests/features/test_quiz_mcq_flow.py
tests/features/test_exam_generation_grading_and_solution_reveal.py
tests/features/test_knowledge_analysis_to_adaptive_quiz.py
tests/features/test_study_plan_with_extracurriculars.py
tests/features/test_stats_transcript_and_school_years.py
tests/features/test_feedback_changes_next_response.py
tests/features/test_subject_language_behavior.py
tests/features/test_math_physics_split.py
tests/features/test_ui_navigation_and_progress.py
```

Create/update smoke, dry-run, and benchmark scripts:

```text
scripts/system_smoke_full_app.py
scripts/system_smoke_model_warmup.py
scripts/system_smoke_material_ingestion.py
scripts/dry_run_grounded_web_answer.py
scripts/dry_run_multimodal_material.py
scripts/dry_run_quiz_exam_grader.py
scripts/dry_run_stats_planner.py
scripts/dry_run_feedback_memory.py
scripts/dry_run_full_student_journey.py
scripts/performance_benchmark.py
```

The full student journey must test:

```text
start → login → School → subject → upload/preview/index material
→ grounded chat → approve optional web search → inspect source groups
→ Knowledge Analysis → MCQ Quiz → full Exam → numeric Swiss grade
→ save/view Stats → Study Plan around extracurriculars
→ multimodal Feedback → verify relevant feedback affects later request
→ Help → logout
```

Normal automated tests must mock Ollama/web/OCR/audio. Real local integrations may be separate marked tests.

Save:

```text
bug_review/test_reports/FINAL_TEST_REPORT.md
bug_review/performance/FINAL_PERFORMANCE_REPORT.md
bug_review/FINAL_BUG_REVIEW.md
```

`FINAL_BUG_REVIEW.md` must mark every requirement as Implemented, Partially implemented, Blocked, or Not implemented, with reason and next step.

---

# 15. Completion gates

Do not declare completion until all applicable commands pass:

```bash
conda activate ~/anaconda3/envs/alim_study_assistant
python scripts/verify_environment.py
python -m pip check
python -m py_compile app.py src/*.py
pytest -q
pytest tests/features -q
python scripts/smoke_test.py
python scripts/system_smoke_full_app.py
python scripts/system_smoke_model_warmup.py
python scripts/system_smoke_material_ingestion.py
python scripts/dry_run_grounded_web_answer.py
python scripts/dry_run_multimodal_material.py
python scripts/dry_run_quiz_exam_grader.py
python scripts/dry_run_stats_planner.py
python scripts/dry_run_feedback_memory.py
python scripts/dry_run_full_student_journey.py
python scripts/performance_benchmark.py
```

If a command is genuinely not applicable, state why. Never silently skip it.

The final Codex report must include:

- files changed/created;
- migrations;
- dependency versions;
- exact commands and PASS/FAIL;
- test count;
- measured before/after performance;
- unresolved limitations;
- log/report locations;
- exact app-start commands.

## Final instruction

Prioritize stability, speed, correct ingestion, source grounding, functional Quiz/Exam/Grader modes, deterministic Swiss grades, useful dashboards, and diagnostic logging before advanced visual tools or Apple integration.

Preserve privacy, user isolation, persistent RAG memory, source provenance, hidden-solution rules, and the strict 128K ceiling. Never output letter grades, never fake an integration, and never claim completion while tests fail.
