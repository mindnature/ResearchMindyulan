from __future__ import annotations

from .models import EvidenceItem


def provenance_grade(item: EvidenceItem) -> str:
    """Grade source-record traceability, not scientific truth or paper quality."""
    meta = item.metadata
    if (
        meta.get("crossref_record_verified") is True
        and meta.get("crossref_title_match") is True
        and meta.get("doi")
    ):
        return "A_crossref_confirmed"
    if meta.get("source_record_verified") is True and meta.get("doi"):
        return "B_provider_confirmed_with_doi"
    if meta.get("source_record_verified") is True:
        return "C_provider_confirmed"
    return "D_unverified_or_fixture"


def grade_evidence(items: list[EvidenceItem]) -> list[EvidenceItem]:
    for item in items:
        item.metadata["provenance_grade"] = provenance_grade(item)
        item.metadata["grade_semantics"] = "source_record_traceability_not_scientific_quality"
    return items
