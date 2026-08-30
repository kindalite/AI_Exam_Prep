"""Strict JSON model-output parsing with one constrained repair attempt."""

from __future__ import annotations

import json
import re
from typing import Callable

from ..config import AppConfig
from ..llm_client import LLMResponse


class StructuredModelUnavailableError(RuntimeError):
    """The configured model could not produce a response."""


class InvalidStructuredOutputError(ValueError):
    """Model output remained malformed after one repair attempt."""


def parse_json_object(text: str) -> dict:
    """Parse one JSON object, accepting only removable Markdown fences."""
    candidate = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidStructuredOutputError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise InvalidStructuredOutputError("The model output must be one JSON object")
    return value


def call_structured_model(
    *,
    prompt: str,
    system_prompt: str,
    config: AppConfig,
    call_llm: Callable[..., LLMResponse],
    validate: Callable[[dict], object],
) -> object:
    """Call, parse, validate, and at most once repair structured model output."""
    response = call_llm(prompt, system_prompt, config=config)
    if not response.ok or not response.text.strip():
        raise StructuredModelUnavailableError(response.error or "The model returned no output")
    try:
        return validate(parse_json_object(response.text))
    except (InvalidStructuredOutputError, TypeError, ValueError, KeyError) as first_error:
        repair_prompt = (
            "Repair the following output into exactly one valid JSON object matching the original "
            "requested schema. Do not add Markdown or commentary. Preserve only supported fields.\n\n"
            f"Validation error: {first_error}\n\nOriginal output:\n{response.text}"
        )
        repaired = call_llm(repair_prompt, system_prompt, config=config)
        if not repaired.ok or not repaired.text.strip():
            raise StructuredModelUnavailableError(repaired.error or "The repair call failed")
        try:
            return validate(parse_json_object(repaired.text))
        except (InvalidStructuredOutputError, TypeError, ValueError, KeyError) as exc:
            raise InvalidStructuredOutputError(
                f"Structured model output failed validation after one repair: {exc}"
            ) from exc
