"""Tests for local password hashing and authentication."""

from __future__ import annotations

from src.auth import create_password_hash, verify_password
from src.user_data_paths import sanitize_username


def test_password_hash_is_salted_and_verifiable() -> None:
    first = create_password_hash("secret")
    second = create_password_hash("secret")
    assert first["hash"] != "secret"
    assert first["hash"] != second["hash"]
    assert verify_password("secret", first)
    assert not verify_password("wrong", first)


def test_username_sanitized_for_paths() -> None:
    assert sanitize_username("Alim Test!!") == "alim_test"
