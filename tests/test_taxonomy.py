import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from elo_recommender.taxonomy import categorize_text, looks_like_opportunity


class TaxonomyTests(unittest.TestCase):
    def test_research_text_is_categorized(self) -> None:
        categories = categorize_text("Faculty research fellowship in a lab with project analysis.")
        self.assertIn("research", categories)

    def test_opportunity_hint_detection(self) -> None:
        self.assertTrue(looks_like_opportunity("Apply to this community service fellowship program."))


if __name__ == "__main__":
    unittest.main()
