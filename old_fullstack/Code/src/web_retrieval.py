"""Public web retrieval and local caching for syllabus-safe sources."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

from .utils import ensure_directory, utc_timestamp


@dataclass(frozen=True)
class WebSource:
    """A fetched public web source."""

    title: str
    url: str
    text: str
    snippet: str
    fetched_at: str
    source_type: str


def _extract_html_text(html: str) -> str:
    """Extract readable text from HTML with optional libraries."""
    try:
        import trafilatura

        extracted = trafilatura.extract(html)
        if extracted:
            return extracted
    except Exception:
        pass
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else ""
        body = soup.get_text("\n")
        return "\n".join(part.strip() for part in [title, body] if part.strip())
    except Exception:
        return html


def fetch_url(url: str, config) -> WebSource:
    """Fetch one public URL and extract text for local caching."""
    response = requests.get(url, timeout=getattr(config, "web_request_timeout_seconds", 20), headers={"User-Agent": "AlimStudyAssistant/1.0"})
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    source_type = "pdf" if "pdf" in content_type or url.lower().endswith(".pdf") else "html"
    if source_type == "html":
        text = _extract_html_text(response.text)
    else:
        text = response.text if isinstance(response.text, str) else ""
    title = urlparse(url).netloc or url
    return WebSource(title=title, url=url, text=text, snippet=text[:300], fetched_at=utc_timestamp(), source_type=source_type)


def search_web(query: str, config, max_results: int) -> list[WebSource]:
    """Search public web sources without sending private notes."""
    if not getattr(config, "allow_internet", True):
        return []
    if getattr(config, "searxng_url", ""):
        response = requests.get(getattr(config, "searxng_url"), params={"q": query, "format": "json"}, timeout=20)
        response.raise_for_status()
        return [fetch_url(item["url"], config) for item in response.json().get("results", [])[:max_results] if item.get("url")]
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        sources: list[WebSource] = []
        for item in results:
            href = item.get("href") or item.get("url")
            if href:
                try:
                    sources.append(fetch_url(href, config))
                except Exception:
                    continue
        return sources
    except Exception:
        return []


def cache_web_source(source: WebSource, config) -> Path:
    """Write a fetched public source to the local web cache."""
    cache_dir = Path(getattr(config, "web_cache_dir", Path("data/web_cache")))
    ensure_directory(cache_dir)
    digest = hashlib.sha256(source.url.encode("utf-8")).hexdigest()[:16]
    path = cache_dir / f"{digest}.json"
    path.write_text(json.dumps(asdict(source), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_cached_web_sources(config) -> list[WebSource]:
    """Load previously cached public web sources."""
    cache_dir = Path(getattr(config, "web_cache_dir", Path("data/web_cache")))
    if not cache_dir.exists():
        return []
    sources: list[WebSource] = []
    for path in sorted(cache_dir.glob("*.json")):
        try:
            sources.append(WebSource(**json.loads(path.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return sources
