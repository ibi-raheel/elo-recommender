import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from elo_recommender.models import Opportunity
from elo_recommender.recommendations import recommend_opportunities


class RecommendationTests(unittest.TestCase):
    def test_paid_professional_answers_rank_coop(self) -> None:
        answers = {
            "experience_style": "professional_team",
            "desired_outcome": "job_ready",
            "structure_preference": "highly_structured",
            "compensation_importance": "essential",
            "global_interest": "prefer_local",
            "impact_style": "collaborate",
        }

        opportunities = [
            Opportunity(
                id="coop",
                title="Demo co-op",
                url="",
                summary="Paid professional placement",
                categories=["co_op"],
                paid=True,
                international=False,
            ),
            Opportunity(
                id="research",
                title="Demo research",
                url="",
                summary="Faculty mentored lab project",
                categories=["research"],
                paid=False,
                international=False,
            ),
        ]

        result = recommend_opportunities(answers, opportunities)
        self.assertEqual("co_op", next(iter(result.category_scores)))
        self.assertEqual("coop", result.matches[0].opportunity.id)


if __name__ == "__main__":
    unittest.main()
