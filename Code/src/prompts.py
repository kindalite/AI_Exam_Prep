"""Prompt templates for subject chat, quizzes, exams, planning, and grading."""

from __future__ import annotations

from .config import load_config
from .subject_registry import Subject
from .token_budget import ContextSection, assert_prompt_under_limit, budget_context_sections


SOURCE_PRIORITY_RULES = """Source priority rules:
1. Use teacher-provided/user-provided learning material and exam criteria first.
2. Use user learning goals second.
3. Use official KSA/Lucerne syllabus sources only to fill gaps.
4. Use public web sources only when internet mode is enabled.
5. Use general model knowledge only when needed and clearly label it as general background.
Say clearly when user material is missing or insufficient. Show sources. Do not pretend image OCR or audio transcripts are complete when uncertain."""

SOURCE_RULES = (
    "Use only the provided notes, syllabus, learning goals, exam criteria, retrieved sources, and local performance context. "
    "If source material is insufficient, say that clearly. Include source file names, pages, modalities, and URLs when possible. "
    "Do not invent exam rules that are not present in the sources."
)


def _finalize_prompt(prompt: str, config=None) -> str:
    """Ensure every prompt stays under the configured local token budget."""
    app_config = config or load_config()
    budgeted = budget_context_sections([ContextSection("prompt", prompt, 1, "current_prompt")], app_config)
    final = budgeted.text or prompt
    if budgeted.warnings:
        final += "\n\nToken budget warnings:\n" + "\n".join(f"- {warning}" for warning in budgeted.warnings)
    assert_prompt_under_limit(final, app_config)
    return final


def build_system_prompt(subject: Subject, language: str) -> str:
    """Create a reusable system prompt for one subject and language."""
    prompt = (
        f"You are Alim Study Assistant for {subject.display_name}. "
        f"Answer in {language}. Subject instructions: {subject.instructions}\n{SOURCE_PRIORITY_RULES}\n{SOURCE_RULES}"
    )
    return _finalize_prompt(prompt)


def build_chat_prompt(subject: Subject, language: str, question: str, context: str, learning_goals: str, criteria: str) -> str:
    """Build the prompt for subject question answering."""
    prompt = f"""Subject: {subject.display_name}
Language: {language}

{SOURCE_PRIORITY_RULES}

Learning goals:
{learning_goals or "No learning goals file was found."}

Exam criteria:
{criteria or "No exam criteria file was found."}

Retrieved source context:
{context or "No retrieved source context was found."}

Student question:
{question}

Task: Answer clearly, explain the reasoning, and list useful source names."""
    return _finalize_prompt(prompt)


def build_multimodal_chat_prompt(
    subject: Subject,
    language: str,
    question: str,
    local_context: str,
    syllabus_context: str,
    web_context: str,
    performance_context: str,
    learning_goals: str = "",
    criteria: str = "",
    audio_transcript: str = "",
    image_ocr: str = "",
    image_description: str = "",
    warnings: list[str] | None = None,
) -> str:
    """Build a prompt from text, audio/image context, RAG layers, web, and performance."""
    warning_text = "\n".join(warnings or []) or "No warnings."
    sections = [
        ContextSection("Current question", question or "No typed question.", 1, "current_question"),
        ContextSection("Audio transcript", audio_transcript or "No audio transcript.", 1, "audio_transcript"),
        ContextSection("Image OCR", image_ocr or "No image OCR text.", 1, "image_ocr"),
        ContextSection("Image description", image_description or "No image description.", 1, "image_description"),
        ContextSection("Local material context", local_context or "No local material context was found.", 2, "local_material"),
        ContextSection("Learning goals", learning_goals or "No learning goals file was found.", 3, "learning_goals"),
        ContextSection("Exam criteria", criteria or "No exam criteria file was found.", 2, "local_material"),
        ContextSection("Official KSA/Lucerne syllabus context", syllabus_context or "No official syllabus context was used.", 4, "official_syllabus"),
        ContextSection("Past performance context", performance_context or "No performance records yet.", 5, "adaptive_memory"),
        ContextSection("Public web context", web_context or "No public web context was used.", 7, "public_web"),
        ContextSection("Tool warnings", warning_text, 1, "internal"),
    ]
    budgeted = budget_context_sections(sections, load_config())
    prompt = f"""Subject: {subject.display_name}
Response language: {language}

{SOURCE_PRIORITY_RULES}

{budgeted.text}

Task: Answer the student using user material first. Use official syllabus only to fill gaps. Use web sources only when internet mode is enabled. Show sources and uncertainty notes."""
    if budgeted.warnings:
        prompt += "\n\nToken budget warnings:\n" + "\n".join(f"- {warning}" for warning in budgeted.warnings)
    return _finalize_prompt(prompt)


