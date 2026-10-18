"""Deterministic fixture benchmark for retrieval quality.

This is a unit/regression benchmark, NOT a blinded scientific comparison
against another Deep Research product. Never report the scores as validation
of research decision quality or generalization.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from .models import EvidenceItem
from .quality import filter_retrieval
from .stages import map_question, rank_evidence

CASES = [
    {
        "question": "How should LLM refusal boundaries be evaluated?",
        "items": [
            ("r1", "Local semantic stability of LLM refusals", "A refusal boundary benchmark measures paraphrase inconsistency.", 1),
            ("r2", "Over-refusal and safe compliance tradeoffs", "Paired harmful and benign prompts help evaluate refusal calibration.", 1),
            ("r3", "Refusal boundary evaluation in safety models", "Evaluation compares accepted and declined responses.", 1),
            ("r4", "LLM legal hallucination taxonomy", "Law warrant and citation accuracy in legal answers.", 0),
            ("r5", "Islamic knowledge LLM benchmark", "Religion and jurisprudence question answering benchmark.", 0),
            ("r6", "Robotic motion planning", "Path optimization and sensor fusion.", 0),
        ],
    },
    {
        "question": "How can lychee agroforestry improve pollinator habitat?",
        "items": [
            ("a1", "Lychee agroforestry and pollinator richness", "Field samples measure pollinator habitat near lychee orchards.", 1),
            ("a2", "Pollinator responses to mixed agroforestry", "Habitat quality and biodiversity in lychee orchards.", 1),
            ("a3", "Lychee fruit supply chain optimization", "Logistics efficiencies in the fruit industry.", 0),
            ("a4", "Improving industrial battery performance", "An engineering study of batteries.", 0),
            ("a5", "Pollinator habitat restoration in orchards", "Mixed agroforestry supports flowering plants.", 1),
            ("a6", "Understanding consumer purchase intention", "Psychological factors affecting retail demand.", 0),
        ],
    },
]


def metrics(predicted: set[str], truth: set[str], population: set[str]) -> dict:
    tp = len(predicted & truth)
    fp = len(predicted - truth)
    fn = len(truth - predicted)
    tn = len(population - predicted - truth)
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
        "recall": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
        "false_positive_rate": round(fp / (fp + tn), 4) if (fp + tn) else 0.0,
    }


def run_fixture_benchmark(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in CASES:
        evidence = [
            EvidenceItem(evidence_id=key, title=title, excerpt=body,
                         source_type="synthetic_fixture", url="")
            for key, title, body, _ in case["items"]
        ]
        truth = {key for key, _, _, label in case["items"] if label}
        population = {item.evidence_id for item in evidence}
        baseline = {
            item.evidence_id for item in rank_evidence(
                map_question(case["question"], "general"),
                list(evidence)
            )[:len(truth)]
        }
        accepted, rejected = filter_retrieval(case["question"], evidence)
        proposed = {e.evidence_id for e in accepted}
        rows.append({
            "question": case["question"], "labels": {x[0]: x[3] for x in case["items"]},
            "baseline_top_k": metrics(baseline, truth, population),
            "topic_gate": metrics(proposed, truth, population),
            "rejected": [e.evidence_id for e in rejected],
        })

    def aggregate(key):
        parts = [row[key] for row in rows]
        totals = {c: sum(part[c] for part in parts) for c in ("tp", "fp", "fn", "tn")}
        pop = totals["tp"] + totals["fp"] + totals["fn"] + totals["tn"]
        return {**totals, "n": pop,
                "precision": round(totals["tp"] / max(1, totals["tp"] + totals["fp"]), 4),
                "recall": round(totals["tp"] / max(1, totals["tp"] + totals["fn"]), 4),
                "false_positive_rate": round(totals["fp"] / max(1, totals["fp"] + totals["tn"]), 4)}
    result = {
        "methodology": "synthetic_fixture_smoke_test_not_real_world_benchmark",
        "case_count": len(rows),
        "results": rows,
        "summary": {"baseline_top_k": aggregate("baseline_top_k"), "topic_gate": aggregate("topic_gate")},
        "limitations": ["Small hand-labeled synthetic corpus", "Not a blinded test", "Does not test LLM extraction or research novelty"],
    }
    (output / "fixture_retrieval.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = result["summary"]
    (output / "fixture_retrieval.md").write_text(
        "# Retrieval fixture smoke test (NOT a competition benchmark)\n\n"
        "| Pipeline | Precision | Recall | False-positive rate |\n"
        "|---|---:|---:|---:|\n"
        + "".join(
            f"| {name} | {m['precision']:.3f} | {m['recall']:.3f} | {m['false_positive_rate']:.3f} |\n"
            for name, m in summary.items()
        ) + "\nSynthetic, hand-labeled cases only. No statistical or comparative performance claims.\n",
        encoding="utf-8"
    )
    return result
