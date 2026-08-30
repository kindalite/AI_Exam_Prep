"""Explicitly opt-in remote OpenAI-compatible/vLLM generation smoke test."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.llm_client import generate_response


def main() -> int:
    """Call the configured remote endpoint only after an explicit environment opt-in."""
    if os.getenv("RUN_REMOTE_LLM_SMOKE") != "1":
        print("SKIP: set RUN_REMOTE_LLM_SMOKE=1 to call the configured remote model")
        return 0
    config = load_config(PROJECT_ROOT)
    if config.model_provider.lower() not in {"openai_compatible", "vllm"}:
        print("FAIL: MODEL_PROVIDER must be openai_compatible or vllm")
        return 1
    response = generate_response("Reply with exactly: PASS", config=config)
    if not response.ok:
        print(f"FAIL: {response.error}")
        return 1
    print(f"PASS: remote model replied: {response.text.strip()[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
