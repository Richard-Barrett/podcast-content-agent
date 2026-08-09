from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Quote:
    timestamp: str
    speaker: str
    text: str


@dataclass
class Claim:
    claim: str
    timestamp: str
    speaker: str


@dataclass
class Verification:
    claim: str
    status: str
    verification: str
    confidence: float
    source: str


@dataclass
class EpisodeAnalysis:
    episode_id: str
    title: str
    summary: str
    top_takeaways: list[str]
    notable_quotes: list[Quote]
    topics: list[str]
    fact_checks: list[Verification]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
