"""Prompt templates for subject chat, quizzes, exams, planning, and grading."""

from __future__ import annotations

from .subject_registry import Subject


SOURCE_RULES = (
    "Use only the provided notes, syllabus, learning goals, exam criteria, and retrieved sources. "
    "If source material is insufficient, say that clearly. Include source file names when possible. "
    "Do not invent exam rules that are not present in the sources."
)


def build_system_prompt(subject: Subject, language: str) -> str:
    """Create a reusable system prompt for one subject and language."""
    return (
        f"You are Alim Study Assistant for {subject.display_name}. "
        f"Answer in {language}. Subject instructions: {subject.instructions} {SOURCE_RULES}"
    )


def build_chat_prompt(subject: Subject, language: str, question: str, context: str, learning_goals: str, criteria: str) -> str:
    """Build the prompt for subject question answering."""
    return f"""Subject: {subject.display_name}
Language: {language}

Learning goals:
{learning_goals or "No learning goals file was found."}

Exam criteria:
{criteria or "No exam criteria file was found."}

Retrieved source context:
{context or "No retrieved source context was found."}

Student question:
{question}

Task: Answer clearly, explain the reasoning, and list useful source names."""


def build_quiz_prompt(subject: Subject, language: str, learning_goal: str, difficulty: str, context: str, criteria: str) -> str:
    """Build a quiz-generation prompt."""
    return f"""Create a {difficulty} quiz for {subject.display_name} in {language}.
Learning goal: {learning_goal or "Use the most relevant available goals."}
Subject criteria: {criteria or "No criteria file was found."}
Source context: {context or "No source context was found."}

Include questions, answer key, short explanations, and source references. {SOURCE_RULES}"""


def build_mock_exam_prompt(subject: Subject, language: str, total_points: int, difficulty: str, context: str, criteria: str, learning_goals: str) -> str:
    """Build a prompt for an exam-style practice paper."""
    return f"""Create a {difficulty} mock exam for {subject.display_name} in {language}.
Total points: {total_points}
Learning goals: {learning_goals or "No learning goals file was found."}
Criteria: {criteria or "No criteria file was found."}
Source context: {context or "No source context was found."}

Include exam paper, marking scheme, model answers, point allocation, and sources. {SOURCE_RULES}"""


def build_study_plan_prompt(subject: Subject, language: str, exam_date: str, hours_per_week: float, weak_topics: str, context: str, learning_goals: str) -> str:
    """Build a study-plan prompt."""
    return f"""Create a study plan for {subject.display_name} in {language}.
Exam date: {exam_date}
Available hours per week: {hours_per_week}
Weak topics: {weak_topics or "No weak topics were entered."}
Learning goals: {learning_goals or "No learning goals file was found."}
Relevant material: {context or "No retrieved source context was found."}

Include schedule, revision tasks, quiz checkpoints, mock exam checkpoints, and priority topics. {SOURCE_RULES}"""


def build_grading_prompt(subject: Subject, language: str, question: str, student_answer: str, maximum_points: float, marking_scheme: str, context: str, criteria: str) -> str:
    """Build a practice-grading prompt."""
    return f"""Grade this practice answer for {subject.display_name} in {language}.
Question: {question}
Student answer: {student_answer}
Maximum points: {maximum_points}
Marking scheme: {marking_scheme or "No marking scheme was provided."}
Criteria: {criteria or "No criteria file was found."}
Relevant context: {context or "No retrieved source context was found."}

Return points achieved, Swiss grade, strengths, missing points, and an improved answer. Warn that this is practice feedback only. {SOURCE_RULES}"""


def build_feedback_analysis_prompt(subject: Subject, feature: str, feedback_text: str) -> str:
    """Build a prompt for later manual feedback analysis."""
    return f"Analyze feedback for {subject.display_name}, feature {feature}: {feedback_text}"

