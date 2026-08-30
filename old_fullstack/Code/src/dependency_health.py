"""Runtime dependency compatibility checks with actionable messages."""

from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True)
class DependencyCheck:
    """A dependency check result suitable for tests and setup output."""

    ok: bool
    message: str
    torch_version: str = ""
    torchvision_version: str = ""


def _major_minor(version: str) -> tuple[int, int] | None:
    """Parse the leading major.minor version from a package version string."""
    base = version.split("+", 1)[0]
    parts = base.split(".")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _expected_torchvision_minor(torch_version: str) -> int | None:
    """Return the torchvision minor version matching the installed torch minor."""
    parsed = _major_minor(torch_version)
    if parsed is None:
        return None
    major, minor = parsed
    if major == 2:
        return minor + 15
    if major == 1 and minor == 13:
        return 14
    return None


def check_torchvision_compatibility() -> DependencyCheck:
    """Check that torch and torchvision are installed as a compatible pair."""
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        return DependencyCheck(False, f"torch is not importable: {exc}")
    torch_version = str(getattr(torch, "__version__", ""))
    try:
        torchvision = importlib.import_module("torchvision")
    except Exception as exc:
        expected_minor = _expected_torchvision_minor(torch_version)
        hint = f" Install torchvision==0.{expected_minor}.0." if expected_minor is not None else " Install a torchvision build matching torch."
        return DependencyCheck(False, f"torch imports as {torch_version}, but torchvision is missing or broken.{hint} Details: {exc}", torch_version)
    torchvision_version = str(getattr(torchvision, "__version__", ""))
    expected_minor = _expected_torchvision_minor(torch_version)
    parsed_tv = _major_minor(torchvision_version)
    if expected_minor is not None and parsed_tv != (0, expected_minor):
        return DependencyCheck(
            False,
            f"torch {torch_version} expects torchvision 0.{expected_minor}.x, found {torchvision_version}. Reinstall the matched torchvision build.",
            torch_version,
            torchvision_version,
        )
    return DependencyCheck(True, f"torch {torch_version} and torchvision {torchvision_version} look compatible.", torch_version, torchvision_version)
