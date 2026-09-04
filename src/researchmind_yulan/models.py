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
class ExtractedClaim:
    text: str
    relation: str = "neutral"
    confidence: float = 0.5


@dataclass
class EvidenceAnalysis:
    evidence_id: str
    research_question: str = ""
    method: str = "unspecified"
    sample: str = "unspecified"
    data: str = "unspecified"
    finding: str = ""
    limitations: list[str] = field(default_factory=list)
    boundary_conditions: list[str] = field(default_factory=list)
    claims: list[ExtractedClaim] = field(default_factory=list)
    extraction_mode: str = "heuristic"


@dataclass
class ClaimNode:
    claim_id: str
    text: str


@dataclass
class ClaimEvidenceLink:
    claim_id: str
    evidence_id: str
    relation: str
    confidence: float


@dataclass
class ClaimEvidenceGraph:
    claims: list[ClaimNode] = field(default_factory=list)
    links: list[ClaimEvidenceLink] = field(default_factory=list)


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
    evidence_analysis: list[EvidenceAnalysis]
    claim_graph: ClaimEvidenceGraph
    literature_matrix: list[LiteratureRow]
    gaps: list[GapCandidate]
    counter_evidence: list[EvidenceItem]
    method_risks: list[MethodRisk]
    decision_summary: str
    stage_status: dict[str, str]
    run_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
