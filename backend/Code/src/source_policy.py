"""Trusted public-source policy and sanitized web-query helpers."""

from __future__ import annotations

import re
from urllib.parse import urlparse


TRUSTED_DOMAINS = (
    ".ch",
    ".edu",
    ".gov",
    "admin.ch",
    "lu.ch",
    "ksalpenquai.lu.ch",
    "ethz.ch",
    "unil.ch",
    "uzh.ch",
    "epfl.ch",
)
REJECTED_HINTS = ("answer farm", "chegg", "studocu", "coursehero", "pirated", "torrent")
PRIVATE_DETAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+|\b\d{3,}\b")


def sanitize_public_query(query: str, subject: str = "") -> str:
    """Remove obvious private identifiers before web search."""
    clean = PRIVATE_DETAIL_PATTERN.sub(" ", query)
    clean = " ".join(clean.split())[:180]
    return f"{subject} {clean}".strip()


def is_trusted_source(url: str, title: str = "") -> bool:
    """Return True when a public source appears suitable for school use."""
    haystack = f"{url} {title}".lower()
    if any(hint in haystack for hint in REJECTED_HINTS):
        return False
    domain = urlparse(url).netloc.lower()
    return any(domain == item.lstrip(".") or domain.endswith(item) for item in TRUSTED_DOMAINS)
