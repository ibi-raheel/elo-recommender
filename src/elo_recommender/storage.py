import json
from pathlib import Path
from typing import Iterable, List, Optional

from elo_recommender.models import Opportunity


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DEFAULT_LIVE_DATA_PATH = DATA_DIR / "opportunities.json"
DEFAULT_DEMO_DATA_PATH = DATA_DIR / "opportunities.demo.json"


def resolve_dataset_path(explicit_path: Optional[str] = None) -> Path:
    if explicit_path:
        return Path(explicit_path).expanduser().resolve()

    if DEFAULT_LIVE_DATA_PATH.exists():
        return DEFAULT_LIVE_DATA_PATH

    return DEFAULT_DEMO_DATA_PATH


def dataset_metadata(explicit_path: Optional[str] = None) -> dict:
    path = resolve_dataset_path(explicit_path)
    mode = "live" if path == DEFAULT_LIVE_DATA_PATH and path.exists() else "demo"
    opportunities = load_opportunities(str(path))
    return {
        "path": str(path),
        "mode": mode,
        "count": len(opportunities),
    }


def load_opportunities(path: Optional[str] = None) -> List[Opportunity]:
    target_path = resolve_dataset_path(path)
    if not target_path.exists():
        return []

    payload = json.loads(target_path.read_text(encoding="utf-8"))
    return [Opportunity(**record) for record in payload]


def dedupe_opportunities(opportunities: Iterable[Opportunity]) -> List[Opportunity]:
    seen = set()
    unique = []

    for opportunity in opportunities:
        key = opportunity.url.strip() or opportunity.title.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(opportunity)

    return unique


def save_opportunities(opportunities: Iterable[Opportunity], path: Optional[str] = None) -> Path:
    target_path = resolve_dataset_path(path or str(DEFAULT_LIVE_DATA_PATH))
    target_path.parent.mkdir(parents=True, exist_ok=True)

    unique = dedupe_opportunities(opportunities)
    payload = [opportunity.to_dict() for opportunity in unique]
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target_path
