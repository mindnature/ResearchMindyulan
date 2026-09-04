from __future__ import annotations

import unittest

from researchmind_yulan.retrieval import OpenAlexClient, reconstruct_abstract


class RetrievalTest(unittest.TestCase):
    def test_reconstruct_abstract(self):
        index = {
            "ResearchMind": [0],
            "tests": [1],
            "research": [2],
            "decisions": [3],
        }
        self.assertEqual(
            reconstruct_abstract(index),
            "ResearchMind tests research decisions",
        )

    def test_openalex_work_to_evidence(self):
        work = {
            "id": "https://openalex.org/W123",
            "doi": "https://doi.org/10.1234/example",
            "title": "A Test Paper",
            "type": "article",
            "publication_year": 2026,
            "language": "en",
            "abstract_inverted_index": {
                "A": [0],
                "benchmark": [1],
                "limitation": [2],
            },
            "authorships": [
                {"author": {"display_name": "Test Author"}},
            ],
            "primary_location": {
                "source": {"display_name": "Test Journal"},
            },
            "cited_by_count": 5,
        }

        item = OpenAlexClient._to_evidence(work)
        self.assertEqual(item.evidence_id, "OA-W123")
        self.assertEqual(item.title, "A Test Paper")
        self.assertTrue(item.verified)
        self.assertEqual(item.metadata["provider"], "openalex")
        self.assertFalse(item.metadata["claim_independently_verified"])
        self.assertIn("benchmark limitation", item.excerpt)


if __name__ == "__main__":
    unittest.main()
