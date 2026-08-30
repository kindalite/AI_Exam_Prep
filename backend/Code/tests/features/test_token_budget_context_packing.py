"""Feature test for 128K token context packing."""

from __future__ import annotations

from src.token_budget import ContextSection, budget_context_sections, estimate_tokens


def test_token_budget_context_packing(temp_config) -> None:
    huge_local = "local material important " * 30000
    huge_web = "public web low priority " * 60000
    sections = [
        ContextSection("current question", "Explain the DNA diagram", 1, "current_question"),
        ContextSection("local material", huge_local, 2, "local_material"),
        ContextSection("syllabus", "official syllabus " * 10000, 4, "official_syllabus"),
        ContextSection("chat history", "old answer " * 10000, 6, "generated_quiz"),
        ContextSection("web", huge_web, 7, "public_web"),
    ]
    budgeted = budget_context_sections(sections, temp_config)
    assert estimate_tokens(budgeted.text) < temp_config.gemma_max_context_tokens
    assert "Explain the DNA diagram" in budgeted.text
    assert "local material" in budgeted.text
    assert budgeted.warnings
