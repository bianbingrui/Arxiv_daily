# arXiv Daily

Small Python project for a daily arXiv digest focused on domains like Optimization and Computer Science.

It does four things:

1. Queries the arXiv API for recent papers in selected categories.
2. Filters to papers updated in the last N days.
3. Uses the OpenAI API to summarize and score each paper against your interests.
4. Writes a Markdown digest you can skim quickly.

## Quick start

```bash
cd /Users/bianbingrui/Documents/Arxiv_daily
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Then add your API key to `.env`.

## Run

```bash
source .venv/bin/activate
arxiv-daily --days-back 1 --limit 15
```

This writes a digest to `outputs/`, for example:

```text
outputs/digest_2026-04-12.md
```

## Example categories

- `math.OC`: Optimization and Control
- `cs.LG`: Machine Learning
- `cs.AI`: Artificial Intelligence
- `cs.ET`: Emerging Technologies
- `cs.RO`: Robotics
- `stat.ML`: Statistics / ML

arXiv category reference:
https://arxiv.org/category_taxonomy

## Daily automation

Use `cron` on macOS/Linux:

```cron
0 8 * * * cd /Users/bianbingrui/Documents/Arxiv_daily && /bin/zsh -lc 'source .venv/bin/activate && arxiv-daily --days-back 1 --limit 20'
```

That runs every day at 8:00 AM local time.

## Notes

- If `OPENAI_API_KEY` is missing, the tool still produces a raw digest without AI summaries.
- The implementation uses only Python's standard library, so it avoids SDK/version friction.
- The OpenAI model is configurable with `OPENAI_MODEL`.
