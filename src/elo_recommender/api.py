from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from elo_recommender.assessment import missing_questions, question_payload
from elo_recommender.recommendations import recommend_opportunities
from elo_recommender.storage import dataset_metadata, load_opportunities
from elo_recommender.taxonomy import CATEGORY_DEFINITIONS, category_display_name


class RecommendationRequest(BaseModel):
    answers: Dict[str, str]
    dataset_path: Optional[str] = None


app = FastAPI(
    title="Drexel ELO Recommender",
    description="Scrape, classify, and recommend experiential learning opportunities.",
    version="0.1.0",
)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return HTML_TEMPLATE


@app.get("/api/dataset")
def get_dataset(dataset_path: Optional[str] = None) -> dict:
    return dataset_metadata(dataset_path)


@app.get("/api/categories")
def get_categories() -> list:
    return [
        {
            "id": category_id,
            "label": category_display_name(category_id),
            "description": definition["description"],
        }
        for category_id, definition in CATEGORY_DEFINITIONS.items()
    ]


@app.get("/api/questions")
def get_questions() -> list:
    return question_payload()


@app.get("/api/opportunities")
def get_opportunities(
    category: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    dataset_path: Optional[str] = None,
) -> dict:
    opportunities = load_opportunities(dataset_path)
    if category:
        opportunities = [opportunity for opportunity in opportunities if category in opportunity.categories]
    sliced = opportunities[:limit]
    return {
        "count": len(sliced),
        "items": [opportunity.to_dict() for opportunity in sliced],
    }


