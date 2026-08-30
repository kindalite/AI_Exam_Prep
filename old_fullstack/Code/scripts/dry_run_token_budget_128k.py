"""Dry-run the 128K token budget with synthetic overlarge context."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.token_budget import ContextSection, budget_context_sections, estimate_tokens


def main() -> int:
    config = load_config(PROJECT_ROOT)
    huge = "local material " * 40000
    sections = [
        ContextSection("current question", "Explain DNA", 1),
        ContextSection("local material", huge, 2),
        ContextSection("syllabus", "syllabus " * 20000, 4),
        ContextSection("web", "web " * 50000, 7),
    ]
    budgeted = budget_context_sections(sections, config)
    assert estimate_tokens(budgeted.text) < config.gemma_max_context_tokens
    assert "Explain DNA" in budgeted.text
    assert "local material" in budgeted.text
    assert budgeted.warnings
    print("PASS: overlarge context packed under 128K")
    print("PASS: high-priority question retained and lower-priority sections trimmed/omitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
