"""Feature test for the mocked multimodal adaptive pipeline."""

from __future__ import annotations

from dataclasses import replace

from src.adaptive_learning import choose_adaptive_difficulty
from src.chunking import chunk_documents
from src.document_loaders import LoadedDocument
from src.grader import calculate_grade
from src.material_router import discover_learning_material, group_material_by_subject
from src.performance_tracker import new_attempt, read_practice_attempts, save_practice_attempt
from src.prompts import build_multimodal_chat_prompt, build_quiz_prompt
from src.subject_registry import build_subject_registry
from src.vector_store import InMemoryVectorStore, RetrievedChunk


def test_end_to_end_multimodal_adaptive_feature(tmp_path, temp_config) -> None:
    """Exercise the real pipeline with fake local data and no external services."""
    material_root = tmp_path / "learning_material"
    (material_root / "Chemie").mkdir(parents=True)
    private_file = material_root / "Chemie" / "reaction.pdf"
    private_file.write_bytes(b"fake pdf")
    config = replace(temp_config, learning_material_root=material_root, allow_internet=False)
    subjects = build_subject_registry(config)
    subject = subjects["chemistry"]

    grouped = group_material_by_subject(discover_learning_material(config), subjects)
    assert private_file in grouped["chemistry"]

    docs = [
        LoadedDocument("Selectable text about reactions", {"source_name": "reaction.pdf", "source_layer": "local_material", "page_number": 1, "modality": "pdf_text", "subject": subject.key}),
        LoadedDocument("OCR text about ions", {"source_name": "reaction.pdf", "source_layer": "local_material", "page_number": 1, "modality": "ocr_text", "subject": subject.key}),
        LoadedDocument("Image description of molecule drawing", {"source_name": "reaction.pdf", "source_layer": "local_material", "page_number": 1, "modality": "page_image_description", "subject": subject.key}),
    ]
    chunks = chunk_documents(docs, 120, 20)
    store = InMemoryVectorStore()
    store.rebuild_collection(subject.collection_name, chunks)
    local = store.query(subject.collection_name, "ions reactions", top_k=3)
    syllabus = RetrievedChunk("Official KSA syllabus chemistry", {"source_layer": "official_syllabus", "source_name": "KSA", "url": "https://ksalpenquai.lu.ch"}, 1.0)
    web = RetrievedChunk("Public web explanation", {"source_layer": "web", "source_name": "Public", "url": "https://example.test"}, 1.0)

    save_practice_attempt(new_attempt(subject_key=subject.key, topic="ions", points_achieved=4, maximum_points=10, grade=3.0), config)
    difficulty = choose_adaptive_difficulty(subject.key, "ions", config)
    prompt_de = build_multimodal_chat_prompt(subject, "German", "Was sind Ionen?", "\n".join(item.text for item in local), syllabus.text, web.text, "performance context", audio_transcript="audio text", image_ocr="ocr text", image_description="image text", warnings=["optional tool warning"])
    prompt_en = build_multimodal_chat_prompt(subject, "English", "What are ions?", "local", "syllabus", "", "performance")
    prompt_fr = build_multimodal_chat_prompt(subject, "French", "Que sont les ions?", "local", "syllabus", "", "performance")
    quiz_prompt = build_quiz_prompt(subject, "German", "ions", difficulty, prompt_de, "criteria", "performance", ["ions"])
    grade = calculate_grade(4, 10)
    attempts = read_practice_attempts(config, subject.key)

    assert "reaction.pdf" in str(local[0].metadata)
    assert local[0].metadata["source_layer"] == "local_material"
    assert syllabus.metadata["source_layer"] == "official_syllabus"
    assert web.metadata["source_layer"] == "web"
    assert "https://ksalpenquai.lu.ch" in syllabus.metadata["url"]
    assert "German" in prompt_de and "English" in prompt_en and "French" in prompt_fr
    assert "Source priority rules" in prompt_de
    assert "audio text" in prompt_de and "ocr text" in prompt_de and "image text" in prompt_de
    assert difficulty == "easy"
    assert "easy" in quiz_prompt
    assert grade.grade == 3.0
    assert attempts
    assert config.allow_internet is False
