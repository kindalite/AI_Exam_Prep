"""System smoke test for the local Gemma 3 4B Ollama setup."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.llm_client import generate_response
from src.ollama_model_manager import ensure_required_model, is_ollama_cli_available, is_ollama_server_reachable, is_model_available


def main() -> int:
    """Verify configuration, model availability, and a tiny local model call."""
    config = load_config(PROJECT_ROOT)
    if config.ollama_model != "gemma3:4b":
        print(f"FAIL: OLLAMA_MODEL is {config.ollama_model}, expected gemma3:4b")
        return 1
    print("PASS: OLLAMA_MODEL=gemma3:4b")
    if not is_ollama_cli_available():
        print("FAIL: Ollama CLI is missing. Install Ollama and run: ollama pull gemma3:4b")
        return 1
    print("PASS: Ollama CLI found")
    if not is_ollama_server_reachable(config.ollama_host):
        print(f"FAIL: Ollama server is not reachable at {config.ollama_host}")
        return 1
    print("PASS: Ollama server reachable")
    if not is_model_available(config.ollama_required_model, config.ollama_host):
        ok, message = ensure_required_model(config)
        print(("PASS" if ok else "FAIL") + f": {message}")
        if not ok:
            return 1
    else:
        print("PASS: gemma3:4b installed")
    response = generate_response("Reply with exactly: PASS", config=config)
    if response.ok:
        print("PASS: tiny local model call succeeded")
        return 0
    print(f"FAIL: tiny local model call failed: {response.error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