@app.post("/api/recommendations")
def get_recommendations(request: RecommendationRequest) -> dict:
    missing = missing_questions(request.answers)
    if missing:
        raise HTTPException(status_code=400, detail="Missing assessment answers: {0}".format(", ".join(missing)))

    opportunities = load_opportunities(request.dataset_path)
    result = recommend_opportunities(request.answers, opportunities)
    return result.to_dict()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Drexel ELO Recommender</title>
  <style>
    :root {
      --drexel-blue: #07294d;
      --drexel-blue-deep: #041b33;
      --drexel-cyan: #006699;
      --drexel-sky: #6cace4;
      --drexel-gold: #ffc600;
      --drexel-orange: #d14124;
      --cream: #f8f5ee;
      --paper: rgba(255, 255, 255, 0.9);
      --ink: #08203c;
      --muted: #52657c;
      --line: rgba(7, 41, 77, 0.12);
      --line-strong: rgba(255, 198, 0, 0.32);
      --shadow: 0 28px 90px rgba(2, 19, 39, 0.28);
      --shadow-soft: 0 18px 50px rgba(7, 41, 77, 0.12);
    }

    html {
      scroll-behavior: smooth;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Futura", "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      color: #ffffff;
      background:
        radial-gradient(circle at 12% 14%, rgba(255, 198, 0, 0.2), transparent 18%),
        radial-gradient(circle at 88% 16%, rgba(108, 172, 228, 0.18), transparent 16%),
        radial-gradient(circle at 50% 105%, rgba(209, 65, 36, 0.18), transparent 22%),
        linear-gradient(180deg, var(--drexel-blue-deep) 0%, var(--drexel-blue) 38%, #0a315b 100%);
      overflow-x: hidden;
      position: relative;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.42), transparent 85%);
      pointer-events: none;
    }

    .page {
      width: min(1240px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 56px;
    }

    .hero-shell {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
      gap: 24px;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 34px;
      background: linear-gradient(145deg, rgba(6, 31, 58, 0.9), rgba(3, 20, 38, 0.96));
      box-shadow: var(--shadow);
      padding: 34px;
      isolation: isolate;
      animation: fade-up 720ms ease both;
    }

    .hero-shell::before {
      content: "";
      position: absolute;
      inset: -1px;
      background:
        linear-gradient(120deg, rgba(255, 198, 0, 0.14), transparent 24%, transparent 70%, rgba(108, 172, 228, 0.12)),
        radial-gradient(circle at 78% 18%, rgba(255, 198, 0, 0.22), transparent 24%);
      pointer-events: none;
      z-index: -1;
    }

    .hero-copy {
      position: relative;
      padding-right: 12px;
    }

    .hero-copy::after {
      content: "";
      position: absolute;
      right: 10%;
      bottom: -12px;
      width: 220px;
      height: 220px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(255, 198, 0, 0.24), transparent 70%);
      filter: blur(10px);
      pointer-events: none;
      z-index: -1;
    }

    h1, h2, h3 {
      margin: 0 0 10px;
      line-height: 1.05;
    }

    h1 {
      font-family: "Miller Display", Georgia, "Times New Roman", serif;
      font-size: clamp(3rem, 6vw, 5.6rem);
      letter-spacing: -0.04em;
      max-width: 10ch;
      color: #ffffff;
    }

    h2 {
      font-family: "Miller Display", Georgia, "Times New Roman", serif;
      font-size: clamp(1.9rem, 3vw, 2.6rem);
      letter-spacing: -0.03em;
      color: var(--ink);
    }

    h3 {
      font-size: 1.15rem;
      line-height: 1.2;
    }

    p {
      margin: 0;
      line-height: 1.65;
    }

    a {
      color: inherit;
      text-decoration: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      border: 1px solid rgba(255, 198, 0, 0.28);
      border-radius: 999px;
      padding: 10px 14px;
      margin-bottom: 18px;
      background: rgba(255, 255, 255, 0.08);
      font-size: 0.84rem;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: #f9df74;
      backdrop-filter: blur(16px);
    }

    .eyebrow-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--drexel-gold);
      box-shadow: 0 0 0 8px rgba(255, 198, 0, 0.12);
    }

    .hero-body {
      max-width: 58ch;
      font-size: 1.02rem;
      color: rgba(255, 255, 255, 0.78);
      margin-top: 14px;
    }

    .hero-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 28px;
    }

    .button-link,
    button {
      appearance: none;
      position: relative;
      overflow: hidden;
      border: 0;
      border-radius: 999px;
      padding: 14px 20px;
      font: inherit;
      font-weight: 700;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
    }

    .button-link:hover,
    button:hover {
      transform: translateY(-1px);
    }

    .button-link.primary,
    .primary {
      background: linear-gradient(135deg, #ffd44c 0%, var(--drexel-gold) 58%, #efb900 100%);
      color: var(--drexel-blue-deep);
      box-shadow: 0 18px 40px rgba(255, 198, 0, 0.24);
    }

    .button-link.primary::after,
    .primary::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(115deg, transparent 20%, rgba(255, 255, 255, 0.5) 44%, transparent 68%);
      transform: translateX(-130%);
      animation: sheen 4.8s ease-in-out infinite;
    }

    .button-link.secondary {
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.16);
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
    }

    button.secondary {
      background: rgba(7, 41, 77, 0.06);
      color: var(--drexel-blue);
      border: 1px solid rgba(7, 41, 77, 0.1);
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
    }

    button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }

    .hero-dashboard {
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 28px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.04)),
        rgba(4, 27, 51, 0.66);
      padding: 22px;
      backdrop-filter: blur(18px);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .dashboard-top,
    .section-heading,
    .metric-head,
    .match-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
    }

    .kicker {
      display: block;
      margin-bottom: 8px;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--drexel-cyan);
    }

    .hero-dashboard .kicker,
    .hero-dashboard p,
    .hero-dashboard h3,
    .panel-dark .kicker,
    .panel-dark p,
    .panel-dark h3 {
      color: rgba(255, 255, 255, 0.82);
    }

    .signal {
      width: 12px;
      height: 12px;
      border-radius: 999px;
      background: #72ffb3;
      box-shadow: 0 0 0 8px rgba(114, 255, 179, 0.12);
      animation: pulse 1.8s ease-in-out infinite;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 18px;
    }

    .metric-card {
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 20px;
      padding: 14px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.03));
    }

    .metric-card strong {
      display: block;
      margin-top: 6px;
      font-size: 1.4rem;
      line-height: 1;
      color: #ffffff;
    }

    .metric-card span {
      font-size: 0.82rem;
      color: rgba(255, 255, 255, 0.62);
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }

    .journey-grid {
      display: grid;
      gap: 12px;
      margin-top: 20px;
    }

    .journey-card {
      display: grid;
      grid-template-columns: 42px 1fr;
      gap: 12px;
      padding: 14px;
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(255, 255, 255, 0.04);
    }

    .journey-index {
      width: 42px;
      height: 42px;
      display: grid;
      place-items: center;
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(255, 198, 0, 0.24), rgba(255, 198, 0, 0.08));
      color: #fff2be;
      font-weight: 800;
    }

    .journey-card p {
      color: rgba(255, 255, 255, 0.68);
    }

    .assessment-stage {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) 340px;
      gap: 24px;
      align-items: start;
      margin-top: 28px;
    }

    .panel {
      border: 1px solid var(--line);
      border-radius: 28px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(249, 246, 240, 0.92));
      color: var(--ink);
      box-shadow: var(--shadow-soft);
      padding: 26px;
      animation: fade-up 720ms ease both;
    }

    .panel-dark {
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 24px;
      background: linear-gradient(180deg, rgba(6, 31, 58, 0.9), rgba(3, 18, 34, 0.94));
      box-shadow: var(--shadow-soft);
      padding: 22px;
      color: #ffffff;
    }

    .panel-accent {
      background:
        radial-gradient(circle at top right, rgba(255, 198, 0, 0.24), transparent 30%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(252, 247, 233, 0.94));
    }

    .assessment-panel {
      position: relative;
      overflow: hidden;
    }

    .assessment-panel::after {
      content: "";
      position: absolute;
      top: 0;
      right: 0;
      width: 220px;
      height: 220px;
      background: radial-gradient(circle, rgba(108, 172, 228, 0.18), transparent 68%);
      pointer-events: none;
    }

    .completion-chip,
    .status-chip,
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      padding: 10px 14px;
      border-radius: 999px;
      font-size: 0.88rem;
      font-weight: 700;
      border: 1px solid rgba(7, 41, 77, 0.08);
      background: rgba(7, 41, 77, 0.05);
      color: var(--ink);
    }

    .status-chip[data-tone="live"],
    .status-badge[data-tone="live"] {
      background: rgba(0, 102, 153, 0.1);
      color: var(--drexel-cyan);
      border-color: rgba(0, 102, 153, 0.18);
    }

    .status-chip[data-tone="demo"],
    .status-badge[data-tone="demo"] {
      background: rgba(255, 198, 0, 0.12);
      color: #8a6100;
      border-color: rgba(255, 198, 0, 0.28);
    }

    .status-chip[data-tone="ready"] {
      background: rgba(0, 102, 153, 0.12);
      color: var(--drexel-cyan);
      border-color: rgba(0, 102, 153, 0.2);
    }

    .status-chip[data-tone="idle"] {
      background: rgba(7, 41, 77, 0.05);
      color: var(--muted);
    }

    .status-chip[data-tone="error"] {
      background: rgba(209, 65, 36, 0.12);
      color: var(--drexel-orange);
      border-color: rgba(209, 65, 36, 0.22);
    }

    .progress-shell {
      margin-top: 20px;
      padding: 18px;
      border-radius: 24px;
      border: 1px solid rgba(7, 41, 77, 0.08);
      background: rgba(7, 41, 77, 0.03);
    }

    .progress-track {
      width: 100%;
      height: 12px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(7, 41, 77, 0.08);
      border: 1px solid rgba(7, 41, 77, 0.05);
    }

    .progress-fill {
      display: block;
      height: 100%;
      width: 0%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--drexel-gold), #ffe180 45%, var(--drexel-sky));
      box-shadow: 0 0 24px rgba(255, 198, 0, 0.34);
      transition: width 260ms ease;
    }

    .progress-copy {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-top: 10px;
      font-size: 0.94rem;
      color: var(--muted);
    }

    .microcopy {
      color: var(--muted);
    }

    .question {
      padding: 24px 0;
      border-top: 1px solid rgba(7, 41, 77, 0.08);
    }

    .question:first-of-type {
      border-top: 0;
      padding-top: 12px;
    }

    .question-top {
      display: grid;
      grid-template-columns: 54px 1fr;
      gap: 16px;
      align-items: start;
    }

    .question-number {
      display: inline-grid;
      place-items: center;
      width: 54px;
      height: 54px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(7, 41, 77, 0.08), rgba(7, 41, 77, 0.02));
      color: var(--drexel-blue);
      font-size: 0.92rem;
      font-weight: 800;
      letter-spacing: 0.08em;
    }

    .options {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-top: 16px;
    }

    label.option {
      position: relative;
      display: grid;
      gap: 10px;
      min-height: 152px;
      border: 1px solid rgba(7, 41, 77, 0.1);
      border-radius: 22px;
      padding: 16px;
      cursor: pointer;
      transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(248, 245, 238, 0.76));
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }

    label.option:hover {
      transform: translateY(-2px);
      border-color: rgba(7, 41, 77, 0.18);
      box-shadow: 0 16px 34px rgba(7, 41, 77, 0.09);
    }

    label.option input {
      position: absolute;
      opacity: 0;
      pointer-events: none;
    }

    label.option.is-selected {
      border-color: var(--line-strong);
      background:
        linear-gradient(180deg, rgba(255, 198, 0, 0.18), rgba(255, 255, 255, 0.96)),
        rgba(255, 255, 255, 0.96);
      box-shadow: 0 20px 46px rgba(7, 41, 77, 0.12), inset 0 0 0 1px rgba(255, 198, 0, 0.32);
      transform: translateY(-2px);
    }

    .option-head {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 800;
      color: var(--ink);
    }

    .radio-mark {
      width: 22px;
      height: 22px;
      border-radius: 999px;
      border: 2px solid rgba(7, 41, 77, 0.22);
      background: rgba(255, 255, 255, 0.72);
      box-shadow: inset 0 0 0 4px rgba(255, 255, 255, 0.8);
      transition: border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
      flex: 0 0 auto;
    }

    label.option.is-selected .radio-mark {
      border-color: var(--drexel-gold);
      background: var(--drexel-blue);
      box-shadow: inset 0 0 0 4px var(--drexel-gold), 0 0 0 6px rgba(255, 198, 0, 0.14);
    }

    .option-copy {
      color: var(--muted);
      font-size: 0.95rem;
    }

    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 24px;
    }

    .insight-rail {
      display: grid;
      gap: 18px;
      position: sticky;
      top: 22px;
    }

    .insight-metric {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      padding-top: 14px;
      margin-top: 14px;
      border-top: 1px solid rgba(7, 41, 77, 0.08);
    }

    .insight-metric strong {
      font-family: "Miller Display", Georgia, "Times New Roman", serif;
      font-size: 2.2rem;
      line-height: 1;
      color: var(--drexel-blue);
    }

    .rail-tags,
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }

    .pill,
    .rail-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      width: fit-content;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255, 198, 0, 0.14);
      color: #866100;
      border: 1px solid rgba(255, 198, 0, 0.22);
      font-size: 0.88rem;
      font-weight: 700;
    }

    .rail-tag {
      background: rgba(7, 41, 77, 0.06);
      color: var(--drexel-blue);
      border-color: rgba(7, 41, 77, 0.08);
    }

    .results-zone {
      margin-top: 28px;
      display: grid;
      gap: 18px;
    }

    .results-root {
      display: grid;
      gap: 18px;
    }

    .summary-panel {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(260px, 0.82fr);
      gap: 18px;
      align-items: start;
    }

    .category-list {
      display: grid;
      gap: 14px;
      margin-top: 18px;
    }

    .category-row {
      display: grid;
      gap: 8px;
    }

    .category-row-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 0.95rem;
    }

    .meter {
      height: 10px;
      overflow: hidden;
      border-radius: 999px;
      background: rgba(7, 41, 77, 0.08);
    }

    .meter > span {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--drexel-blue), var(--drexel-cyan), var(--drexel-gold));
    }

    .results-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }

    .match-card {
      display: grid;
      gap: 12px;
      min-height: 260px;
      position: relative;
      overflow: hidden;
    }

    .match-card::before {
      content: "";
      position: absolute;
      inset: 0 0 auto;
      height: 6px;
      background: linear-gradient(90deg, var(--drexel-blue), var(--drexel-cyan), var(--drexel-gold));
    }

    .match-score {
      display: inline-flex;
      align-items: center;
      width: fit-content;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(7, 41, 77, 0.06);
      color: var(--drexel-blue);
      font-weight: 800;
      font-size: 0.9rem;
    }

    .match-link {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      font-weight: 700;
      color: var(--drexel-cyan);
    }

    .match-link::after {
      content: "↗";
      font-size: 0.9rem;
    }

    .muted {
      color: var(--muted);
    }

    .empty-panel {
      display: grid;
      gap: 10px;
      min-height: 220px;
      place-content: center;
      text-align: center;
      background:
        radial-gradient(circle at top center, rgba(255, 198, 0, 0.18), transparent 34%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(250, 245, 236, 0.92));
    }

    .empty-panel h3 {
      font-family: "Miller Display", Georgia, "Times New Roman", serif;
      font-size: 2rem;
      color: var(--ink);
    }

    .subtle-rule {
      width: 100%;
      height: 1px;
      margin: 18px 0;
      background: linear-gradient(90deg, rgba(7, 41, 77, 0), rgba(7, 41, 77, 0.12), rgba(7, 41, 77, 0));
    }

    @keyframes sheen {
      0%, 64%, 100% {
        transform: translateX(-130%);
      }

      78% {
        transform: translateX(130%);
      }
    }

    @keyframes fade-up {
      from {
        opacity: 0;
        transform: translateY(18px);
      }

      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
        opacity: 1;
      }

      50% {
        transform: scale(1.08);
        opacity: 0.76;
      }
    }

    @media (max-width: 1080px) {
      .hero-shell,
      .assessment-stage,
      .summary-panel {
        grid-template-columns: 1fr;
      }

      .insight-rail {
        position: static;
      }
    }

    @media (max-width: 720px) {
      .page {
        width: min(100%, calc(100% - 20px));
        padding-top: 20px;
      }

      .hero-shell,
      .panel,
      .panel-dark {
        border-radius: 24px;
        padding: 22px;
      }

      .metric-grid {
        grid-template-columns: 1fr;
      }

      .question-top {
        grid-template-columns: 1fr;
      }

      .options {
        grid-template-columns: 1fr;
      }

      .progress-copy,
      .section-heading,
      .dashboard-top,
      .match-head {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  </style>
</head>
<body>
  <main class="page">
    <section class="hero-shell">
      <div class="hero-copy">
        <div class="eyebrow">
          <span class="eyebrow-dot"></span>
          Drexel experiential learning navigator
        </div>
        <h1>Make Drexel opportunities feel curated, not chaotic.</h1>
        <p class="hero-body">
          This interface turns the ELO search into a premium guided experience: collect opportunities across Drexel,
          classify them into meaningful pathways, and match each student to the work that actually fits how they want to learn.
        </p>
        <div class="hero-actions">
          <a class="button-link primary" href="#assessment">Start the assessment</a>
          <a class="button-link secondary" href="#results-zone">Preview the recommendation layer</a>
        </div>
      </div>

      <aside class="hero-dashboard">
        <div class="dashboard-top">
          <div>
            <span class="kicker">Experience cockpit</span>
            <h3>One flow. Three decisive moves.</h3>
          </div>
          <span class="signal"></span>
        </div>

        <div class="metric-grid">
          <article class="metric-card">
            <span>Dataset mode</span>
            <strong id="metric-data-mode">Loading</strong>
          </article>
          <article class="metric-card">
            <span>Records loaded</span>
            <strong id="metric-opportunity-count">0</strong>
          </article>
          <article class="metric-card">
            <span>Assessment completion</span>
            <strong id="metric-completion">0%</strong>
          </article>
          <article class="metric-card">
            <span>Recommendation state</span>
            <strong id="metric-state">Standby</strong>
          </article>
        </div>

        <div class="journey-grid">
          <article class="journey-card">
            <div class="journey-index">01</div>
            <div>
              <h3>Collect</h3>
              <p>Scrape Drexel pages into one opportunity inventory.</p>
            </div>
          </article>
          <article class="journey-card">
            <div class="journey-index">02</div>
            <div>
              <h3>Classify</h3>
              <p>Sort records into research, co-op, study abroad, service, and more.</p>
            </div>
          </article>
          <article class="journey-card">
            <div class="journey-index">03</div>
            <div>
              <h3>Recommend</h3>
              <p>Turn preferences into a student-specific ELO path.</p>
            </div>
          </article>
        </div>
      </aside>
    </section>

    <section class="assessment-stage" id="assessment">
      <article class="panel assessment-panel">
        <div class="section-heading">
          <div>
            <span class="kicker">Student assessment</span>
            <h2>Find the ELO that feels right to move toward.</h2>
            <p class="muted">Each question sharpens the recommendation engine. Complete all six to unlock the fit map.</p>
          </div>
          <div class="completion-chip" id="completion-chip">0 / 0 answered</div>
        </div>

        <div class="progress-shell">
          <div class="progress-track">
            <span class="progress-fill" id="progress-fill"></span>
          </div>
          <div class="progress-copy">
            <span id="progress-caption">Loading assessment…</span>
            <strong id="progress-value">0%</strong>
          </div>
        </div>

        <form id="assessment-form"></form>

        <div class="actions">
          <button class="primary" id="submit-button" type="button" disabled>Answer every question to continue</button>
          <button class="secondary" id="reset-button" type="button">Reset selections</button>
        </div>
      </article>

      <aside class="insight-rail">
        <article class="panel panel-accent">
          <span class="kicker">Progress</span>
          <h3>Assessment readiness</h3>
          <p class="muted">The interaction should feel quick and deliberate, not like a clunky survey.</p>
          <div class="insight-metric">
            <strong id="rail-progress">0%</strong>
            <span class="status-chip" id="results-status" data-tone="idle">Waiting for answers</span>
          </div>
        </article>

        <article class="panel">
          <span class="kicker">Dataset status</span>
          <h3 id="dataset-mode">Loading dataset…</h3>
          <p id="dataset-count" class="muted"></p>
          <div class="subtle-rule"></div>
          <p class="muted">The app automatically switches to a live crawl file when `data/opportunities.json` exists.</p>
        </article>

        <article class="panel-dark">
          <span class="kicker">Emerging fit</span>
          <h3>Top pathways</h3>
          <p id="rail-summary" class="muted">Your strongest-fit categories will surface here after the assessment is complete.</p>
          <div id="rail-tags" class="rail-tags"></div>
        </article>
      </aside>
    </section>

    <section class="results-zone" id="results-zone">
      <div class="section-heading">
        <div>
          <span class="eyebrow" style="margin-bottom: 10px; background: rgba(255, 255, 255, 0.08); color: #f9df74;">Recommendation output</span>
          <h2 style="color: #ffffff;">Your best-fit Drexel opportunity stack</h2>
          <p style="color: rgba(255, 255, 255, 0.72);">A strong result should tell the student what to explore first and why.</p>
        </div>
        <span class="status-chip" id="results-status-large" data-tone="idle">Awaiting completion</span>
      </div>
      <div id="results" class="results-root"></div>
    </section>
  </main>

  <script>
    const form = document.getElementById("assessment-form");
    const results = document.getElementById("results");
    const submitButton = document.getElementById("submit-button");
    const resetButton = document.getElementById("reset-button");
    const datasetMode = document.getElementById("dataset-mode");
    const datasetCount = document.getElementById("dataset-count");
    const completionChip = document.getElementById("completion-chip");
    const progressFill = document.getElementById("progress-fill");
    const progressCaption = document.getElementById("progress-caption");
    const progressValue = document.getElementById("progress-value");
    const railProgress = document.getElementById("rail-progress");
    const resultsStatus = document.getElementById("results-status");
    const resultsStatusLarge = document.getElementById("results-status-large");
    const railSummary = document.getElementById("rail-summary");
    const railTags = document.getElementById("rail-tags");
    const metricDataMode = document.getElementById("metric-data-mode");
    const metricOpportunityCount = document.getElementById("metric-opportunity-count");
    const metricCompletion = document.getElementById("metric-completion");
    const metricState = document.getElementById("metric-state");

    let totalQuestions = 0;
    let categoryLabels = {};

    async function fetchJson(path, options) {
      const response = await fetch(path, options);
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Request failed");
      }
      return response.json();
    }

    function titleCase(value) {
      return value
        .split("_")
        .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
        .join(" ");
    }

    function formatCategory(categoryId) {
      return categoryLabels[categoryId] || titleCase(categoryId);
    }

    function createTag(text, className = "pill") {
      const span = document.createElement("span");
      span.className = className;
      span.textContent = text;
      return span;
    }

    function setStatus(text, tone) {
      resultsStatus.textContent = text;
      resultsStatus.dataset.tone = tone;
      resultsStatusLarge.textContent = text;
      resultsStatusLarge.dataset.tone = tone;
      metricState.textContent = text;
    }

    function collectAnswers() {
      const answers = {};
      new FormData(form).forEach((value, key) => {
        answers[key] = value;
      });
      return answers;
    }

    function updateSelectionState() {
      form.querySelectorAll("label.option").forEach((optionLabel) => {
        const input = optionLabel.querySelector("input");
        optionLabel.classList.toggle("is-selected", Boolean(input && input.checked));
      });
    }

    function updateProgress() {
      const answered = Object.keys(collectAnswers()).length;
      const percent = totalQuestions ? Math.round((answered / totalQuestions) * 100) : 0;
      const remaining = Math.max(totalQuestions - answered, 0);

      progressFill.style.width = percent + "%";
      progressValue.textContent = percent + "%";
      railProgress.textContent = percent + "%";
      completionChip.textContent = answered + " / " + totalQuestions + " answered";
      metricCompletion.textContent = percent + "%";

      if (!totalQuestions) {
        progressCaption.textContent = "Loading assessment…";
      } else if (!remaining) {
        progressCaption.textContent = "Everything is answered. Generate the recommendation.";
      } else {
        progressCaption.textContent = remaining + " question" + (remaining === 1 ? "" : "s") + " remaining.";
      }

      submitButton.disabled = answered !== totalQuestions || totalQuestions === 0;
      submitButton.textContent = submitButton.disabled
        ? "Answer every question to continue"
        : "Generate your Drexel fit";
    }

    function renderQuestions(questions) {
      totalQuestions = questions.length;
      form.innerHTML = "";

      questions.forEach((question, index) => {
        const questionEl = document.createElement("section");
        questionEl.className = "question";

        const top = document.createElement("div");
        top.className = "question-top";

        const number = document.createElement("div");
        number.className = "question-number";
        number.textContent = String(index + 1).padStart(2, "0");

        const copy = document.createElement("div");
        const title = document.createElement("h3");
        title.textContent = question.title;
        const prompt = document.createElement("p");
        prompt.className = "muted";
        prompt.textContent = question.prompt;
        copy.appendChild(title);
        copy.appendChild(prompt);

        top.appendChild(number);
        top.appendChild(copy);

        const options = document.createElement("div");
        options.className = "options";

        question.options.forEach((option) => {
          const label = document.createElement("label");
          label.className = "option";

          const input = document.createElement("input");
          input.type = "radio";
          input.name = question.id;
          input.value = option.id;

          const head = document.createElement("div");
          head.className = "option-head";

          const radioMark = document.createElement("span");
          radioMark.className = "radio-mark";

          const text = document.createElement("span");
          text.textContent = option.label;

          head.appendChild(radioMark);
          head.appendChild(text);

          const description = document.createElement("p");
          description.className = "option-copy";
          description.textContent = option.description;

          label.appendChild(input);
          label.appendChild(head);
          label.appendChild(description);
          options.appendChild(label);
        });

        questionEl.appendChild(top);
        questionEl.appendChild(options);
        form.appendChild(questionEl);
      });

      updateSelectionState();
      updateProgress();
    }

    function renderRailCategories(scoreEntries) {
      railTags.innerHTML = "";
      if (!scoreEntries.length) {
        railSummary.textContent = "Your strongest-fit categories will surface here after the assessment is complete.";
        return;
      }

      railSummary.textContent = "These are the pathways currently rising to the top based on the student’s answers.";
      scoreEntries.slice(0, 3).forEach(([category]) => {
        railTags.appendChild(createTag(formatCategory(category), "rail-tag"));
      });
    }

    function renderEmpty(message) {
      results.innerHTML = "";
      const card = document.createElement("article");
      card.className = "panel empty-panel";

      const title = document.createElement("h3");
      title.textContent = "Recommendations will appear here.";

      const body = document.createElement("p");
      body.className = "muted";
      body.textContent = message;

      card.appendChild(title);
      card.appendChild(body);
      results.appendChild(card);
    }

    function renderResults(payload) {
      results.innerHTML = "";

      const scoreEntries = Object.entries(payload.category_scores || {});
      if (!scoreEntries.length) {
        renderRailCategories([]);
        renderEmpty("No category scores were generated.");
        return;
      }

      renderRailCategories(scoreEntries);

      const summaryPanel = document.createElement("article");
      summaryPanel.className = "panel summary-panel";

      const scoreColumn = document.createElement("div");
      const scoreHeader = document.createElement("div");
      scoreHeader.innerHTML = '<span class="kicker">Fit profile</span><h3>Best-fit categories</h3><p class="muted">These scores represent the strongest opportunity directions for the student.</p>';
      scoreColumn.appendChild(scoreHeader);

      const categoryList = document.createElement("div");
      categoryList.className = "category-list";
      const topScore = scoreEntries[0][1];

      scoreEntries.forEach(([category, score]) => {
        const row = document.createElement("div");
        row.className = "category-row";

        const head = document.createElement("div");
        head.className = "category-row-head";

        const label = document.createElement("span");
        label.textContent = formatCategory(category);

        const value = document.createElement("strong");
        value.textContent = score.toFixed(1);

        head.appendChild(label);
        head.appendChild(value);

        const meter = document.createElement("div");
        meter.className = "meter";
        const fill = document.createElement("span");
        fill.style.width = (score / topScore) * 100 + "%";
        meter.appendChild(fill);

        row.appendChild(head);
        row.appendChild(meter);
        categoryList.appendChild(row);
      });

      scoreColumn.appendChild(categoryList);

      const guidanceColumn = document.createElement("div");
      const guidanceHeader = document.createElement("div");
      guidanceHeader.innerHTML = '<span class="kicker">Direction</span><h3>What to explore first</h3>';
      guidanceColumn.appendChild(guidanceHeader);

      const guidanceCopy = document.createElement("div");
      (payload.guidance || []).forEach((line) => {
        const paragraph = document.createElement("p");
        paragraph.className = "muted";
        paragraph.style.marginTop = "10px";
        paragraph.textContent = line;
        guidanceCopy.appendChild(paragraph);
      });

      const guidanceTags = document.createElement("div");
      guidanceTags.className = "pill-row";
      scoreEntries.slice(0, 3).forEach(([category]) => {
        guidanceTags.appendChild(createTag(formatCategory(category)));
      });

      guidanceColumn.appendChild(guidanceCopy);
      guidanceColumn.appendChild(guidanceTags);

      summaryPanel.appendChild(scoreColumn);
      summaryPanel.appendChild(guidanceColumn);
      results.appendChild(summaryPanel);

      const matchesWrap = document.createElement("div");
      matchesWrap.className = "results-grid";

      const matches = payload.matches || [];
      if (!matches.length) {
        const empty = document.createElement("article");
        empty.className = "panel empty-panel";

        const title = document.createElement("h3");
        title.textContent = "The fit model is ready, but the dataset is thin.";

        const body = document.createElement("p");
        body.className = "muted";
        body.textContent = "Run the Drexel crawler or load a reviewed opportunity file to populate match cards here.";

        empty.appendChild(title);
        empty.appendChild(body);
        matchesWrap.appendChild(empty);
      } else {
        matches.forEach((match) => {
          const opportunity = match.opportunity;
          const card = document.createElement("article");
          card.className = "panel match-card";

          const head = document.createElement("div");
          head.className = "match-head";

          const titleWrap = document.createElement("div");
          const title = document.createElement("h3");
          title.textContent = opportunity.title;
          const summary = document.createElement("p");
          summary.className = "muted";
          summary.textContent = opportunity.summary;
          titleWrap.appendChild(title);
          titleWrap.appendChild(summary);

          const score = document.createElement("span");
          score.className = "match-score";
          score.textContent = "Match " + match.score.toFixed(1);

          head.appendChild(titleWrap);
          head.appendChild(score);

          const tags = document.createElement("div");
          tags.className = "pill-row";
          (opportunity.categories || []).forEach((category) => {
            tags.appendChild(createTag(formatCategory(category), "rail-tag"));
          });
          if (opportunity.paid) {
            tags.appendChild(createTag("Paid", "rail-tag"));
          }
          if (opportunity.international) {
            tags.appendChild(createTag("International", "rail-tag"));
          }

          const reasons = document.createElement("div");
          (match.reasons || []).forEach((reason) => {
            const paragraph = document.createElement("p");
            paragraph.className = "muted";
            paragraph.textContent = reason;
            reasons.appendChild(paragraph);
          });

          card.appendChild(head);
          card.appendChild(tags);
          card.appendChild(reasons);

          if (opportunity.url && !opportunity.url.startsWith("demo://")) {
            const link = document.createElement("a");
            link.className = "match-link";
            link.href = opportunity.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "Open opportunity";
            card.appendChild(link);
          }

          matchesWrap.appendChild(card);
        });
      }

      results.appendChild(matchesWrap);
    }

    async function loadDatasetStatus() {
      const payload = await fetchJson("/api/dataset");
      const modeText = payload.mode === "live" ? "Live crawl data" : "Demo seed data";
      const tone = payload.mode === "live" ? "live" : "demo";

      datasetMode.textContent = modeText;
      datasetCount.textContent = payload.count + " opportunities loaded from " + payload.path;
      metricDataMode.textContent = payload.mode === "live" ? "Live" : "Demo";
      metricOpportunityCount.textContent = String(payload.count);

      datasetMode.className = "status-badge";
      datasetMode.dataset.tone = tone;
    }

    async function loadCategories() {
      const categories = await fetchJson("/api/categories");
      categoryLabels = {};
      categories.forEach((category) => {
        categoryLabels[category.id] = category.label;
      });
    }

    async function loadQuestions() {
      const questions = await fetchJson("/api/questions");
      renderQuestions(questions);
    }

    form.addEventListener("change", () => {
      updateSelectionState();
      updateProgress();
    });

    submitButton.addEventListener("click", async () => {
      try {
        const answers = collectAnswers();
        const payload = await fetchJson("/api/recommendations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers })
        });
        setStatus("Recommendations ready", "ready");
        renderResults(payload);
      } catch (error) {
        setStatus("Needs attention", "error");
        renderEmpty(error.message.replaceAll('"', ""));
      }
    });

    resetButton.addEventListener("click", () => {
      form.reset();
      updateSelectionState();
      updateProgress();
      setStatus("Waiting for answers", "idle");
      renderRailCategories([]);
      renderEmpty("Complete the assessment to reveal category fit and ranked opportunities.");
    });

    Promise.all([loadDatasetStatus(), loadCategories(), loadQuestions()])
      .then(() => {
        setStatus("Waiting for answers", "idle");
        renderEmpty("Complete the assessment to reveal category fit and ranked opportunities.");
      })
      .catch((error) => {
        setStatus("Needs attention", "error");
        renderEmpty(error.message);
      });
  </script>
</body>
</html>
"""
