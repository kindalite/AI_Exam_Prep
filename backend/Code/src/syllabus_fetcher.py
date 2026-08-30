"""Fetch and prepare official KSA/Lucerne syllabus sources."""

from __future__ import annotations

from pathlib import Path

from .document_loaders import LoadedDocument
from .retrieval import RetrievalResult
from .subject_registry import Subject
from .utils import ensure_directory, utc_timestamp
from .web_retrieval import WebSource, cache_web_source, fetch_url, load_cached_web_sources

SYLLABUS_SEED_URLS = [
    "https://ksalpenquai.lu.ch/profil/langzeitgymnasium",
    "https://ksalpenquai.lu.ch/dokumente/reglemente_co/mar_faecher",
    "https://ksalpenquai.lu.ch/profil/schwerpunktfaecher",
    "https://ksalpenquai.lu.ch/dokumente/Lehrplaene_Untergymnasium",
    "https://ksalpenquai.lu.ch/-/media/KSAlpenquai/Dokumente/dokumente/lehrplaene/MAR/BEI_BKD_DGym_Kantonsschule_Alpenquai_Lehrplne_MAR_2021.pdf?rev=c0bb982a13404ab9854dce61f4637f69",
]


def subject_to_syllabus_keywords(subject: Subject) -> list[str]:
    """Return public-safe keywords for a subject syllabus lookup."""
    base = subject.display_name.lower().replace("/", " ").replace("spf", "")
    translations = {
        "chemistry": ["chemie"],
        "biology": ["biologie"],
        "history": ["geschichte"],
        "french": ["französisch", "franzoesisch"],
        "german": ["deutsch"],
        "english": ["englisch"],
        "maths physics": ["mathematik", "physik"],
        "political education": ["politische bildung"],
    }
    words = [part for part in base.split() if part]
    for key, values in translations.items():
        if key in base:
            words.extend(values)
    return sorted(set(words + [subject.key.replace("_", " "), subject.display_name.lower()]))


def fetch_official_syllabus_sources(config) -> list[WebSource]:
    """Fetch seed syllabus URLs and cache successful responses locally."""
    if not getattr(config, "allow_internet", True):
        return load_cached_web_sources(config)
    sources: list[WebSource] = []
    for url in SYLLABUS_SEED_URLS:
        try:
            source = fetch_url(url, config)
            cache_web_source(source, config)
            sources.append(source)
        except Exception:
            continue
    return sources or load_cached_web_sources(config)


def extract_subject_syllabus_sections(subject: Subject, sources: list[WebSource]) -> list[LoadedDocument]:
    """Convert relevant syllabus source text into LoadedDocument objects."""
    keywords = subject_to_syllabus_keywords(subject)
    documents: list[LoadedDocument] = []
    for source in sources:
        text = source.text or source.snippet
        lowered = text.lower()
        if not any(keyword in lowered for keyword in keywords):
            continue
        metadata = {
            "subject": subject.key,
            "source_path": source.url,
            "source_name": source.title,
            "source_type": source.source_type,
            "source_layer": "official_syllabus",
            "url": source.url,
            "loaded_at": utc_timestamp(),
        }
        documents.append(LoadedDocument(text=text, metadata=metadata))
    return documents


def ensure_subject_syllabus_cached(subject: Subject, config) -> list[LoadedDocument]:
    """Fetch/cache official syllabus content and return documents for one subject."""
    cache_dir = Path(getattr(config, "syllabus_cache_dir", Path("data/web_cache/syllabus"))) / subject.key
    ensure_directory(cache_dir)
    sources = fetch_official_syllabus_sources(config)
    documents = extract_subject_syllabus_sections(subject, sources)
    for index, document in enumerate(documents, start=1):
        (cache_dir / f"syllabus_{index}.txt").write_text(document.text, encoding="utf-8")
    return documents


def should_fetch_syllabus_for_subject(subject: Subject, retrieval_result: RetrievalResult) -> bool:
    """Decide whether official syllabus fallback should be used."""
    if not retrieval_result.sources:
        return True
    if "No indexed notes" in retrieval_result.message:
        return True
    starter_markers = ["Add exam learning goals here", "Add teacher criteria"]
    return all(any(marker in source.text for marker in starter_markers) for source in retrieval_result.sources)
