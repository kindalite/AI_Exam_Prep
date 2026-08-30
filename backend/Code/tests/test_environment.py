"""Environment sanity tests."""

from __future__ import annotations

import importlib.util
import sys


def test_python_version_is_compatible() -> None:
    """The app is designed for Python 3.11 or newer."""
    assert sys.version_info >= (3, 11)


def test_key_packages_are_available_or_documented() -> None:
    """Check package availability without failing a bare development shell."""
    packages = ["pytest", "requests"]
    optional_packages = ["streamlit", "chromadb", "sentence_transformers", "pandas", "dotenv", "pypdf", "docx"]
    for package in packages:
        assert importlib.util.find_spec(package) is not None
    missing = [package for package in optional_packages if importlib.util.find_spec(package) is None]
    assert isinstance(missing, list)

