"""Focused tests for Prompt 8 stability and grounding scaffolding."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.app_logging import append_log, ensure_log_directories, redact_value
from src.dependency_health import _expected_torchvision_minor
from src.document_loaders import SUPPORTED_EXTENSIONS, load_document
from src.model_runtime import build_chat_payload
from src.operation_tracker import OperationTracker
from src.source_citations import group_sources
from src.source_policy import is_trusted_source, sanitize_public_query
from src.subject_languages import language_for_subject, language_instruction
from src.web_permission import permission_from_choice


def test_torchvision_minor_matches_torch_minor_rule() -> None:
    assert _expected_torchvision_minor("2.13.0+cu130") == 28
    assert _expected_torchvision_minor("1.13.1") == 14


def test_safe_logging_redacts_and_caps_private_text(temp_config) -> None:
    folders = ensure_log_directories(temp_config)
    assert folders["app_runs"].exists()
    redacted = redact_value({"password": "secret", "note": "token=abc123 " + "x" * 500})
    assert redacted["password"] == "[REDACTED]"
    assert "abc123" not in redacted["note"]
    row = append_log(folders["app_runs"] / "test.jsonl", "event", redacted)
    assert row["event"] == "event"


def test_operation_tracker_records_recoverable_states(temp_config) -> None:
    tracker = OperationTracker(temp_config, slow_threshold_seconds=0)
    state = tracker.start("indexing", "reading files")
    updated = tracker.update(state.operation_id, "chunking")
    assert updated.warnings
    done = tracker.succeed(state.operation_id)
    assert done.status == "success"


def test_ollama_payload_uses_keep_alive_and_stream_flag() -> None:
    payload = build_chat_payload("Hi", "System", "gemma3:4b", stream=True)
    assert payload["stream"] is True
    assert payload["keep_alive"] == "10m"
    assert payload["messages"][0]["role"] == "system"


def test_subject_language_mapping_and_french_instruction() -> None:
    assert language_for_subject("mathematics") == "English"
    assert language_for_subject("physics") == "English"
    assert language_for_subject("spf_chemistry") == "German"
    assert language_for_subject("french") == "French"
    assert "CEFR B1" in language_instruction("French")


def test_svg_loading_extracts_text_and_warns_on_scripts(tmp_path: Path) -> None:
    path = tmp_path / "diagram.svg"
    path.write_text("<svg><title>Cell diagram</title><text>Nucleus</text><script>alert(1)</script></svg>", encoding="utf-8")
    docs = load_document(path, "biology")
    assert ".svg" in SUPPORTED_EXTENSIONS
    assert "Cell diagram" in docs[0].text
    assert "Nucleus" in docs[0].text
    assert "svg_warning" in docs[0].metadata


def test_source_policy_sanitizes_and_classifies_sources() -> None:
    query = sanitize_public_query("alim@example.com photosynthesis chapter 12345", "Biology")
    assert "@" not in query
    assert "12345" not in query
    assert is_trusted_source("https://www.lu.ch/schulen/lehrplan")
    assert not is_trusted_source("https://example.com/chegg-answer-farm")


def test_source_grouping_uses_required_headings() -> None:
    sources = [SimpleNamespace(metadata={"source_layer": "public_web", "source_name": "KSA", "url": "https://ksalpenquai.lu.ch"})]
    grouped = group_sources(sources)
    assert "From your materials" in grouped
    assert "From approved online sources" in grouped
    assert grouped["From approved online sources"]


def test_web_permission_choice() -> None:
    assert permission_from_choice("Search internet", remember=True).allowed is True
    assert permission_from_choice("Use local material only").allowed is False
