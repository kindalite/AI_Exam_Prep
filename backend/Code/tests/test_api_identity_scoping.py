"""Isolation tests for the Stage-1 API identity and retrieval bridge."""

from __future__ import annotations

import pytest

from src.services.identity_service import StudentContext, resolve_student_context
from src.services.retrieval_service import index_student_subject, retrieve_student_study_context
from src.user_data_paths import ensure_user_data_structure, get_user_root, get_user_subject_root, user_subject_collection_name
from src.vector_store import InMemoryVectorStore


def _write_note(student: StudentContext, subject_key: str, name: str, text: str, temp_config) -> None:
    ensure_user_data_structure(student.student_id, temp_config, [subject_key])
    path = get_user_subject_root(student.student_id, subject_key, temp_config) / "notes" / name
    path.write_text(text, encoding="utf-8")


def test_two_students_have_isolated_paths_collections_and_retrieval(temp_config) -> None:
    """Student A must never retrieve Student B's private indexed material."""
    student_a = StudentContext("Student A")
    student_b = StudentContext("Student B")
    assert get_user_root(student_a.student_id, temp_config) != get_user_root(student_b.student_id, temp_config)
    assert user_subject_collection_name(student_a.student_id, "biology") != user_subject_collection_name(student_b.student_id, "biology")

    _write_note(student_a, "biology", "a.md", "alpha-only private mitochondria", temp_config)
    _write_note(student_b, "biology", "b.md", "beta-only private chloroplast", temp_config)
    store = InMemoryVectorStore()
    index_student_subject(student_a, "biology", temp_config, vector_store=store)
    index_student_subject(student_b, "biology", temp_config, vector_store=store)

    result_a = retrieve_student_study_context(
        student_a,
        "biology",
        "alpha mitochondria",
        temp_config,
        include_memory=False,
        vector_store=store,
    )
    result_b = retrieve_student_study_context(
        student_b,
        "biology",
        "alpha mitochondria",
        temp_config,
        include_memory=False,
        vector_store=store,
    )
    assert "alpha-only" in result_a.context.local_context
    assert "alpha-only" not in result_b.context.local_context
    assert "Learning Goals" in result_a.context.local_context
    assert "Learning Goals" in result_b.context.local_context
    assert all(
        source.metadata.get("user_id") in {None, student_a.student_id}
        for source in result_a.context.sources
    )


def test_spf_component_scope_and_material_filter(temp_config) -> None:
    """A selected SPF component cannot retrieve the sibling component corpus."""
    student = StudentContext("spf-user")
    _write_note(student, "spf_biology", "bio.md", "advanced biology marker", temp_config)
    _write_note(student, "spf_chemistry", "chem.md", "advanced chemistry marker", temp_config)
    store = InMemoryVectorStore()
    index_student_subject(student, "spf_biology_chemistry", temp_config, vector_store=store)

    biology = retrieve_student_study_context(
        student,
        "spf_biology_chemistry",
        "advanced marker",
        temp_config,
        component_subject_id="spf_biology",
        material_ids=["bio.md"],
        include_shared=False,
        include_memory=False,
        vector_store=store,
    )
    combined = "\n".join(source.text for source in biology.context.sources)
    assert biology.corpus_keys == ("spf_biology",)
    assert "advanced biology" in combined
    assert "advanced chemistry" not in combined


def test_raw_identity_is_sanitized_and_cannot_escape_user_root(temp_config) -> None:
    """Path-like IDs stay below the configured user-data root."""
    student = resolve_student_context("../../Outside Student")
    configured_root = (temp_config.user_data_root or temp_config.data_dir / "users").resolve()
    resolved_user_root = get_user_root(student.student_id, temp_config).resolve()
    assert resolved_user_root.is_relative_to(configured_root)
    assert "/" not in student.student_id and ".." not in student.student_id
    with pytest.raises(ValueError, match="X-Student-Id"):
        resolve_student_context(None)
    fallback = resolve_student_context(None, fallback_student_id="Developer")
    assert fallback.student_id == "developer"
