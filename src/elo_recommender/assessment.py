from typing import Dict, Iterable, List

from elo_recommender.models import AssessmentOption, AssessmentQuestion
from elo_recommender.taxonomy import all_categories


ASSESSMENT_QUESTIONS = [
    AssessmentQuestion(
        id="experience_style",
        title="What kind of experience sounds most energizing?",
        prompt="Choose the option that feels closest to the kind of learning you want.",
        options=[
            AssessmentOption(
                id="discovery_lab",
                label="Discovery and research",
                description="I want to investigate questions, build knowledge, or work on a guided project.",
                weights={"research": 3.0, "entrepreneurship": 1.0},
            ),
            AssessmentOption(
                id="professional_team",
                label="Professional workplace",
                description="I want exposure to employers, teams, and real workplace expectations.",
                weights={"co_op": 3.0, "internship": 2.0, "leadership": 1.0},
            ),
            AssessmentOption(
                id="community_centered",
                label="Community impact",
                description="I want to work closely with communities and see a visible difference.",
                weights={"community_service": 3.0, "leadership": 2.0},
            ),
            AssessmentOption(
                id="global_immersion",
                label="Global immersion",
                description="I want a cross-cultural or international learning experience.",
                weights={"study_abroad": 3.0, "community_service": 1.0},
            ),
        ],
    ),
    AssessmentQuestion(
        id="desired_outcome",
        title="What is your main goal?",
        prompt="Pick the outcome that matters most right now.",
        options=[
            AssessmentOption(
                id="job_ready",
                label="Career readiness",
                description="I want professional experience that strengthens my resume quickly.",
                weights={"co_op": 3.0, "internship": 3.0},
            ),
            AssessmentOption(
                id="academic_depth",
                label="Academic depth",
                description="I want deeper subject knowledge, faculty mentorship, or a strong project portfolio.",
                weights={"research": 3.0},
            ),
            AssessmentOption(
                id="social_impact",
                label="Social impact",
                description="I want my experience to improve communities or solve a real public need.",
                weights={"community_service": 3.0, "leadership": 1.0},
            ),
            AssessmentOption(
                id="build_my_own",
                label="Build something new",
                description="I want to test ideas, make prototypes, or launch something of my own.",
                weights={"entrepreneurship": 3.0, "leadership": 1.0},
            ),
        ],
    ),
    AssessmentQuestion(
        id="structure_preference",
        title="How much structure do you want?",
        prompt="Choose the environment that fits your working style best.",
        options=[
            AssessmentOption(
                id="highly_structured",
                label="Highly structured",
                description="I want clear expectations, schedules, and formal support.",
                weights={"co_op": 2.0, "study_abroad": 1.0},
            ),
            AssessmentOption(
                id="mentor_project",
                label="Mentored project",
                description="I want guidance, but I still want room to own a project.",
                weights={"research": 2.0, "internship": 1.0},
            ),
            AssessmentOption(
                id="self_directed",
                label="Self-directed",
                description="I want flexibility to shape the work and make independent choices.",
                weights={"entrepreneurship": 2.0, "leadership": 1.0},
            ),
        ],
    ),
    AssessmentQuestion(
        id="compensation_importance",
        title="How important is paid work?",
        prompt="Be direct about whether compensation changes the right opportunity for you.",
        options=[
            AssessmentOption(
                id="essential",
                label="It is essential",
                description="A paid opportunity is strongly preferred or required.",
                weights={"co_op": 2.0, "internship": 2.0},
            ),
            AssessmentOption(
                id="nice_to_have",
                label="Nice to have",
                description="Compensation helps, but it is not the only factor.",
                weights={"co_op": 1.0, "internship": 1.0, "research": 0.5},
            ),
            AssessmentOption(
                id="not_required",
                label="Not required",
                description="I care more about fit and learning than compensation.",
                weights={"research": 1.0, "study_abroad": 1.0, "community_service": 1.0},
            ),
        ],
    ),
    AssessmentQuestion(
        id="global_interest",
        title="How interested are you in international experience?",
        prompt="Choose the option that matches your current interest in global learning.",
        options=[
            AssessmentOption(
                id="yes_high",
                label="Very interested",
                description="I actively want an international or cross-cultural opportunity.",
                weights={"study_abroad": 3.0},
            ),
            AssessmentOption(
                id="maybe_local_global",
                label="Open to it",
                description="I like global themes, even if the opportunity stays local.",
                weights={"study_abroad": 1.0, "community_service": 1.0},
            ),
            AssessmentOption(
                id="prefer_local",
                label="Prefer local options",
                description="I want opportunities closer to campus or my local community.",
                weights={"co_op": 1.0, "research": 1.0},
            ),
        ],
    ),
    AssessmentQuestion(
        id="impact_style",
        title="How do you want to show up in the experience?",
        prompt="Choose the role that feels most natural to you.",
        options=[
            AssessmentOption(
                id="lead_change",
                label="Lead and organize",
                description="I want responsibility, ownership, and visible leadership opportunities.",
                weights={"leadership": 3.0, "community_service": 2.0, "entrepreneurship": 1.0},
            ),
            AssessmentOption(
                id="collaborate",
                label="Collaborate closely",
                description="I want to be part of a team solving problems together.",
                weights={"co_op": 1.0, "research": 1.0, "community_service": 1.0},
            ),
            AssessmentOption(
                id="individual_depth",
                label="Go deep independently",
                description="I want focused work where I can develop expertise and ownership.",
                weights={"research": 2.0, "internship": 1.0},
            ),
        ],
    ),
]


def get_questions() -> List[AssessmentQuestion]:
    return ASSESSMENT_QUESTIONS


def score_answers(answers: Dict[str, str]) -> Dict[str, float]:
    category_scores = {category_id: 0.0 for category_id in all_categories()}

    for question in ASSESSMENT_QUESTIONS:
        option_id = answers.get(question.id)
        if not option_id:
            continue

        selected_option = None
        for option in question.options:
            if option.id == option_id:
                selected_option = option
                break

        if not selected_option:
            continue

        for category_id, weight in selected_option.weights.items():
            category_scores[category_id] = category_scores.get(category_id, 0.0) + weight

    return {key: value for key, value in category_scores.items() if value > 0}


def selected_option_ids(answers: Dict[str, str]) -> List[str]:
    selected = []
    for question in ASSESSMENT_QUESTIONS:
        option_id = answers.get(question.id)
        if option_id:
            selected.append(option_id)
    return selected


def required_question_ids() -> List[str]:
    return [question.id for question in ASSESSMENT_QUESTIONS]


def missing_questions(answers: Dict[str, str]) -> List[str]:
    provided = set(answers.keys())
    return [question_id for question_id in required_question_ids() if question_id not in provided]


def question_payload() -> List[Dict[str, object]]:
    return [question.to_dict() for question in get_questions()]
