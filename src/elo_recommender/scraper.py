import argparse
import re
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

from elo_recommender.models import Opportunity
from elo_recommender.storage import DEFAULT_LIVE_DATA_PATH, save_opportunities
from elo_recommender.taxonomy import categorize_text, looks_like_opportunity, ranked_categories


USER_AGENT = "NHPS-ELO-Recommender/0.1"


@dataclass
class CrawlConfig:
    seed_urls: List[str] = field(default_factory=lambda: ["https://drexel.edu/"])
    allowed_domains: List[str] = field(default_factory=lambda: ["drexel.edu"])
    max_pages: int = 150
    max_depth: int = 3
    delay_seconds: float = 0.25
    timeout_seconds: float = 15.0
    output_path: str = str(DEFAULT_LIVE_DATA_PATH)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    cleaned = parsed._replace(fragment="", query=parsed.query)
    normalized = urlunparse(cleaned)
    return normalized.rstrip("/")


def is_allowed_domain(url: str, allowed_domains: Iterable[str]) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return any(hostname == domain or hostname.endswith("." + domain) for domain in allowed_domains)


def build_robot_parser(url: str) -> RobotFileParser:
    parsed = urlparse(url)
    robots_url = "{0}://{1}/robots.txt".format(parsed.scheme, parsed.netloc)
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return parser
    return parser


def extract_text_block(raw_text: str, max_length: int = 280) -> str:
    cleaned = re.sub(r"\s+", " ", raw_text or "").strip()
    return cleaned[:max_length]


def infer_booleans(text: str) -> Tuple[Optional[bool], Optional[bool]]:
    lowered = (text or "").lower()
    paid = None
    international = None

    if any(keyword in lowered for keyword in ["paid", "stipend", "salary", "compensation"]):
        paid = True
    if any(keyword in lowered for keyword in ["international", "study abroad", "global", "exchange"]):
        international = True

    return paid, international


def candidate_id(title: str, url: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (title or url).lower()).strip("-")
    return base[:80] or "opportunity"


def make_opportunity(
    title: str,
    url: str,
    summary: str,
    source_page: str,
    categories: List[str],
    confidence: float,
) -> Opportunity:
    paid, international = infer_booleans(" ".join([title, summary]))
    category_summary = " ".join(categories)
    tags = [category for category in categories]
    return Opportunity(
        id=candidate_id(title, url),
        title=title.strip() or "Untitled opportunity",
        url=url,
        summary=summary.strip(),
        categories=categories,
        tags=tags,
        source_page=source_page,
        audience=[],
        format="web",
        paid=paid,
        international=international,
        location="",
        commitment="",
        scraped_at=datetime.utcnow().isoformat() + "Z",
        confidence=confidence + (0.1 if category_summary else 0.0),
        source_type="crawl",
    )


def extract_links(soup, page_url: str, allowed_domains: Iterable[str]) -> List[str]:
    discovered = []
    for anchor in soup.find_all("a", href=True):
        absolute_url = normalize_url(urljoin(page_url, anchor["href"]))
        if absolute_url.startswith("mailto:") or absolute_url.startswith("tel:"):
            continue
        if not absolute_url.startswith("http"):
            continue
        if is_allowed_domain(absolute_url, allowed_domains):
            discovered.append(absolute_url)
    return discovered


