"""Tests for conservative token budgeting."""

from __future__ import annotations

from src.token_budget import ContextSection, budget_context_sections, estimate_tokens, trim_text_to_token_budget


def test_token_estimate_is_conservative() -> None:
    assert estimate_tokens("one two three") >= 5


def test_huge_context_is_trimmed_under_limit(temp_config) -> None:
    huge = "local " * 120000
    budgeted = budget_context_sections([ContextSection("question", "keep me", 1), ContextSection("local", huge, 2), ContextSection("web", huge, 7)], temp_config)
    assert estimate_tokens(budgeted.text) < temp_config.gemma_max_context_tokens
    assert "keep me" in budgeted.text
    assert budgeted.warnings
    assert estimate_tokens(trim_text_to_token_budget(huge, 1000)) <= 1100
