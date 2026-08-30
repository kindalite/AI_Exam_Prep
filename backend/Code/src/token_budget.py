"""Conservative token-budget protection for the local Gemma context window."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContextSection:
    """A named prompt section with priority and text."""

    name: str
    text: str
    priority: int
    source_layer: str = "general"


@dataclass(frozen=True)
class BudgetedContext:
    """Context sections after token-budget packing."""

    sections: list[ContextSection]
    text: str
    estimated_tokens: int
    warnings: list[str] = field(default_factory=list)
    omitted_sections: list[str] = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    """Conservatively estimate tokens without depending on a local tokenizer."""
    if not text:
        return 0
    by_chars = math.ceil(len(text) / 3.2)
    by_words = math.ceil(len(text.split()) * 1.4)
    return max(by_chars, by_words)


def trim_text_to_token_budget(text: str, max_tokens: int) -> str:
    """Trim text to a conservative token budget."""
    if estimate_tokens(text) <= max_tokens:
        return text
    max_chars = max(0, int(max_tokens * 3.0))
    trimmed = text[:max_chars].rstrip()
    while estimate_tokens(trimmed) > max_tokens and trimmed:
        trimmed = trimmed[: int(len(trimmed) * 0.9)].rstrip()
    return trimmed + "\n[Trimmed to stay under the local 128K token limit.]"


def _section_header(section: ContextSection) -> str:
    """Render a context section header."""
    return f"\n\n## {section.name}\n"


def budget_context_sections(sections: list[ContextSection], config) -> BudgetedContext:
    """Pack context sections by source priority within the configured prompt budget."""
    hard_limit = int(getattr(config, "gemma_max_context_tokens", 128000))
    input_limit = int(getattr(config, "max_prompt_input_tokens", 110000))
    reserved = int(getattr(config, "reserved_output_tokens", 8192)) + int(getattr(config, "token_safety_margin", 4096))
    budget = max(1, min(input_limit, hard_limit - reserved))
    per_section_chars = int(getattr(config, "max_chars_per_chunk_in_prompt", 2500))
    kept: list[ContextSection] = []
    warnings: list[str] = []
    omitted: list[str] = []
    running_text = ""
    for section in sorted(sections, key=lambda item: item.priority):
        section_text = section.text or ""
        if len(section_text) > per_section_chars and section.priority > 1:
            section_text = section_text[:per_section_chars].rstrip() + "\n[Section shortened before packing.]"
            warnings.append(f"Trimmed long section: {section.name}")
        candidate_section = ContextSection(section.name, section_text, section.priority, section.source_layer)
        candidate_text = running_text + _section_header(candidate_section) + candidate_section.text
        if estimate_tokens(candidate_text) <= budget:
            kept.append(candidate_section)
            running_text = candidate_text
            continue
        if section.priority <= 2:
            remaining = max(1, budget - estimate_tokens(running_text + _section_header(candidate_section)))
            trimmed = trim_text_to_token_budget(section_text, remaining)
            kept.append(ContextSection(section.name, trimmed, section.priority, section.source_layer))
            running_text = running_text + _section_header(candidate_section) + trimmed
            warnings.append(f"Trimmed required high-priority section: {section.name}")
        else:
            omitted.append(section.name)
            warnings.append(f"Omitted lower-priority section due to token budget: {section.name}")
    return BudgetedContext(kept, running_text.strip(), estimate_tokens(running_text), warnings, omitted)


def assert_prompt_under_limit(prompt: str, config) -> None:
    """Raise a helpful error if a prompt would exceed the hard Gemma limit."""
    limit = int(getattr(config, "gemma_max_context_tokens", 128000))
    tokens = estimate_tokens(prompt)
    if tokens > limit:
        raise ValueError(f"Prompt is estimated at {tokens} tokens, above the hard {limit} token limit.")


def build_token_budget_report(prompt: str, sections: list[ContextSection], config) -> dict:
    """Return a readable report for debugging prompt size."""
    return {
        "estimated_prompt_tokens": estimate_tokens(prompt),
        "hard_limit": int(getattr(config, "gemma_max_context_tokens", 128000)),
        "section_tokens": {section.name: estimate_tokens(section.text) for section in sections},
    }
