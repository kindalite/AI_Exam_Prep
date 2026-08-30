"""Contract and isolation tests for subject, goal, and material read APIs."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.dependencies import get_config
from src.api.main import create_app
from src.subject_registry import TOP_LEVEL_SUBJECT_IDS
from src.user_data_paths import ensure_user_data_structure, get_user_subject_root


def _client(temp_config) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    return TestClient(app)


def test_subject_catalog_has_exact_order_languages_and_no_grade_state(temp_config) -> None:
    """The backend enriches but never redefines frontend cards or grade state."""
    with _client(temp_config) as client:
        response = client.get("/api/subjects")
    assert response.status_code == 200
    subjects = response.json()
    assert [subject["subject_id"] for subject in subjects] == list(TOP_LEVEL_SUBJECT_IDS)
    assert len(subjects) == 15
    languages = {subject["subject_id"]: subject["language"] for subject in subjects}
    assert languages["french"] == "fr"
    assert languages["history"] == "en"
    assert languages["german"] == "de"
    spf = next(subject for subject in subjects if subject["subject_id"] == "spf_biology_chemistry")
    assert [item["subject_id"] for item in spf["components"]] == ["spf_biology", "spf_chemistry"]
    assert not ({"grade", "average_grade", "color"} & set(subjects[0]))


def test_subject_detail_aggregates_spf_and_reports_structured_errors(temp_config) -> None:
    """SPF metadata uses component corpora and invalid IDs use the error envelope."""
    with _client(temp_config) as client:
        combined = client.get("/api/subjects/spf_biology_chemistry")
        biology = client.get(
            "/api/subjects/spf_biology_chemistry",
            params={"component_subject_id": "spf_biology"},
        )
        unknown = client.get("/api/subjects/not-a-subject", headers={"X-Request-Id": "subject-404"})
        invalid_component = client.get(
            "/api/subjects/history",
            params={"component_subject_id": "spf_biology"},
        )

    assert combined.status_code == 200
    assert combined.json()["corpus_keys"] == ["spf_biology", "spf_chemistry"]
    assert biology.json()["corpus_keys"] == ["spf_biology"]
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "subject_not_found"
    assert unknown.json()["error"]["request_id"] == "subject-404"
    assert invalid_component.status_code == 422
    assert invalid_component.json()["error"]["code"] == "invalid_subject_component"


def test_learning_goals_use_user_file_then_canonical_and_filter_topic(temp_config) -> None:
    """Anonymous reads are canonical while identified reads stay user-scoped."""
    canonical = temp_config.subject_data_dir / "history" / "learning_goals.md"
    canonical.write_text("# History goals\n- Explain canonical causes\n", encoding="utf-8")
    ensure_user_data_structure("student-a", temp_config, ["history"])
    ensure_user_data_structure("student-b", temp_config, ["history"])
    (get_user_subject_root("student-a", "history", temp_config) / "learning_goals.md").write_text(
        "# A goals\n- Analyze alpha archive\n", encoding="utf-8"
    )
    (get_user_subject_root("student-b", "history", temp_config) / "learning_goals.md").write_text(
        "# B goals\n- Compare beta source\n", encoding="utf-8"
    )

    with _client(temp_config) as client:
        shared = client.get("/api/subjects/history/learning-goals")
        student_a = client.get(
            "/api/subjects/history/learning-goals",
            headers={"X-Student-Id": "student-a"},
            params={"topic": "alpha"},
        )
        student_b = client.get(
            "/api/subjects/history/learning-goals",
            headers={"X-Student-Id": "student-b"},
        )

    assert "canonical causes" in shared.json()[0]["text"]
    assert len(student_a.json()) == 1 and "alpha archive" in student_a.json()[0]["text"]
    assert all("beta" not in goal["text"] for goal in student_a.json())
    assert "beta source" in student_b.json()[0]["text"]
    assert student_a.json()[0]["source"]["source_layer"] == "user_learning_goals"


def test_material_inventory_shared_mode_and_two_user_isolation(temp_config) -> None:
    """Private files appear only with the matching sanitized student identity."""
    for student, file_name in [("student-a", "alpha.jpg"), ("student-b", "beta.pdf")]:
        ensure_user_data_structure(student, temp_config, ["chemistry"])
        path = get_user_subject_root(student, "chemistry", temp_config) / "notes" / file_name
        path.write_bytes(b"private")

    with _client(temp_config) as client:
        shared = client.get("/api/subjects/chemistry/materials")
        student_a = client.get(
            "/api/subjects/chemistry/materials",
            headers={"X-Student-Id": "student-a"},
        )
        student_b = client.get(
            "/api/subjects/chemistry/materials",
            headers={"X-Student-Id": "student-b"},
        )

    shared_names = {item["file_name"] for item in shared.json()}
    a_items = {item["file_name"]: item for item in student_a.json()}
    b_names = {item["file_name"] for item in student_b.json()}
    assert "alpha.jpg" not in shared_names and "beta.pdf" not in shared_names
    assert "alpha.jpg" in a_items and "beta.pdf" not in a_items
    assert "beta.pdf" in b_names and "alpha.jpg" not in b_names
    assert a_items["alpha.jpg"]["media_type"] == "jpeg"
    assert "path" not in a_items["alpha.jpg"]

