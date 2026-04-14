from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from .arxiv_client import Paper, fetch_recent_papers, filter_papers_updated_within
from .config import Settings
from .openai_client import PaperAnalysis, analyze_paper


@dataclass(slots=True)
class DigestItem:
    paper: Paper
    analysis: PaperAnalysis | None


def simple_keyword_score(paper: Paper, interest_profile: str) -> int:
    haystack = f"{paper.title} {paper.summary}".lower()
    keywords = {
        token.strip(" ,.")
        for token in interest_profile.lower().split()
        if len(token.strip(" ,.")) >= 4
    }
    matches = sum(1 for keyword in keywords if keyword in haystack)
    return max(1, min(10, 3 + matches))


def build_digest(settings: Settings, days_back: int, limit: int) -> list[DigestItem]:
    papers = fetch_recent_papers(settings.arxiv_categories, settings.arxiv_max_results)
    recent = filter_papers_updated_within(papers, days_back)[:limit]

    digest_items: list[DigestItem] = []
    for paper in recent:
        analysis = None
        if settings.openai_api_key:
            analysis = analyze_paper(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                paper=paper,
                interest_profile=settings.interest_profile,
            )
        digest_items.append(DigestItem(paper=paper, analysis=analysis))

    digest_items.sort(
        key=lambda item: (
            item.analysis.score if item.analysis else simple_keyword_score(item.paper, settings.interest_profile),
            item.paper.updated_at,
        ),
        reverse=True,
    )
    return digest_items


def render_markdown(
    items: list[DigestItem],
    settings: Settings,
    generated_at: datetime,
    days_back: int,
) -> str:
    lines = [
        "# arXiv Daily Digest",
        "",
        f"- Generated at: {generated_at.isoformat()}",
        f"- Categories: {', '.join(settings.arxiv_categories)}",
        f"- Window: last {days_back} day(s)",
        f"- Interest profile: {settings.interest_profile}",
        "",
    ]

    if not items:
        lines.extend(
            [
                "No papers matched the current window.",
                "",
            ]
        )
        return "\n".join(lines)

    for index, item in enumerate(items, start=1):
        paper = item.paper
        analysis = item.analysis
        score = analysis.score if analysis else simple_keyword_score(paper, settings.interest_profile)
        recommended = analysis.recommended_for_you if analysis else score >= 6
        lines.extend(
            [
                f"## {index}. {paper.title}",
                "",
                f"- Score: {score}/10",
                f"- Recommended: {'Yes' if recommended else 'No'}",
                f"- Authors: {', '.join(paper.authors)}",
                f"- Categories: {', '.join(paper.categories)}",
                f"- Published: {paper.published_at.date().isoformat()}",
                f"- Updated: {paper.updated_at.date().isoformat()}",
                f"- Abstract page: {paper.abs_url}",
                f"- PDF: {paper.pdf_url or 'N/A'}",
                "",
                "### Summary",
                "",
                analysis.summary if analysis else paper.summary,
                "",
                "### Why It May Matter",
                "",
                (
                    analysis.why_interesting
                    if analysis
                    else "No OpenAI analysis was run. Add OPENAI_API_KEY to enable personalized screening."
                ),
                "",
            ]
        )

    return "\n".join(lines)


def render_json(items: list[DigestItem]) -> str:
    payload = []
    for item in items:
        paper = item.paper
        analysis = item.analysis
        payload.append(
            {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "authors": paper.authors,
                "categories": paper.categories,
                "published_at": paper.published_at.isoformat(),
                "updated_at": paper.updated_at.isoformat(),
                "abstract_url": paper.abs_url,
                "pdf_url": paper.pdf_url,
                "abstract": paper.summary,
                "analysis": (
                    {
                        "score": analysis.score,
                        "recommended_for_you": analysis.recommended_for_you,
                        "summary": analysis.summary,
                        "why_interesting": analysis.why_interesting,
                    }
                    if analysis
                    else None
                ),
            }
        )
    return json.dumps(payload, indent=2)


def write_outputs(
    project_root: Path,
    settings: Settings,
    items: list[DigestItem],
    generated_at: datetime,
    days_back: int,
) -> tuple[Path, Path]:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = generated_at.date().isoformat()
    markdown_path = settings.output_dir / f"digest_{stamp}.md"
    json_path = settings.output_dir / f"digest_{stamp}.json"

    markdown_path.write_text(
        render_markdown(items, settings, generated_at, days_back),
        encoding="utf-8",
    )
    json_path.write_text(render_json(items), encoding="utf-8")
    return markdown_path, json_path
