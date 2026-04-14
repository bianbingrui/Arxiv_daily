from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from .config import load_settings
from .pipeline import build_digest, write_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a daily personalized arXiv digest.")
    parser.add_argument("--days-back", type=int, default=1, help="Only include papers updated in the last N days.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of digest items to keep.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    settings = load_settings(project_root)

    try:
        items = build_digest(settings, days_back=args.days_back, limit=args.limit)
        generated_at = datetime.now(timezone.utc)
        markdown_path, json_path = write_outputs(
            project_root=project_root,
            settings=settings,
            items=items,
            generated_at=generated_at,
            days_back=args.days_back,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote markdown digest: {markdown_path}")
    print(f"Wrote JSON digest: {json_path}")
    print(f"Digest items: {len(items)}")
    if not settings.openai_api_key:
        print("OPENAI_API_KEY not set, so the digest used raw abstracts without AI analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
