"""Tests that UI modules import without starting Streamlit."""

from __future__ import annotations


def test_ui_modules_import() -> None:
    import src.ui_auth  # noqa: F401
    import src.ui_components  # noqa: F401
    import src.ui_docs  # noqa: F401
    import src.ui_navigation  # noqa: F401
    import src.ui_practice_modes  # noqa: F401
    import src.ui_subject_dashboard  # noqa: F401
