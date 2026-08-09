from __future__ import annotations

import json
from pathlib import Path

from .models import EpisodeAnalysis


def write_json(result: EpisodeAnalysis, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result.episode_id}_analysis.json"
    path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


def write_markdown(result: EpisodeAnalysis, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result.episode_id}_analysis.md"
    lines = [
        f"# {result.title}",
        "",
        "## Summary",
        "",
        result.summary,
        "",
        "## Top 5 Takeaways",
        "",
    ]
    lines.extend(f"- {x}" for x in result.top_takeaways)
    lines += ["", "## Notable Quotes", ""]
    lines.extend(
        f"> **{q.timestamp} — {q.speaker}:** {q.text}" for q in result.notable_quotes
    )
    lines += [
        "",
        "## Topics",
        "",
        " ".join(result.topics),
        "",
        "## Fact Check",
        "",
        "| Claim | Status | Verification | Confidence | Source |",
        "|---|---|---|---:|---|",
    ]

    def clean(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    for fact in result.fact_checks:
        lines.append(
            f"| {clean(fact.claim)} | {clean(fact.status)} | "
            f"{clean(fact.verification)} | {fact.confidence:.2f} | "
            f"{clean(fact.source)} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
