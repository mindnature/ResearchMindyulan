from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from .models import (
    EvidenceAnalysis,
    EvidenceItem,
    GapCandidate,
    LiteratureRow,
    MethodRisk,
    ResearchQuestion,
    SearchQuery,
)


STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with",
    "how", "should", "be", "is", "are", "what", "which", "that", "this",
}


def _tokens(text: str) -> list[str]:
    return [
        t.lower()
        for t in re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]+", text)
        if t.lower() not in STOPWORDS and len(t) > 1
    ]


def map_question(raw: str, discipline: str) -> ResearchQuestion:
    raw = raw.strip()
    if not raw:
        raise ValueError("Research question cannot be empty")
    return ResearchQuestion(
        raw=raw,
        discipline=discipline,
        subquestions=[
            f"What is already established about: {raw}",
            f"Where do findings or assumptions conflict for: {raw}",
            f"What evidence or populations are missing for: {raw}",
            f"Which methodological risks could invalidate conclusions about: {raw}",
        ],
    )


def plan_search(question: ResearchQuestion) -> list[SearchQuery]:
    return [
        SearchQuery(question.raw, "core literature"),
        SearchQuery(f"{question.raw} review benchmark", "state of the field"),
        SearchQuery(f"{question.raw} limitation failure negative result", "counter-evidence"),
        SearchQuery(f"{question.raw} method evaluation dataset", "methodological evidence"),
    ]


def rank_evidence(question: ResearchQuestion, corpus: Iterable[EvidenceItem]) -> list[EvidenceItem]:
    q_terms = Counter(_tokens(question.raw))
    ranked: list[EvidenceItem] = []
    for item in corpus:
        haystack = f"{item.title} {item.excerpt}"
        d_terms = Counter(_tokens(haystack))
        overlap = sum(min(q_terms[t], d_terms[t]) for t in q_terms)
        denominator = max(1, sum(q_terms.values()))
        item.relevance = round(overlap / denominator, 3)
        ranked.append(item)
    ranked.sort(key=lambda x: (x.relevance, x.verified), reverse=True)
    return ranked


def build_literature_matrix(evidence: Iterable[EvidenceItem]) -> list[LiteratureRow]:
    rows: list[LiteratureRow] = []
    for item in evidence:
        text = item.excerpt.strip()
        method = "unspecified"
        lowered = text.lower()
        for keyword in (
            "randomized", "experiment", "survey", "benchmark", "dataset", "case study",
            "regression", "difference-in-differences", "simulation", "qualitative",
        ):
            if keyword in lowered:
                method = keyword
                break
        limitation = ""
        for marker in ("limitation", "limited", "however", "unclear", "few", "lack"):
            if marker in lowered:
                limitation = text
                break
        rows.append(
            LiteratureRow(
                evidence_id=item.evidence_id,
                claim=item.title,
                method=method,
                finding=text,
                limitation=limitation,
                stance=item.stance,
            )
        )
    return rows


def build_literature_matrix_from_analysis(
    analyses: Iterable[EvidenceAnalysis],
    evidence: Iterable[EvidenceItem],
) -> list[LiteratureRow]:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    rows: list[LiteratureRow] = []
    for analysis in analyses:
        item = evidence_by_id.get(analysis.evidence_id)
        stance = item.stance if item is not None else "neutral"
        claim = analysis.claims[0].text if analysis.claims else (item.title if item else "")
        rows.append(
            LiteratureRow(
                evidence_id=analysis.evidence_id,
                claim=claim,
                method=analysis.method or "unspecified",
                finding=analysis.finding,
                limitation="; ".join(analysis.limitations),
                stance=stance,
            )
        )
    return rows


def detect_gaps(matrix: Iterable[LiteratureRow]) -> list[GapCandidate]:
    rows = list(matrix)
    gaps: list[GapCandidate] = []
    limitation_ids = [r.evidence_id for r in rows if r.limitation]
    methods = {r.method for r in rows if r.method != "unspecified"}
    stances = {r.stance for r in rows if r.stance != "neutral"}

    if limitation_ids:
        gaps.append(
            GapCandidate(
                gap_type="evidence_gap",
                statement="Multiple sources explicitly report limitations or missing evidence; these constraints should be converted into testable research questions.",
                supporting_evidence_ids=limitation_ids,
                confidence=min(0.95, 0.55 + 0.08 * len(limitation_ids)),
            )
        )
    if len(methods) <= 1 and rows:
        gaps.append(
            GapCandidate(
                gap_type="method_gap",
                statement="The retrieved evidence is methodologically narrow; conclusions may depend on a limited evaluation design.",
                supporting_evidence_ids=[r.evidence_id for r in rows],
                confidence=0.72,
            )
        )
    if len(stances) >= 2:
        gaps.append(
            GapCandidate(
                gap_type="theory_or_finding_conflict",
                statement="The evidence contains competing conclusions. A useful study should identify conditions under which each conclusion holds.",
                supporting_evidence_ids=[r.evidence_id for r in rows if r.stance != "neutral"],
                confidence=0.84,
            )
        )
    if not gaps and rows:
        gaps.append(
            GapCandidate(
                gap_type="verification_gap",
                statement="The current corpus does not expose a strong explicit gap; further targeted retrieval is required before claiming novelty.",
                supporting_evidence_ids=[r.evidence_id for r in rows[:3]],
                confidence=0.6,
            )
        )
    return gaps


def select_counter_evidence(evidence: Iterable[EvidenceItem]) -> list[EvidenceItem]:
    items = list(evidence)
    explicit = [i for i in items if i.stance in {"negative", "mixed", "counter"}]
    if explicit:
        return explicit
    markers = ("fail", "risk", "limitation", "not", "however", "harm", "bias")
    return [i for i in items if any(m in i.excerpt.lower() for m in markers)]


def audit_methods(matrix: Iterable[LiteratureRow]) -> list[MethodRisk]:
    rows = list(matrix)
    risks: list[MethodRisk] = []
    unspecified = [r.evidence_id for r in rows if r.method == "unspecified"]
    if unspecified:
        risks.append(
            MethodRisk(
                risk="Method details are missing for part of the evidence; causal or comparative claims may be over-interpreted.",
                evidence_ids=unspecified,
                severity="medium",
            )
        )
    if not any(r.method in {"experiment", "randomized"} for r in rows):
        risks.append(
            MethodRisk(
                risk="No experimental evidence was detected in the current evidence set; causal claims require caution.",
                evidence_ids=[r.evidence_id for r in rows],
                severity="medium",
            )
        )
    if len(rows) < 5:
        risks.append(
            MethodRisk(
                risk="Evidence coverage is too small for a stable research map; expand retrieval before finalizing a research direction.",
                evidence_ids=[r.evidence_id for r in rows],
                severity="high",
            )
        )
    return risks
