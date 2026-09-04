from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from researchmind_yulan.models import EvidenceItem
from researchmind_yulan.pipeline import ResearchPipeline
from researchmind_yulan.providers import DeterministicProvider


class PipelineTest(unittest.TestCase):
    def test_pipeline_generates_auditable_outputs(self):
        corpus = [
            EvidenceItem(
                evidence_id="E001",
                title="Boundary benchmark",
                source_type="synthetic_demo",
                url="",
                excerpt="A benchmark reports a limitation in English-only refusal evaluation.",
                stance="positive",
                verified=False,
            ),
            EvidenceItem(
                evidence_id="E002",
                title="Over-refusal failure cases",
                source_type="synthetic_demo",
                url="",
                excerpt="An experiment finds over-refusal on benign prompts; however results vary by instruction style.",
                stance="counter",
                verified=False,
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            pipeline = ResearchPipeline(
                provider=DeterministicProvider(),
                runs_dir=tmp,
            )
            result = pipeline.run(
                question="How should LLM refusal boundaries be evaluated?",
                discipline="ai",
                corpus=corpus,
            )

            run_dir = Path(tmp) / result.run_id
            self.assertTrue((run_dir / "final_report.md").exists())
            self.assertTrue((run_dir / "audit_trail.json").exists())
            self.assertEqual(result.stage_status["decision_synthesizer"], "ok")
            self.assertGreaterEqual(len(result.gaps), 1)
            self.assertGreaterEqual(len(result.counter_evidence), 1)


if __name__ == "__main__":
    unittest.main()
