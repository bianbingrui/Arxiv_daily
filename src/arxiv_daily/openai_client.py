from __future__ import annotations

from dataclasses import dataclass
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

from .arxiv_client import Paper
from .http_utils import build_ssl_context


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(slots=True)
class PaperAnalysis:
    score: int
    why_interesting: str
    summary: str
    recommended_for_you: bool


def build_prompt(paper: Paper, interest_profile: str) -> str:
    return f"""
You are screening newly updated arXiv papers for a researcher.

User interest profile:
{interest_profile}

Return strict JSON with keys:
- score: integer from 1 to 10
- recommended_for_you: boolean
- summary: concise 2-3 sentence summary in plain English
- why_interesting: one concise sentence explaining why this paper may matter for this user's interests

Paper metadata:
Title: {paper.title}
Authors: {", ".join(paper.authors)}
Categories: {", ".join(paper.categories)}
Published: {paper.published_at.isoformat()}
Updated: {paper.updated_at.isoformat()}
Abstract: {paper.summary}
""".strip()


def analyze_paper(
    api_key: str,
    model: str,
    paper: Paper,
    interest_profile: str,
) -> PaperAnalysis:
    payload = {
        "model": model,
        "input": build_prompt(paper, interest_profile),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "paper_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 1, "maximum": 10},
                        "recommended_for_you": {"type": "boolean"},
                        "summary": {"type": "string"},
                        "why_interesting": {"type": "string"},
                    },
                    "required": [
                        "score",
                        "recommended_for_you",
                        "summary",
                        "why_interesting",
                    ],
                    "additionalProperties": False,
                },
            }
        },
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60, context=build_ssl_context()) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error ({exc.code}): {body}") from exc

    content = (
        data.get("output", [{}])[0]
        .get("content", [{}])[0]
        .get("text")
    )
    if not content:
        raise RuntimeError(f"Unexpected OpenAI response shape: {json.dumps(data)[:800]}")

    parsed = json.loads(content)
    return PaperAnalysis(
        score=int(parsed["score"]),
        recommended_for_you=bool(parsed["recommended_for_you"]),
        summary=str(parsed["summary"]).strip(),
        why_interesting=str(parsed["why_interesting"]).strip(),
    )
