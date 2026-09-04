from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .evidence import grade_evidence
from .models import EvidenceItem, PipelineResult
from .providers import LLMProvider, resolve_provider
from .semantic import (
    apply_analysis_stance,
    build_claim_evidence_graph,
    extract_evidence_batch,
)
from .stages import (
    audit_methods,
    build_literature_matrix_from_analysis,
    detect_gaps,
    map_question,
    plan_search,
    rank_evidence,
    select_counter_evidence,
)


class ResearchPipeline:
    def __init__(self, provider: LLMProvider | None = None, runs_dir: str | Path | None = None):
        self.provider = provider or resolve_provider(prefer_llm=True)
        self.runs_dir = Path(runs_dir or os.getenv("RM_YULAN_RUNS_DIR", "runs"))

    def run(
        self,
        question: str,
        discipline: str,
        corpus: Iterable[EvidenceItem],
        top_k: int = 12,
    ) -> PipelineResult:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        stage_status: dict[str, str] = {}

        mapped = map_question(question, discipline)
        stage_status["question_mapper"] = "ok"

        queries = plan_search(mapped)
        stage_status["search_planner"] = "ok"

        evidence = rank_evidence(mapped, corpus)[:top_k]
        if not evidence:
            raise ValueError("No evidence items available after retrieval")
        stage_status["evidence_scout"] = "ok"

        evidence = grade_evidence(evidence)
        stage_status["evidence_registry"] = "ok"

        evidence_analysis = extract_evidence_batch(self.provider, mapped, evidence)
        evidence = apply_analysis_stance(evidence, evidence_analysis)
        stage_status["evidence_extractor"] = "ok"

        claim_graph = build_claim_evidence_graph(evidence_analysis)
        stage_status["claim_evidence_graph"] = "ok"

        matrix = build_literature_matrix_from_analysis(evidence_analysis, evidence)
        stage_status["literature_matrix"] = "ok"

        gaps = detect_gaps(matrix)
        stage_status["gap_detector"] = "ok"

        counter_evidence = select_counter_evidence(evidence)
        stage_status["skeptic_counter_search"] = "ok"

        method_risks = audit_methods(matrix)
        stage_status["method_auditor"] = "ok"

        decision_summary = self._synthesize(
            question=question,
            discipline=discipline,
            evidence=evidence,
            claim_graph=claim_graph,
            gaps=gaps,
            counter_evidence=counter_evidence,
            method_risks=method_risks,
        )
        stage_status["decision_synthesizer"] = "ok"
        stage_status["scholar_advisor"] = "not_enabled"

        result = PipelineResult(
            question=mapped,
            queries=queries,
            evidence=evidence,
            evidence_analysis=evidence_analysis,
            claim_graph=claim_graph,
            literature_matrix=matrix,
            gaps=gaps,
            counter_evidence=counter_evidence,
            method_risks=method_risks,
            decision_summary=decision_summary,
            stage_status=stage_status,
            run_id=run_id,
        )
        self._persist(result)
        return result

    def _synthesize(
        self,
        *,
        question: str,
        discipline: str,
        evidence: list[EvidenceItem],
        claim_graph,
        gaps,
        counter_evidence: list[EvidenceItem],
        method_risks,
    ) -> str:
        evidence_lines = "\n".join(
            f"- {e.evidence_id}: {e.title} | stance={e.stance} | "
            f"provenance={e.metadata.get('provenance_grade', 'unknown')} | {e.excerpt}"
            for e in evidence
        )
        link_by_claim = {link.claim_id: link for link in claim_graph.links}
        claim_lines = "\n".join(
            f"- {claim.claim_id}: {claim.text} | relation="
            f"{link_by_claim[claim.claim_id].relation if claim.claim_id in link_by_claim else 'neutral'} | "
            f"evidence={link_by_claim[claim.claim_id].evidence_id if claim.claim_id in link_by_claim else 'unknown'}"
            for claim in claim_graph.claims
        )
        gap_lines = "\n".join(f"- {g.gap_type}: {g.statement}" for g in gaps)
        risk_lines = "\n".join(f"- {r.severity}: {r.risk}" for r in method_risks)
        counter_ids = ", ".join(e.evidence_id for e in counter_evidence) or "none"

        system = (
            "You are the Decision Synthesizer inside ResearchMind Yulan. "
            "Do not invent citations or claims. Distinguish established evidence, conflicts, "
            "research gaps, method risks, and next-step decisions. Be conservative about novelty. "
            "Every factual statement should be attributable to an evidence ID when possible."
        )
        user = f"""Research question: {question}
Discipline: {discipline}

Evidence:
{evidence_lines}

Claim-Evidence Graph:
{claim_lines}

Candidate gaps:
{gap_lines}

Counter-evidence IDs: {counter_ids}

Method risks:
{risk_lines}

Produce a concise decision memo with these headings:
1. Current evidence state
2. Most defensible research gap
3. Strongest counterargument
4. Method risk that must be resolved
5. Recommended next experiment or retrieval step
Use evidence IDs in brackets for claims supported by the supplied records.
"""
        return self.provider.complete(system, user)

    def _persist(self, result: PipelineResult) -> None:
        run_dir = self.runs_dir / result.run_id
        stage_dir = run_dir / "stages"
        stage_dir.mkdir(parents=True, exist_ok=False)

        stage_payloads = {
            "01_question_mapper.json": asdict(result.question),
            "02_search_planner.json": [asdict(item) for item in result.queries],
            "03_evidence_registry.json": [asdict(item) for item in result.evidence],
            "04_evidence_analysis.json": [asdict(item) for item in result.evidence_analysis],
            "05_claim_evidence_graph.json": asdict(result.claim_graph),
            "06_literature_matrix.json": [asdict(item) for item in result.literature_matrix],
            "07_gap_detector.json": [asdict(item) for item in result.gaps],
            "08_counter_evidence.json": [asdict(item) for item in result.counter_evidence],
            "09_method_audit.json": [asdict(item) for item in result.method_risks],
            "10_stage_status.json": result.stage_status,
        }
        for filename, payload in stage_payloads.items():
            (stage_dir / filename).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        audit_path = run_dir / "audit_trail.json"
        audit_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        report_path = run_dir / "final_report.md"
        report_path.write_text(self._render_report(result), encoding="utf-8")

        manifest = {
            "run_id": result.run_id,
            "question": result.question.raw,
            "discipline": result.question.discipline,
            "stage_status": result.stage_status,
            "artifacts": [
                "final_report.md",
                "audit_trail.json",
                *[f"stages/{name}" for name in stage_payloads],
            ],
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _render_report(result: PipelineResult) -> str:
        gaps = "\n".join(
            f"- **{g.gap_type}** ({g.confidence:.2f}): {g.statement} "
            f"[evidence: {', '.join(g.supporting_evidence_ids)}]"
            for g in result.gaps
        ) or "- None"
        counter = "\n".join(
            f"- {e.evidence_id}: {e.title} — {e.excerpt}" for e in result.counter_evidence
        ) or "- None found in current corpus"
        risks = "\n".join(
            f"- **{r.severity}**: {r.risk} [evidence: {', '.join(r.evidence_ids)}]"
            for r in result.method_risks
        ) or "- None detected"
        evidence = "\n".join(
            f"- `{e.evidence_id}` {e.title} | relevance={e.relevance:.3f} | "
            f"record_verified={e.verified} | provenance={e.metadata.get('provenance_grade', 'unknown')} | "
            f"stance={e.stance}"
            for e in result.evidence
        )
        link_by_claim = {link.claim_id: link for link in result.claim_graph.links}
        claims = "\n".join(
            f"- `{claim.claim_id}` {claim.text} → "
            f"{link_by_claim[claim.claim_id].relation if claim.claim_id in link_by_claim else 'neutral'} "
            f"[`{link_by_claim[claim.claim_id].evidence_id if claim.claim_id in link_by_claim else 'unknown'}`]"
            for claim in result.claim_graph.claims
        ) or "- None"

        return f"""# ResearchMind Yulan Decision Report

Run ID: `{result.run_id}`

## Research question

{result.question.raw}

## Evidence registry snapshot

{evidence}

## Claim–Evidence Graph

{claims}

## Candidate research gaps

{gaps}

## Counter-evidence

{counter}

## Method audit

{risks}

## Decision memo

{result.decision_summary}

## Auditability

The machine-readable run record is stored in `audit_trail.json`. Provenance grades describe source-record traceability, not scientific truth or journal quality. Claim relation confidence describes extraction support from the supplied record, not scientific truth. Candidate gaps and recommendations should not be treated as established novelty until targeted retrieval and source verification are complete.
"""


def load_corpus(path: str | Path) -> list[EvidenceItem]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Corpus JSON must contain a list of evidence items")
    items: list[EvidenceItem] = []
    for index, row in enumerate(data, start=1):
        items.append(
            EvidenceItem(
                evidence_id=str(row.get("evidence_id") or f"E{index:03d}"),
                title=str(row.get("title") or "Untitled source"),
                source_type=str(row.get("source_type") or "unknown"),
                url=str(row.get("url") or ""),
                excerpt=str(row.get("excerpt") or ""),
                stance=str(row.get("stance") or "neutral"),
                verified=bool(row.get("verified", False)),
                metadata=dict(row.get("metadata") or {}),
            )
        )
    return items
