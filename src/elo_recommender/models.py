from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass
class Opportunity:
    id: str
    title: str
    url: str
    summary: str
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source_page: str = ""
    audience: List[str] = field(default_factory=list)
    format: str = ""
    paid: Optional[bool] = None
    international: Optional[bool] = None
    location: str = ""
    commitment: str = ""
    scraped_at: str = ""
    confidence: float = 0.0
    source_type: str = "crawl"

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class AssessmentOption:
    id: str
    label: str
    description: str
    weights: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class AssessmentQuestion:
    id: str
    title: str
    prompt: str
    options: List[AssessmentOption]

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["options"] = [option.to_dict() for option in self.options]
        return data


@dataclass
class OpportunityMatch:
    opportunity: Opportunity
    score: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "opportunity": self.opportunity.to_dict(),
            "score": self.score,
            "reasons": self.reasons,
        }


@dataclass
class RecommendationResult:
    category_scores: Dict[str, float]
    matches: List[OpportunityMatch]
    guidance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "category_scores": self.category_scores,
            "matches": [match.to_dict() for match in self.matches],
            "guidance": self.guidance,
        }
