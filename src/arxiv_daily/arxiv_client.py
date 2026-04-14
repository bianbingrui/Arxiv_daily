from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .http_utils import build_ssl_context


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclass(slots=True)
class Paper:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    published_at: datetime
    updated_at: datetime
    pdf_url: str
    abs_url: str


def build_category_query(categories: Iterable[str]) -> str:
    parts = [f"cat:{category}" for category in categories]
    return " OR ".join(parts)


def _parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def fetch_recent_papers(categories: list[str], max_results: int) -> list[Paper]:
    params = {
        "search_query": build_category_query(categories),
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": max_results,
    }
    url = f"{ARXIV_API_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "arxiv-daily/0.1 (academic paper digest project)",
        },
    )
    with urlopen(request, timeout=30, context=build_ssl_context()) as response:
        payload = response.read()
    return parse_atom_feed(payload)


def parse_atom_feed(payload: bytes) -> list[Paper]:
    root = ET.fromstring(payload)
    papers: list[Paper] = []

    for entry in root.findall("atom:entry", ATOM_NS):
        paper_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM_NS).split())
        summary = " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM_NS).split())
        published = _parse_datetime(
            entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        )
        updated = _parse_datetime(entry.findtext("atom:updated", default="", namespaces=ATOM_NS))
        authors = [
            author.findtext("atom:name", default="", namespaces=ATOM_NS)
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        categories = [category.attrib.get("term", "") for category in entry.findall("atom:category", ATOM_NS)]
        pdf_url = ""
        abs_url = paper_id
        for link in entry.findall("atom:link", ATOM_NS):
            href = link.attrib.get("href", "")
            title_attr = link.attrib.get("title", "")
            link_type = link.attrib.get("type", "")
            if title_attr == "pdf" or link_type == "application/pdf":
                pdf_url = href
                break

        papers.append(
            Paper(
                paper_id=paper_id.rsplit("/", 1)[-1],
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                published_at=published,
                updated_at=updated,
                pdf_url=pdf_url,
                abs_url=abs_url,
            )
        )
    return papers


def filter_papers_updated_within(papers: list[Paper], days_back: int) -> list[Paper]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    return [paper for paper in papers if paper.updated_at >= cutoff]
