"""Falsification-oriented second-round scholarly retrieval.

Finding candidate prior art is NOT proof that a gap is closed, and failing to
find a paper is NOT proof of novelty. All hits must pass the relevance gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .models import EvidenceItem, GapCandidate
from .quality import filter_retrieval, focus_terms, tokens


class SearchClient(Protocol):
    def search(self, query: str, per_page: int = 3, semantic: bool = False) -> list[EvidenceItem]: ...


@dataclass
class CounterSearchTrace:
    query: str
    gap_type: str
    retrieved_evidence_ids: list[str] = field(default_factory=list)
    rejected_evidence_ids: list[str] = field(default_factory=list)
    error: str = ""
    conclusion: str = "unverified_requires_manual_review"


def investigate_gaps(
    question: str,
    gaps: list[GapCandidate],
    client: SearchClient,
    *,
    max_gaps: int = 2,
    per_query: int = 3,
    existing_ids: set[str] | None = None,
) -> tuple[list[EvidenceItem], list[CounterSearchTrace]]:
    known = set(existing_ids or ())
    additions: list[EvidenceItem] = []
    traces: list[CounterSearchTrace] = []
    base = " ".join(focus_terms(question)[:5]) or " ".join(tokens(question)[:5])
    for gap in gaps[:max_gaps]:
        # Search prior art and adverse results; never claim a contradiction solely
        # from results returned by the search engine.
        suffix = "prior work review counterexample" if gap.gap_type != "method_gap" else "alternative method comparison"
        query = " ".join([base, suffix]).strip()
        trace = CounterSearchTrace(query=query, gap_type=gap.gap_type)
        try:
            hits = client.search(query, per_page=per_query)
            accepted, rejected = filter_retrieval(question, hits)
            trace.rejected_evidence_ids = [e.evidence_id for e in rejected]
            for item in accepted:
                if item.evidence_id not in known:
                    item.metadata["retrieval_purpose"] = "skeptic_second_pass"
                    item.metadata["retrieval_query"] = query
                    known.add(item.evidence_id)
                    additions.append(item)
                    trace.retrieved_evidence_ids.append(item.evidence_id)
        except Exception as exc:
            trace.error = f"{type(exc).__name__}: {str(exc)[:250]}"
            trace.conclusion = "search_failed_not_evaluated"
        traces.append(trace)
    return additions, traces
