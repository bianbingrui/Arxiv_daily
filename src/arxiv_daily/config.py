from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    arxiv_categories: list[str]
    arxiv_max_results: int
    interest_profile: str
    output_dir: Path


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def load_settings(project_root: Path) -> Settings:
    load_env_file(project_root / ".env")

    categories = os.getenv("ARXIV_CATEGORIES", "cs.AI,cs.LG,math.OC")
    output_dir = project_root / "outputs"

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        arxiv_categories=[item.strip() for item in categories.split(",") if item.strip()],
        arxiv_max_results=int(os.getenv("ARXIV_MAX_RESULTS", "20")),
        interest_profile=os.getenv(
            "INTEREST_PROFILE",
            "Optimization, AI, machine learning, reinforcement learning, "
            "decision science, and practically useful research.",
        ),
        output_dir=output_dir,
    )
