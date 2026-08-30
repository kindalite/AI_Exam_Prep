"""Format retrieved sources into the required evidence groups."""

from __future__ import annotations

from collections import defaultdict
from datetime import date


LAYER_TITLES = {
    "local_material": "From your materials",
    "learning_goals": "From your materials",
    "official_syllabus": "From the official Lucerne/KSA syllabus",
    "public_web": "From approved online sources",
    "general": "Model inference/general background",
}


def source_label(metadata: dict, fetch_date: str | None = None) -> str:
    """Create a compact source label without exposing private content."""
    name = metadata.get("source_name") or metadata.get("title") or "source"
    page = metadata.get("page_number")
    modality = metadata.get("modality")
    url = metadata.get("url")
    details = [str(name)]
    if page:
        details.append(f"page {page}")
    if modality:
        details.append(str(modality))
    if url:
        details.append(str(url))
    details.append(f"fetched {fetch_date or date.today().isoformat()}")
    return " | ".join(details)


def group_sources(sources: list) -> dict[str, list[str]]:
    """Group retrieved source metadata under required evidence headings."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for source in sources:
        metadata = getattr(source, "metadata", source)
        layer = str(metadata.get("source_layer", "local_material"))
        grouped[LAYER_TITLES.get(layer, LAYER_TITLES["general"])].append(source_label(metadata))
    for title in LAYER_TITLES.values():
        grouped.setdefault(title, [])
    return dict(grouped)