def extract_page_opportunities(soup, page_url: str) -> List[Opportunity]:
    opportunities = []
    seen = set()

    page_title = extract_text_block(soup.title.get_text(" ", strip=True) if soup.title else "")
    meta_description = ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    if description_tag and description_tag.get("content"):
        meta_description = extract_text_block(description_tag["content"], max_length=360)

    page_text = extract_text_block(soup.get_text(" ", strip=True), max_length=2500)
    page_categories = categorize_text(" ".join([page_title, meta_description, page_text]))
    combined_text = " ".join([page_title, meta_description, page_text])

    if page_categories and looks_like_opportunity(combined_text):
        page_level = make_opportunity(
            title=page_title,
            url=page_url,
            summary=meta_description or page_text[:240],
            source_page=page_url,
            categories=page_categories,
            confidence=0.5,
        )
        seen.add((page_level.title.lower(), page_level.url))
        opportunities.append(page_level)

    for anchor in soup.find_all("a", href=True):
        link_text = extract_text_block(anchor.get_text(" ", strip=True), max_length=180)
        link_url = normalize_url(urljoin(page_url, anchor["href"]))
        context_text = extract_text_block(anchor.parent.get_text(" ", strip=True), max_length=280)
        candidate_text = " ".join([link_text, context_text, link_url])

        if len(link_text) < 6 or not looks_like_opportunity(candidate_text):
            continue

        categories = categorize_text(candidate_text)
        if not categories:
            ranked = ranked_categories(candidate_text)
            if not ranked:
                continue
            categories = [ranked[0][0]]

        dedupe_key = (link_text.lower(), link_url)
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        opportunities.append(
            make_opportunity(
                title=link_text,
                url=link_url,
                summary=context_text or page_text[:240],
                source_page=page_url,
                categories=categories,
                confidence=0.75,
            )
        )

    return opportunities


def crawl(config: CrawlConfig) -> List[Opportunity]:
    import httpx
    from bs4 import BeautifulSoup

    queue = deque((normalize_url(url), 0) for url in config.seed_urls)
    visited: Set[str] = set()
    robots_by_host: Dict[str, RobotFileParser] = {}
    opportunities: List[Opportunity] = []

    with httpx.Client(
        follow_redirects=True,
        timeout=config.timeout_seconds,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        while queue and len(visited) < config.max_pages:
            current_url, depth = queue.popleft()
            if current_url in visited:
                continue
            if not is_allowed_domain(current_url, config.allowed_domains):
                continue

            hostname = urlparse(current_url).hostname or ""
            robot_parser = robots_by_host.get(hostname)
            if robot_parser is None:
                robot_parser = build_robot_parser(current_url)
                robots_by_host[hostname] = robot_parser

            try:
                can_fetch = robot_parser.can_fetch(USER_AGENT, current_url)
            except Exception:
                can_fetch = True
            if can_fetch is False:
                continue

            try:
                response = client.get(current_url)
                response.raise_for_status()
            except Exception:
                visited.add(current_url)
                continue

            visited.add(current_url)
            soup = BeautifulSoup(response.text, "html.parser")
            opportunities.extend(extract_page_opportunities(soup, current_url))

            if depth < config.max_depth:
                for discovered in extract_links(soup, current_url, config.allowed_domains):
                    if discovered not in visited:
                        queue.append((discovered, depth + 1))

            time.sleep(config.delay_seconds)

    return opportunities


def crawl_and_save(config: CrawlConfig) -> str:
    opportunities = crawl(config)
    output_path = save_opportunities(opportunities, config.output_path)
    return str(output_path)


def parse_args() -> CrawlConfig:
    parser = argparse.ArgumentParser(description="Crawl Drexel pages for ELO opportunities.")
    parser.add_argument("--seed", action="append", dest="seeds", help="Seed URL to start crawling from.")
    parser.add_argument("--domain", action="append", dest="domains", help="Allowed domain suffix.")
    parser.add_argument("--max-pages", type=int, default=150)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--output", default=str(DEFAULT_LIVE_DATA_PATH))
    args = parser.parse_args()

    return CrawlConfig(
        seed_urls=args.seeds or ["https://drexel.edu/"],
        allowed_domains=args.domains or ["drexel.edu"],
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay_seconds=args.delay,
        timeout_seconds=args.timeout,
        output_path=args.output,
    )


def main() -> None:
    config = parse_args()
    output = crawl_and_save(config)
    print("Saved opportunities to {0}".format(output))


if __name__ == "__main__":
    main()
