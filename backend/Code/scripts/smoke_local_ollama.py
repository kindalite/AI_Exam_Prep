"""Explicitly opt-in local Ollama generation smoke test."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.llm_client import generate_response


def main() -> int:
    """Call local Ollama only after an explicit environment opt-in."""
    if os.getenv("RUN_LOCAL_OLLAMA_SMOKE") != "1":
        print("SKIP: set RUN_LOCAL_OLLAMA_SMOKE=1 to call local Ollama")
        return 0
    config = load_config(PROJECT_ROOT)
    if config.model_provider.lower() != "ollama":
        print("FAIL: MODEL_PROVIDER must be ollama")
        return 1
    response = generate_response("Reply with exactly: PASS", config=config)
    if not response.ok:
        print(f"FAIL: {response.error}")
        return 1
    print(f"PASS: local Ollama replied: {response.text.strip()[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
