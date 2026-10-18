from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from researchmind_yulan.benchmark import run_fixture_benchmark
from researchmind_yulan.models import EvidenceItem, GapCandidate, ResearchQuestion
from researchmind_yulan.pipeline import ResearchPipeline
from researchmind_yulan.planning import plan_queries
from researchmind_yulan.providers import DeterministicProvider
from researchmind_yulan.quality import filter_retrieval, focus_terms
from researchmind_yulan.skeptic import investigate_gaps
from researchmind_yulan.stages import select_counter_evidence


def paper(code, title, text, stance="neutral"):
    return EvidenceItem(
        evidence_id=code, title=title, source_type="article",
        url=f"https://example.org/{code}", excerpt=text, stance=stance,
    )


class FakeClient:
    def search(self, query: str, per_page: int = 3, semantic: bool = False):
        return [
            paper("OA-N1", "Refusal boundary calibration in LLMs",
                  "Prior research tests refusal and boundary stability with counterexamples."),
            paper("OA-N2", "Islamic LLM knowledge benchmark",
                  "This compares religious knowledge question answering."),
        ]


class CompetitionQualityTest(unittest.TestCase):
    def test_topic_gate_excludes_llm_only_distractor(self):
        question = "How should LLM refusal boundaries be evaluated?"
        candidates = [
            paper("OA-GOOD", "Local LLM refusal boundary", "Benchmark of refusal and benign prompts."),
            paper("OA-BAD", "IslamicMMLU: LLM knowledge evaluation", "A benchmark for Islamic knowledge."),
            paper("OA-LEGAL", "Legal LLM hallucination reliability", "Statutes and citations."),
        ]
        accepted, rejected = filter_retrieval(question, candidates)
        self.assertEqual([e.evidence_id for e in accepted], ["OA-GOOD"])
        self.assertEqual({e.evidence_id for e in rejected}, {"OA-BAD", "OA-LEGAL"})

    def test_planner_produces_keyword_queries_not_questions(self):
        question = ResearchQuestion("How should LLM refusal boundaries be evaluated?", "ai")
        plan = plan_queries(question, DeterministicProvider())
        self.assertGreaterEqual(len(plan), 3)
        self.assertIn("refusal", plan[0].query.lower())
        self.assertNotIn("?", plan[0].query)

    def test_unknown_stance_is_not_counter_evidence(self):
        items = [
            paper("one", "Failure review", "However, failure exists.", "neutral"),
            paper("two", "Risk survey", "Limited applicability.", "mixed"),
            paper("three", "Direct competing result", "Specific disagreement.", "counter"),
        ]
        self.assertEqual([e.evidence_id for e in select_counter_evidence(items)], ["three"])

    def test_skeptic_produces_trace_and_filters_irrelevant(self):
        gaps = [GapCandidate("method_gap", "Further prior-art comparison needed", ["E001"], 0.5)]
        items, traces = investigate_gaps(
            "How should LLM refusal boundaries be evaluated?", gaps, FakeClient()
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].evidence_id, "OA-N1")
        self.assertEqual(traces[0].rejected_evidence_ids, ["OA-N2"])
        self.assertEqual(traces[0].conclusion, "unverified_requires_manual_review")

    def test_pipeline_second_pass_keeps_auditable_artifacts(self):
        corpus = [
            paper("E001", "Refusal boundary benchmark",
                  "Experimental refusal boundaries have a limitation."),
            paper("E002", "Language model refusal variation",
                  "However refusal behavior varies by prompt.", "counter"),
        ]
        with tempfile.TemporaryDirectory() as d:
            result = ResearchPipeline(
                provider=DeterministicProvider(), runs_dir=d,
                counter_search_client=FakeClient(),
            ).run("How should LLM refusal boundaries be evaluated?", "ai", corpus)
            self.assertEqual(result.stage_status["skeptic_counter_search"], "executed")
            self.assertGreaterEqual(len(result.skeptic_traces), 1)
            self.assertIn("OA-N1", [e.evidence_id for e in result.evidence])
            self.assertTrue((Path(d) / result.run_id / "stages" / "11_skeptic_second_pass.json").exists())

    def test_fixture_report_carries_limitations(self):
        with tempfile.TemporaryDirectory() as d:
            results = run_fixture_benchmark(Path(d))
            self.assertEqual(results["case_count"], 2)
            self.assertIn("synthetic_fixture", results["methodology"])
            self.assertTrue((Path(d) / "fixture_retrieval.md").exists())


if __name__ == "__main__":
    unittest.main()
