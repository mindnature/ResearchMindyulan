from __future__ import annotations

import unittest

from researchmind_yulan.evidence import provenance_grade
from researchmind_yulan.models import EvidenceItem


class EvidenceGradeTest(unittest.TestCase):
    def make_item(self, metadata):
        return EvidenceItem(
            evidence_id="E1",
            title="Example",
            source_type="article",
            url="https://doi.org/10.1234/example",
            excerpt="Example abstract",
            metadata=metadata,
        )

    def test_crossref_confirmed_grade(self):
        item = self.make_item(
            {
                "doi": "https://doi.org/10.1234/example",
                "source_record_verified": True,
                "crossref_record_verified": True,
                "crossref_title_match": True,
            }
        )
        self.assertEqual(provenance_grade(item), "A_crossref_confirmed")

    def test_provider_confirmed_with_doi_grade(self):
        item = self.make_item(
            {
                "doi": "https://doi.org/10.1234/example",
                "source_record_verified": True,
            }
        )
        self.assertEqual(provenance_grade(item), "B_provider_confirmed_with_doi")

    def test_unverified_fixture_grade(self):
        item = self.make_item({})
        self.assertEqual(provenance_grade(item), "D_unverified_or_fixture")


if __name__ == "__main__":
    unittest.main()
