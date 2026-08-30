"""Configuration loading for the local-first study assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - depends on optional package installs
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEARNING_MATERIAL_ROOT = Path("/home/kindalite/AI-App/AI_Exam_Prep/learning_material")
DEFAULT_CONDA_ENV_PATH = "~/anaconda3/envs/alim_study_assistant"


@dataclass(frozen=True)
class AppConfig:
    """Typed settings used by the app and tests."""

    project_root: Path
    data_dir: Path
    subject_data_dir: Path
    vector_db_dir: Path
    feedback_file: Path
    stats_file: Path
    model_provider: str
    ollama_host: str
    ollama_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    learning_material_root: Path | None = None
    enable_pdf_page_rendering: bool = True
    pdf_render_dpi: int = 200
    enable_ocr: bool = True
    ocr_languages: str = "deu+eng+fra"
    enable_image_understanding: bool = True
    ollama_vision_model: str = "gemma3:4b"
    enable_audio_input: bool = True
    audio_transcription_backend: str = "whisper_local"
    whisper_model_size: str = "base"
    allow_internet: bool = True
    allow_web_for_private_queries: bool = False
    web_cache_dir: Path | None = None
    syllabus_cache_dir: Path | None = None
    web_search_provider: str = "duckduckgo"
    searxng_url: str = ""
    max_web_results: int = 5
    web_request_timeout_seconds: int = 20
    performance_log_file: Path | None = None
    performance_summary_file: Path | None = None
    adaptive_default_difficulty: bool = True
    ollama_required_model: str = "gemma3:4b"
    auto_pull_ollama_model: bool = True
    allow_model_download: bool = True
    model_download_timeout_seconds: int = 1800
    expected_conda_env_path: str = DEFAULT_CONDA_ENV_PATH
    user_data_root: Path | None = None
    auth_db_file: Path | None = None
    shared_template_root: Path | None = None
    default_template_user_id: str = ""
    enable_user_accounts: bool = True
    gemma_max_context_tokens: int = 128000
    max_prompt_input_tokens: int = 110000
    reserved_output_tokens: int = 8192
    token_safety_margin: int = 4096
    max_retrieved_chunks_per_layer: int = 12
    max_chars_per_chunk_in_prompt: int = 2500
    enable_context_compression: bool = True
    default_quiz_timer_minutes: int = 20
    default_exam_timer_minutes: int = 45
    allow_auto_submit_on_timer_end: bool = True
    hide_solutions_until_graded: bool = True

    @property
    def intelligence_model_label(self) -> str:
        """Return the text model displayed in setup screens."""
        return f"{self.model_provider}:{self.ollama_model}"

    @property
    def vision_model_label(self) -> str:
        """Return the local vision model displayed in setup screens."""
        return self.ollama_vision_model or self.ollama_model


def _env_bool(name: str, default: bool) -> bool:
    """Read a friendly boolean environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_path(name: str, default: Path, root: Path) -> Path:
    """Read a path environment variable and resolve project-relative values."""
    value = Path(os.path.expanduser(os.getenv(name, str(default))))
    if not value.is_absolute():
        value = root / value
    return value