def build_quiz_prompt(subject: Subject, language: str, learning_goal: str, difficulty: str, context: str, criteria: str, performance_context: str = "", focus_topics: list[str] | None = None) -> str:
    """Build a quiz-generation prompt."""
    focus_text = ", ".join(focus_topics or []) or "No focus topics recorded yet."
    prompt = f"""Create a {difficulty} quiz for {subject.display_name} in {language}.
Learning goal: {learning_goal or "Use the most relevant available goals."}
Adaptive performance context: {performance_context or "No performance context."}
Focus topics: {focus_text}
Subject criteria: {criteria or "No criteria file was found."}
Source context: {context or "No source context was found."}

Include questions, answer key, short explanations, and source references. {SOURCE_PRIORITY_RULES} {SOURCE_RULES}"""
    return _finalize_prompt(prompt)


def build_mock_exam_prompt(subject: Subject, language: str, total_points: int, difficulty: str, context: str, criteria: str, learning_goals: str, performance_context: str = "") -> str:
    """Build a prompt for an exam-style practice paper."""
    prompt = f"""Create a {difficulty} mock exam for {subject.display_name} in {language}.
Total points: {total_points}
Learning goals: {learning_goals or "No learning goals file was found."}
Criteria: {criteria or "No criteria file was found."}
Adaptive performance context: {performance_context or "No performance context."}
Source context: {context or "No source context was found."}

Include exam paper, marking scheme, model answers, point allocation, and sources. {SOURCE_PRIORITY_RULES} {SOURCE_RULES}"""
    return _finalize_prompt(prompt)


def build_study_plan_prompt(subject: Subject, language: str, exam_date: str, hours_per_week: float, weak_topics: str, context: str, learning_goals: str) -> str:
    """Build a study-plan prompt."""
    prompt = f"""Create a study plan for {subject.display_name} in {language}.
Exam date: {exam_date}
Available hours per week: {hours_per_week}
Weak topics: {weak_topics or "No weak topics were entered."}
Learning goals: {learning_goals or "No learning goals file was found."}
Relevant material: {context or "No retrieved source context was found."}

Include schedule, revision tasks, quiz checkpoints, mock exam checkpoints, and priority topics. {SOURCE_PRIORITY_RULES} {SOURCE_RULES}"""
    return _finalize_prompt(prompt)


def build_grading_prompt(subject: Subject, language: str, question: str, student_answer: str, maximum_points: float, marking_scheme: str, context: str, criteria: str) -> str:
    """Build a practice-grading prompt."""
    prompt = f"""Grade this practice answer for {subject.display_name} in {language}.
Question: {question}
Student answer: {student_answer}
Maximum points: {maximum_points}
Marking scheme: {marking_scheme or "No marking scheme was provided."}
Criteria: {criteria or "No criteria file was found."}
Relevant context: {context or "No retrieved source context was found."}

Return points achieved, Swiss grade, strengths, missing points, and an improved answer. Warn that this is practice feedback only. {SOURCE_PRIORITY_RULES} {SOURCE_RULES}"""
    return _finalize_prompt(prompt)


def build_feedback_analysis_prompt(subject: Subject, feature: str, feedback_text: str) -> str:
    """Build a prompt for later manual feedback analysis."""
    return _finalize_prompt(f"Analyze feedback for {subject.display_name}, feature {feature}: {feedback_text}")
