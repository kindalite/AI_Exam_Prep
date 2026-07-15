"""Tests for web retrieval caching with mocked public pages."""

from __future__ import annotations

from dataclasses import replace

from src.web_retrieval import WebSource, cache_web_source, load_cached_web_sources


def test_web_source_cache_round_trip(tmp_path, temp_config) -> None:
    config = replace(temp_config, web_cache_dir=tmp_path / "web_cache")
    source = WebSource("Title", "https://example.test", "Text", "Snippet", "now", "html")
    path = cache_web_source(source, config)
    assert path.exists()
    loaded = load_cached_web_sources(config)
    assert loaded[0].url == source.url