def load_config(project_root: Path | None = None) -> AppConfig:
    """Load environment variables and return an application configuration."""
    root = project_root or PROJECT_ROOT
    if load_dotenv is not None:
        load_dotenv(root / ".env")

    data_dir = root / "data"
    vector_db_dir = _env_path("CHROMA_DB_DIR", root / "vector_db", root)
    web_cache_dir = _env_path("WEB_CACHE_DIR", data_dir / "web_cache", root)
    syllabus_cache_dir = _env_path("SYLLABUS_CACHE_DIR", data_dir / "web_cache" / "syllabus", root)
    performance_log_file = _env_path("PERFORMANCE_LOG_FILE", data_dir / "performance" / "attempts.jsonl", root)
    performance_summary_file = _env_path("PERFORMANCE_SUMMARY_FILE", data_dir / "performance" / "topic_mastery.json", root)

    return AppConfig(
        project_root=root,
        data_dir=data_dir,
        subject_data_dir=data_dir / "subjects",
        vector_db_dir=vector_db_dir,
        feedback_file=data_dir / "feedback" / "feedback.jsonl",
        stats_file=data_dir / "stats" / "grades.csv",
        model_provider=os.getenv("MODEL_PROVIDER", "ollama"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
        learning_material_root=_env_path("LEARNING_MATERIAL_ROOT", DEFAULT_LEARNING_MATERIAL_ROOT, root),
        enable_pdf_page_rendering=_env_bool("ENABLE_PDF_PAGE_RENDERING", True),
        pdf_render_dpi=int(os.getenv("PDF_RENDER_DPI", "200")),
        enable_ocr=_env_bool("ENABLE_OCR", True),
        ocr_languages=os.getenv("OCR_LANGUAGES", "deu+eng+fra"),
        enable_image_understanding=_env_bool("ENABLE_IMAGE_UNDERSTANDING", True),
        ollama_vision_model=os.getenv("OLLAMA_VISION_MODEL", os.getenv("OLLAMA_MODEL", "gemma3:4b")),
        enable_audio_input=_env_bool("ENABLE_AUDIO_INPUT", True),
        audio_transcription_backend=os.getenv("AUDIO_TRANSCRIPTION_BACKEND", "whisper_local"),
        whisper_model_size=os.getenv("WHISPER_MODEL_SIZE", "base"),
        allow_internet=_env_bool("ALLOW_INTERNET", True),
        allow_web_for_private_queries=_env_bool("ALLOW_WEB_FOR_PRIVATE_QUERIES", False),
        web_cache_dir=web_cache_dir,
        syllabus_cache_dir=syllabus_cache_dir,
        web_search_provider=os.getenv("WEB_SEARCH_PROVIDER", "duckduckgo"),
        searxng_url=os.getenv("SEARXNG_URL", ""),
        max_web_results=int(os.getenv("MAX_WEB_RESULTS", "5")),
        web_request_timeout_seconds=int(os.getenv("WEB_REQUEST_TIMEOUT_SECONDS", "20")),
        performance_log_file=performance_log_file,
        performance_summary_file=performance_summary_file,
        adaptive_default_difficulty=_env_bool("ADAPTIVE_DEFAULT_DIFFICULTY", True),
        ollama_required_model=os.getenv("OLLAMA_REQUIRED_MODEL", "gemma3:4b"),
        auto_pull_ollama_model=_env_bool("AUTO_PULL_OLLAMA_MODEL", True),
        allow_model_download=_env_bool("ALLOW_MODEL_DOWNLOAD", True),
        model_download_timeout_seconds=int(os.getenv("MODEL_DOWNLOAD_TIMEOUT_SECONDS", "1800")),
        expected_conda_env_path=os.getenv("EXPECTED_CONDA_ENV_PATH", DEFAULT_CONDA_ENV_PATH),
        user_data_root=_env_path("USER_DATA_ROOT", data_dir / "users", root),
        auth_db_file=_env_path("AUTH_DB_FILE", data_dir / "auth" / "users.json", root),
        shared_template_root=_env_path("SHARED_TEMPLATE_ROOT", data_dir / "shared_templates" / "default_student_material", root),
        default_template_user_id=os.getenv("DEFAULT_TEMPLATE_USER_ID", ""),
        enable_user_accounts=_env_bool("ENABLE_USER_ACCOUNTS", True),
        gemma_max_context_tokens=int(os.getenv("GEMMA_MAX_CONTEXT_TOKENS", "128000")),
        max_prompt_input_tokens=int(os.getenv("MAX_PROMPT_INPUT_TOKENS", "110000")),
        reserved_output_tokens=int(os.getenv("RESERVED_OUTPUT_TOKENS", "8192")),
        token_safety_margin=int(os.getenv("TOKEN_SAFETY_MARGIN", "4096")),
        max_retrieved_chunks_per_layer=int(os.getenv("MAX_RETRIEVED_CHUNKS_PER_LAYER", "12")),
        max_chars_per_chunk_in_prompt=int(os.getenv("MAX_CHARS_PER_CHUNK_IN_PROMPT", "2500")),
        enable_context_compression=_env_bool("ENABLE_CONTEXT_COMPRESSION", True),
        default_quiz_timer_minutes=int(os.getenv("DEFAULT_QUIZ_TIMER_MINUTES", "20")),
        default_exam_timer_minutes=int(os.getenv("DEFAULT_EXAM_TIMER_MINUTES", "45")),
        allow_auto_submit_on_timer_end=_env_bool("ALLOW_AUTO_SUBMIT_ON_TIMER_END", True),
        hide_solutions_until_graded=_env_bool("HIDE_SOLUTIONS_UNTIL_GRADED", True),
    )
