"""Local per-user storage for generated practice, solutions, answers, and reports."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .document_loaders import LoadedDocument
from .user_data_paths import get_user_root, relative_to_user, sanitize_username
from .utils import ensure_directory, utc_timestamp


@dataclass(frozen=True)
class GeneratedPracticeRecord:
    """A generated quiz or exam question set plus hidden solution location."""

    practice_id: str
    user_id: str
    subject_key: str
    mode: str
    timestamp: str
    language: str
    topic: str
    learning_goal: str | None
    difficulty_requested: str
    difficulty_used: str
    timer_seconds: int
    question_set: str
    solution_set_path: str
    visibility: str = "user_visible"
    sources: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class SolutionSetRecord:
    """A hidden solution set that is revealed only after grading."""

    solution_id: str
    practice_id: str
    user_id: str
    subject_key: str
    mode: str
    timestamp: str
    solution_set: str
    visibility: str = "hidden_until_finished"


@dataclass(frozen=True)
class PerformanceReportRecord:
    """A grading and study-improvement report for one attempt."""

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
    visibility: str = "user_visible"


def new_generated_practice(**kwargs) -> GeneratedPracticeRecord:
    """Create a generated practice record with defaults."""
    data = {
        "practice_id": uuid.uuid4().hex,
        "user_id": "default",
        "subject_key": "general",
        "mode": "quiz",
        "timestamp": utc_timestamp(),
        "language": "German",
        "topic": "",
        "learning_goal": None,
        "difficulty_requested": "adaptive",
        "difficulty_used": "easy",
        "timer_seconds": 1200,
        "question_set": "",
        "solution_set_path": "",
        "visibility": "user_visible",
        "sources": [],
    }
    data.update(kwargs)
    data["user_id"] = sanitize_username(data["user_id"])
    return GeneratedPracticeRecord(**data)


def new_solution_set(**kwargs) -> SolutionSetRecord:
    """Create a hidden solution set record with defaults."""
    data = {"solution_id": uuid.uuid4().hex, "practice_id": "", "user_id": "default", "subject_key": "general", "mode": "quiz", "timestamp": utc_timestamp(), "solution_set": "", "visibility": "hidden_until_finished"}
    data.update(kwargs)
    data["user_id"] = sanitize_username(data["user_id"])
    return SolutionSetRecord(**data)


def new_performance_report(**kwargs) -> PerformanceReportRecord:
    """Create a performance report record with defaults."""
    data = {"report_id": uuid.uuid4().hex, "user_id": "default", "subject_key": "general", "practice_id": "", "timestamp": utc_timestamp(), "points_achieved": 0.0, "maximum_points": 1.0, "grade": 1.0, "strengths": [], "weaknesses": [], "recommended_actions": [], "source_layers_used": []}
    data.update(kwargs)
    data["user_id"] = sanitize_username(data["user_id"])
    return PerformanceReportRecord(**data)


def _append_jsonl(path: Path, row: dict) -> dict:
    """Append one row to a JSONL file."""
    ensure_directory(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _practice_dir(user_id: str, mode: str, config) -> Path:
    """Return the generated practice folder for a mode."""
    folder = "exams" if mode == "exam" else "quizzes"
    return get_user_root(user_id, config) / "generated_practice" / folder


def save_solution_set(record: SolutionSetRecord, config) -> dict:
    """Persist a hidden solution set locally."""
    path = get_user_root(record.user_id, config) / "generated_practice" / "solution_sets" / f"{record.practice_id}.json"
    ensure_directory(path.parent)
    row = asdict(record)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    return row | {"path": str(path)}


def save_generated_quiz(record: GeneratedPracticeRecord, config) -> dict:
    """Save a generated quiz record."""
    return _save_generated_practice(record, config)


def save_generated_exam(record: GeneratedPracticeRecord, config) -> dict:
    """Save a generated exam record."""
    return _save_generated_practice(record, config)


def _save_generated_practice(record: GeneratedPracticeRecord, config) -> dict:
    """Save generated practice metadata and question text."""
    path = _practice_dir(record.user_id, record.mode, config) / f"{record.practice_id}.json"
    ensure_directory(path.parent)
    row = asdict(record)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    return row | {"path": str(path)}


def save_submitted_answers(user_id: str, practice_id: str, subject_key: str, mode: str, answers: str, config) -> dict:
    """Save submitted answers for a timed quiz or exam."""
    row = {"answer_id": uuid.uuid4().hex, "practice_id": practice_id, "user_id": sanitize_username(user_id), "subject_key": subject_key, "mode": mode, "timestamp": utc_timestamp(), "answers": answers, "source_layer": "student_answer", "visibility": "user_visible"}
    filename = "exam_attempts.jsonl" if mode == "exam" else "quiz_attempts.jsonl"
    return _append_jsonl(get_user_root(user_id, config) / "attempts" / filename, row)


def save_performance_report(record: PerformanceReportRecord, config) -> dict:
    """Save a performance report for RAG and dashboard use."""
    return _append_jsonl(get_user_root(record.user_id, config) / "reports" / "performance_reports.jsonl", asdict(record))


def _read_json_files(folder: Path) -> list[dict]:
    """Read JSON files from a folder."""
    if not folder.exists():
        return []
    rows = []
    for path in sorted(folder.glob("*.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")) | {"_path": str(path)})
        except Exception:
            continue
    return rows


def practice_records_to_documents(user_id: str, config, subject_key: str | None = None) -> list[LoadedDocument]:
    """Convert practice records and reports into RAG documents."""
    documents: list[LoadedDocument] = []
    root = get_user_root(user_id, config)
    for mode, layer in [("quizzes", "generated_quiz"), ("exams", "generated_exam")]:
        for row in _read_json_files(root / "generated_practice" / mode):
            if subject_key and row.get("subject_key") != subject_key:
                continue
            metadata = {
                "user_id": sanitize_username(user_id),
                "session_id": row.get("practice_id", ""),
                "subject": row.get("subject_key", "general"),
                "subject_key": row.get("subject_key", "general"),
                "feature": row.get("mode", "quiz"),
                "source_layer": layer,
                "source_type": "generated_practice",
                "timestamp": row.get("timestamp", ""),
                "language": row.get("language", ""),
                "topic": row.get("topic", ""),
                "learning_goal": row.get("learning_goal") or "",
                "source_name": f"{layer}_{row.get('practice_id', 'practice')}",
                "file_name": Path(row.get("_path", "practice.json")).name,
                "file_path_or_relative_path": relative_to_user(Path(row.get("_path", root)), user_id, config),
                "modality": "quiz" if layer == "generated_quiz" else "exam",
                "visibility": row.get("visibility", "user_visible"),
            }
            documents.append(LoadedDocument(row.get("question_set", ""), metadata))
    report_path = root / "reports" / "performance_reports.jsonl"
    if report_path.exists():
        for line in report_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if subject_key and row.get("subject_key") != subject_key:
                continue
            text = "\n".join(["Performance report", f"Strengths: {', '.join(row.get('strengths', []))}", f"Weaknesses: {', '.join(row.get('weaknesses', []))}", f"Recommended actions: {', '.join(row.get('recommended_actions', []))}"])
            metadata = {"user_id": sanitize_username(user_id), "session_id": row.get("practice_id", ""), "subject": row.get("subject_key", "general"), "subject_key": row.get("subject_key", "general"), "feature": "performance", "source_layer": "performance_report", "source_type": "report", "timestamp": row.get("timestamp", ""), "language": "", "topic": "", "learning_goal": "", "source_name": f"performance_report_{row.get('report_id', row.get('practice_id', 'report'))}", "file_name": "performance_reports.jsonl", "file_path_or_relative_path": relative_to_user(report_path, user_id, config), "modality": "report", "visibility": row.get("visibility", "user_visible")}
            documents.append(LoadedDocument(text, metadata))
    return documents
