from __future__ import annotations

import json
import unittest

from researchmind_yulan.models import EvidenceItem, ResearchQuestion
from researchmind_yulan.providers import DeterministicProvider
from researchmind_yulan.semantic import (
    apply_analysis_stance,
    build_claim_evidence_graph,
    extract_evidence,
)


class JsonProvider:
    def complete(self, system: str, user: str) -> str:
        return json.dumps(
            {
                "research_question": "How refusal behavior changes near safety boundaries",
                "method": "benchmark",
                "sample": "multilingual prompts",
                "data": "boundary prompt set",
                "finding": "Binary refusal rate hides variation near the decision boundary.",
                "limitations": ["The benchmark covers only two model families."],
                "boundary_conditions": ["Results vary by prompt language."],
                "claims": [
                    {
                        "text": "Binary refusal rate can hide boundary variation.",
                        "relation": "supporting",
                        "confidence": 0.91,
                    },
                    {
                        "text": "The result may not generalize across languages.",
                        "relation": "boundary",
                        "confidence": 0.84,
                    },
                ],
            }
        )


class InvalidProvider:
    def complete(self, system: str, user: str) -> str:
        return "not-json"


class SemanticExtractionTest(unittest.TestCase):
    def setUp(self):
        self.question = ResearchQuestion(
            raw="How should LLM refusal boundaries be evaluated?",
            discipline="ai",
        )
        self.item = EvidenceItem(
            evidence_id="E001",
            title="Boundary benchmark",
            source_type="paper",
            url="https://example.org/paper",
            excerpt="A benchmark reports a limitation in binary refusal evaluation.",
        )

    def test_llm_json_is_normalized(self):
        analysis = extract_evidence(JsonProvider(), self.question, self.item)
        self.assertEqual(analysis.extraction_mode, "llm")
        self.assertEqual(analysis.method, "benchmark")
        self.assertEqual(len(analysis.claims), 2)
        self.assertEqual(analysis.claims[1].relation, "boundary")

        graph = build_claim_evidence_graph([analysis])
        self.assertEqual(len(graph.claims), 2)
        self.assertEqual(graph.links[0].evidence_id, "E001")
        self.assertEqual(graph.links[0].relation, "supporting")

    def test_invalid_llm_output_falls_back(self):
        analysis = extract_evidence(InvalidProvider(), self.question, self.item)
        self.assertEqual(analysis.extraction_mode, "heuristic")
        self.assertGreaterEqual(len(analysis.claims), 1)

    def test_deterministic_provider_never_requires_json(self):
        analysis = extract_evidence(DeterministicProvider(), self.question, self.item)
        self.assertEqual(analysis.extraction_mode, "heuristic")

    def test_analysis_relation_updates_evidence_stance(self):
        analysis = extract_evidence(JsonProvider(), self.question, self.item)
        evidence = apply_analysis_stance([self.item], [analysis])
        self.assertEqual(evidence[0].stance, "mixed")
        self.assertEqual(evidence[0].metadata["semantic_extraction_mode"], "llm")


if __name__ == "__main__":
    unittest.main()
