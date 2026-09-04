from __future__ import annotations

import unittest

from researchmind_yulan.verification import normalize_doi, title_similarity


class VerificationTest(unittest.TestCase):
    def test_normalize_doi(self):
        self.assertEqual(
            normalize_doi("https://doi.org/10.1234/Example.1"),
            "10.1234/Example.1",
        )
        self.assertEqual(normalize_doi("doi: 10.1000/test"), "10.1000/test")

    def test_title_similarity(self):
        score = title_similarity(
            "Large Language Model Refusal Boundaries: An Evaluation",
            "Large-language model refusal boundaries: an evaluation",
        )
        self.assertGreaterEqual(score, 0.95)
        self.assertLess(title_similarity("Unrelated paper", "Another topic"), 0.6)


if __name__ == "__main__":
    unittest.main()
