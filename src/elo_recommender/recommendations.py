from typing import Dict, List, Tuple

from elo_recommender.assessment import score_answers
from elo_recommender.models import Opportunity, OpportunityMatch, RecommendationResult
from elo_recommender.taxonomy import category_display_name


def _sorted_scores(category_scores: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(category_scores.items(), key=lambda item: item[1], reverse=True)


def _derive_preferences(answers: Dict[str, str]) -> Dict[str, bool]:
    return {
        "prefers_paid": answers.get("compensation_importance") == "essential",
        "prefers_global": answers.get("global_interest") == "yes_high",
        "prefers_service": answers.get("desired_outcome") == "social_impact",
        "prefers_research": answers.get("experience_style") == "discovery_lab",
    }


def _score_opportunity(
    opportunity: Opportunity,
    category_scores: Dict[str, float],
    preferences: Dict[str, bool],
) -> OpportunityMatch:
    score = 0.0
    reasons = []

    matched_categories = []
    for category_id in opportunity.categories:
        category_score = category_scores.get(category_id, 0.0)
        if category_score > 0:
            score += category_score
            matched_categories.append(category_id)

    if matched_categories:
        readable = ", ".join(category_display_name(category_id) for category_id in matched_categories)
        reasons.append("Matches your strongest category fit: {0}.".format(readable))

    if preferences["prefers_paid"] and opportunity.paid:
        score += 1.5
        reasons.append("This opportunity aligns with your need for paid experience.")

    if preferences["prefers_global"] and opportunity.international:
        score += 1.5
        reasons.append("This opportunity supports your interest in global learning.")

    if preferences["prefers_service"] and "community_service" in opportunity.categories:
        score += 1.0
        reasons.append("This opportunity fits your goal of community impact.")

    if preferences["prefers_research"] and "research" in opportunity.categories:
        score += 1.0
        reasons.append("This opportunity supports a project or inquiry-driven learning style.")

    return OpportunityMatch(opportunity=opportunity, score=score, reasons=reasons)


def _build_guidance(category_scores: Dict[str, float], matches: List[OpportunityMatch]) -> List[str]:
    sorted_categories = _sorted_scores(category_scores)
    if not sorted_categories:
        return ["Complete all assessment questions to generate recommendations."]

    top_labels = [category_display_name(category_id) for category_id, _ in sorted_categories[:3]]
    guidance = [
        "Start by reviewing opportunities in {0}.".format(", ".join(top_labels)),
    ]

    if not matches:
        guidance.append(
            "No matching records are in the current dataset yet. Run the crawler or load a reviewed opportunity file."
        )

    return guidance


def recommend_opportunities(answers: Dict[str, str], opportunities: List[Opportunity], limit: int = 6) -> RecommendationResult:
    category_scores = score_answers(answers)
    preferences = _derive_preferences(answers)

    scored_matches = []
    for opportunity in opportunities:
        match = _score_opportunity(opportunity, category_scores, preferences)
        if match.score > 0:
            scored_matches.append(match)

    scored_matches.sort(key=lambda match: match.score, reverse=True)
    top_matches = scored_matches[:limit]
    guidance = _build_guidance(category_scores, top_matches)

    return RecommendationResult(
        category_scores=dict(_sorted_scores(category_scores)),
        matches=top_matches,
        guidance=guidance,
    )
