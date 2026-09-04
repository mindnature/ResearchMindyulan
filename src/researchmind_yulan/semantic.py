from __future__ import annotations

import json
import re
from typing import Any, Iterable

from .models import (
    ClaimEvidenceGraph,
    ClaimEvidenceLink,
    ClaimNode,
    EvidenceAnalysis,
    EvidenceItem,
    ExtractedClaim,
    ResearchQuestion,
)
from .providers import DeterministicProvider, LLMProvider


RELATIONS = {"supporting", "contradicting", "boundary", "neutral"}


def _clip(text: str, limit: int = 7000) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit] + "…"


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?。！？])\s+", (text or "").strip())
    return (parts[0] if parts else text).strip()


def _json_object(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(text[start : end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _relation(value: Any) -> str:
    normalized = str(value or "neutral").strip().lower()
    aliases = {
        "support": "supporting",
        "positive": "supporting",
        "confirm": "supporting",
        "contradict": "contradicting",
        "negative": "contradicting",
        "counter": "contradicting",
        "mixed": "boundary",
        "qualify": "boundary",
        "qualified": "boundary",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in RELATIONS else "neutral"


def _confidence(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, score))


def _heuristic_analysis(item: EvidenceItem) -> EvidenceAnalysis:
    text = item.excerpt.strip()
    lowered = text.lower()
    method = "unspecified"
    for keyword in (
        "randomized",
        "experiment",
        "survey",
        "benchmark",
        "dataset",
        "case study",
        "regression",
        "difference-in-differences",
        "simulation",
        "qualitative",
    ):
        if keyword in lowered:
            method = keyword
            break

    limitations = []
    if any(marker in lowered for marker in ("limitation", "limited", "however", "unclear", "few", "lack")):
        limitations.append(text)

    relation = _relation(item.stance)
    if relation == "neutral":
        if any(marker in lowered for marker in ("fail", "harm", "bias", "over-refusal", "contradict")):
            relation = "contradicting"
        elif any(marker in lowered for marker in ("however", "only", "limited", "depends", "vary")):
            relation = "boundary"

    claim_text = _first_sentence(text) or item.title
    return EvidenceAnalysis(
        evidence_id=item.evidence_id,
        research_question="",
        method=method,
        finding=text,
        limitations=limitations,
        claims=[ExtractedClaim(text=claim_text, relation=relation, confidence=0.45)],
        extraction_mode="heuristic",
    )


def extract_evidence(
    provider: LLMProvider,
    question: ResearchQuestion,
    item: EvidenceItem,
) -> EvidenceAnalysis:
    fallback = _heuristic_analysis(item)
    if isinstance(provider, DeterministicProvider):
        return fallback

    system = """You are the Evidence Extractor inside ResearchMind Yulan.
Extract only information supported by the supplied evidence record. Never invent missing details.
Return one JSON object only, with no markdown and no prose outside JSON.
Relation labels describe how a claim bears on the user's research question:
- supporting: directly supports a proposition relevant to the question
- contradicting: provides evidence against a relevant proposition or common assumption
- boundary: qualifies a proposition by population, context, method, time, or condition
- neutral: relevant but not directional
Use 'unspecified' or empty arrays when the record does not contain the information."""

    user = f"""Research question: {question.raw}
Discipline: {question.discipline}

Evidence ID: {item.evidence_id}
Title: {item.title}
Source type: {item.source_type}
URL: {item.url}
Text:
{_clip(item.excerpt)}

Return exactly this schema:
{{
  "research_question": "question studied by this source or unspecified",
  "method": "method or unspecified",
  "sample": "sample/population or unspecified",
  "data": "data/dataset or unspecified",
  "finding": "main finding supported by the supplied text",
  "limitations": ["explicit limitation"],
  "boundary_conditions": ["scope or condition"],
  "claims": [
    {{"text": "atomic claim", "relation": "supporting|contradicting|boundary|neutral", "confidence": 0.0}}
  ]
}}
Keep at most 3 claims. Confidence is confidence that the supplied text supports the extraction, not confidence that the claim is scientifically true."""

    try:
        raw = provider.complete(system, user)
    except Exception:
        return fallback
    payload = _json_object(raw)
    if payload is None:
        return fallback

    claims: list[ExtractedClaim] = []
    raw_claims = payload.get("claims")
    if isinstance(raw_claims, list):
        for row in raw_claims[:3]:
            if not isinstance(row, dict):
                continue
            text = str(row.get("text") or "").strip()
            if not text:
                continue
            claims.append(
                ExtractedClaim(
                    text=text,
                    relation=_relation(row.get("relation")),
                    confidence=_confidence(row.get("confidence")),
                )
            )
    if not claims:
        claims = fallback.claims

    limitations = payload.get("limitations")
    boundary_conditions = payload.get("boundary_conditions")
    return EvidenceAnalysis(
        evidence_id=item.evidence_id,
        research_question=str(payload.get("research_question") or "").strip(),
        method=str(payload.get("method") or "unspecified").strip() or "unspecified",
        sample=str(payload.get("sample") or "unspecified").strip() or "unspecified",
        data=str(payload.get("data") or "unspecified").strip() or "unspecified",
        finding=str(payload.get("finding") or fallback.finding).strip(),
        limitations=[str(x).strip() for x in limitations if str(x).strip()]
        if isinstance(limitations, list)
        else fallback.limitations,
        boundary_conditions=[str(x).strip() for x in boundary_conditions if str(x).strip()]
        if isinstance(boundary_conditions, list)
        else [],
        claims=claims,
        extraction_mode="llm",
    )


def extract_evidence_batch(
    provider: LLMProvider,
    question: ResearchQuestion,
    evidence: Iterable[EvidenceItem],
) -> list[EvidenceAnalysis]:
    return [extract_evidence(provider, question, item) for item in evidence]


def build_claim_evidence_graph(analyses: Iterable[EvidenceAnalysis]) -> ClaimEvidenceGraph:
    nodes: list[ClaimNode] = []
    links: list[ClaimEvidenceLink] = []
    claim_index = 1
    for analysis in analyses:
        for claim in analysis.claims:
            claim_id = f"C{claim_index:03d}"
            claim_index += 1
            nodes.append(ClaimNode(claim_id=claim_id, text=claim.text))
            links.append(
                ClaimEvidenceLink(
                    claim_id=claim_id,
                    evidence_id=analysis.evidence_id,
                    relation=claim.relation,
                    confidence=claim.confidence,
                )
            )
    return ClaimEvidenceGraph(claims=nodes, links=links)


def apply_analysis_stance(
    evidence: Iterable[EvidenceItem],
    analyses: Iterable[EvidenceAnalysis],
) -> list[EvidenceItem]:
    by_id = {analysis.evidence_id: analysis for analysis in analyses}
    priority = ("contradicting", "boundary", "supporting", "neutral")
    stance_map = {
        "contradicting": "counter",
        "boundary": "mixed",
        "supporting": "positive",
        "neutral": "neutral",
    }
    result = list(evidence)
    for item in result:
        analysis = by_id.get(item.evidence_id)
        if analysis is None or not analysis.claims:
            continue
        relations = {claim.relation for claim in analysis.claims}
        chosen = next((value for value in priority if value in relations), "neutral")
        item.stance = stance_map[chosen]
        item.metadata["semantic_extraction_mode"] = analysis.extraction_mode
    return result
