"""Verify or pull the required local Ollama Gemma model."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.ollama_model_manager import ensure_required_model, is_ollama_cli_available, is_ollama_server_reachable, is_model_available


def _line(status: str, message: str) -> None:
    """Print one readable status line."""
    print(f"{status}: {message}")


def main() -> int:
    """Check Ollama and ensure gemma3:4b is available."""
    config = load_config(PROJECT_ROOT)
    model = config.ollama_required_model
    if is_ollama_cli_available():
        _line("PASS", "ollama CLI is installed")
    else:
        _line("FAIL", "ollama CLI is missing. Install Ollama, then run: ollama pull gemma3:4b")
        return 1
    if is_ollama_server_reachable(config.ollama_host):
        _line("PASS", f"Ollama server is reachable at {config.ollama_host}")
    else:
        _line("FAIL", f"Ollama server is not reachable at {config.ollama_host}. Start Ollama and retry.")
        return 1
    if is_model_available(model, config.ollama_host):
        _line("PASS", f"{model} is already installed")
        return 0
    ok, message = ensure_required_model(config)
    _line("PASS" if ok else "FAIL", message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
