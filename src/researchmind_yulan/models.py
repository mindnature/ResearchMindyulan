from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ResearchQuestion:
    raw: str
    discipline: str = "general"
    subquestions: list[str] = field(default_factory=list)


@dataclass
class SearchQuery:
    query: str
    purpose: str


@dataclass
class EvidenceItem:
    evidence_id: str
    title: str
    source_type: str
    url: str
    excerpt: str
    relevance: float = 0.0
    stance: str = "neutral"
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LiteratureRow:
    evidence_id: str
    claim: str
    method: str
    finding: str
    limitation: str
    stance: str


@dataclass
class GapCandidate:
    gap_type: str
    statement: str
    supporting_evidence_ids: list[str]
    confidence: float


@dataclass
class MethodRisk:
    risk: str
    evidence_ids: list[str]
    severity: str


@dataclass
class PipelineResult:
    question: ResearchQuestion
    queries: list[SearchQuery]
    evidence: list[EvidenceItem]
    literature_matrix: list[LiteratureRow]
    gaps: list[GapCandidate]
    counter_evidence: list[EvidenceItem]
    method_risks: list[MethodRisk]
    decision_summary: str
    stage_status: dict[str, str]
    run_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
