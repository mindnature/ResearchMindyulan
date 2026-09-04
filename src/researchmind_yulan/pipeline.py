from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import EvidenceItem, PipelineResult
from .providers import LLMProvider, resolve_provider
from .stages import (
    audit_methods,
    build_literature_matrix,
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
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stage_status: dict[str, str] = {}

        mapped = map_question(question, discipline)
        stage_status["question_mapper"] = "ok"

        queries = plan_search(mapped)
        stage_status["search_planner"] = "ok"

        evidence = rank_evidence(mapped, corpus)[:top_k]
        if not evidence:
            raise ValueError("No evidence items available after retrieval")
        stage_status["evidence_scout"] = "ok"
        stage_status["evidence_registry"] = "ok"

        matrix = build_literature_matrix(evidence)
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
        gaps,
        counter_evidence: list[EvidenceItem],
        method_risks,
    ) -> str:
        evidence_lines = "\n".join(
            f"- {e.evidence_id}: {e.title} | stance={e.stance} | {e.excerpt}"
            for e in evidence
        )
        gap_lines = "\n".join(f"- {g.gap_type}: {g.statement}" for g in gaps)
        risk_lines = "\n".join(f"- {r.severity}: {r.risk}" for r in method_risks)
        counter_ids = ", ".join(e.evidence_id for e in counter_evidence) or "none"

        system = (
            "You are the Decision Synthesizer inside ResearchMind Yulan. "
            "Do not invent citations or claims. Distinguish established evidence, conflicts, "
            "research gaps, method risks, and next-step decisions. Be conservative about novelty."
        )
        user = f"""Research question: {question}
Discipline: {discipline}

Evidence:
{evidence_lines}

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
"""
        return self.provider.complete(system, user)

    def _persist(self, result: PipelineResult) -> None:
        run_dir = self.runs_dir / result.run_id
        run_dir.mkdir(parents=True, exist_ok=False)

        audit_path = run_dir / "audit_trail.json"
        audit_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        report_path = run_dir / "final_report.md"
        report_path.write_text(self._render_report(result), encoding="utf-8")

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
            f"verified={e.verified} | stance={e.stance}"
            for e in result.evidence
        )

        return f"""# ResearchMind Yulan Decision Report

Run ID: `{result.run_id}`

## Research question

{result.question.raw}

## Evidence registry snapshot

{evidence}

## Candidate research gaps

{gaps}

## Counter-evidence

{counter}

## Method audit

{risks}

## Decision memo

{result.decision_summary}

## Auditability

The machine-readable run record is stored in `audit_trail.json`. Candidate gaps and recommendations should not be treated as established novelty until targeted retrieval and source verification are complete.
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
