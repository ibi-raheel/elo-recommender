from typing import Dict, List, Tuple


CATEGORY_DEFINITIONS = {
    "research": {
        "display_name": "Research",
        "description": "Faculty-guided inquiry, labs, design studios, and project-based investigation.",
        "keywords": [
            "research",
            "lab",
            "laboratory",
            "faculty mentor",
            "scholar",
            "investigation",
            "project",
            "analysis",
            "thesis",
        ],
    },
    "co_op": {
        "display_name": "Co-op",
        "description": "Structured professional placements tied to workplace experience.",
        "keywords": [
            "co-op",
            "coop",
            "co op",
            "employer",
            "placement",
            "professional practice",
            "career",
            "work experience",
            "full-time",
        ],
    },
    "study_abroad": {
        "display_name": "Study Abroad",
        "description": "International learning, exchange programs, and cross-cultural immersion.",
        "keywords": [
            "study abroad",
            "international",
            "exchange",
            "global",
            "travel",
            "immersion",
            "country",
            "cross-cultural",
        ],
    },
    "community_service": {
        "display_name": "Community Service",
        "description": "Community-based learning, civic engagement, service, and local impact work.",
        "keywords": [
            "community",
            "service",
            "civic",
            "engagement",
            "volunteer",
            "outreach",
            "partnership",
            "public service",
            "impact",
        ],
    },
    "internship": {
        "display_name": "Internship",
        "description": "Shorter-form professional experiences focused on skill building.",
        "keywords": [
            "internship",
            "intern",
            "summer program",
            "career readiness",
            "professional skills",
            "externship",
        ],
    },
    "entrepreneurship": {
        "display_name": "Entrepreneurship",
        "description": "Innovation, venture building, product incubation, and startup activity.",
        "keywords": [
            "startup",
            "venture",
            "innovation",
            "entrepreneurship",
            "incubator",
            "accelerator",
            "prototype",
            "founder",
        ],
    },
    "leadership": {
        "display_name": "Leadership",
        "description": "Programs centered on leadership development, facilitation, or peer guidance.",
        "keywords": [
            "leadership",
            "leader",
            "fellowship",
            "ambassador",
            "mentor",
            "facilitator",
            "student leader",
            "peer educator",
        ],
    },
}

OPPORTUNITY_HINTS = [
    "apply",
    "opportunity",
    "program",
    "experience",
    "placement",
    "fellowship",
    "research",
    "co-op",
    "internship",
    "study abroad",
    "service",
    "volunteer",
]


def category_display_name(category_id: str) -> str:
    definition = CATEGORY_DEFINITIONS.get(category_id, {})
    return definition.get("display_name", category_id.replace("_", " ").title())


def all_categories() -> List[str]:
    return list(CATEGORY_DEFINITIONS.keys())


def score_categories(text: str) -> Dict[str, float]:
    lowered = (text or "").lower()
    scores = {}

    for category_id, definition in CATEGORY_DEFINITIONS.items():
        score = 0.0
        for keyword in definition["keywords"]:
            if keyword in lowered:
                if " " in keyword:
                    score += 2.0
                else:
                    score += 1.0
        if score > 0:
            scores[category_id] = score

    return scores


def categorize_text(text: str, threshold: float = 1.0, limit: int = 3) -> List[str]:
    scores = score_categories(text)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [category_id for category_id, score in ranked if score >= threshold][:limit]


def looks_like_opportunity(text: str) -> bool:
    lowered = (text or "").lower()
    return any(hint in lowered for hint in OPPORTUNITY_HINTS)


def ranked_categories(text: str) -> List[Tuple[str, float]]:
    return sorted(score_categories(text).items(), key=lambda item: item[1], reverse=True)
