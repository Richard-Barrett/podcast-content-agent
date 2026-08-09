from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Claim, Verification


def _tokens(text: str) -> set[str]:
    stop = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "in",
        "for",
        "is",
        "are",
        "it",
        "that",
        "this",
        "with",
        "on",
        "be",
        "will",
    }
    return {
        x
        for x in re.findall(r"[a-z0-9]+", text.lower())
        if len(x) > 2 and x not in stop
    }


class LocalKnowledgeBase:
    """Transparent lexical retrieval over a small JSON knowledge base."""

    def __init__(self, path: Path):
        self.entries = json.loads(path.read_text(encoding="utf-8"))["facts"]

    def verify(self, claim: Claim) -> Verification:
        claim_tokens = _tokens(claim.claim)
        best, score = None, 0.0
        for entry in self.entries:
            fact_tokens = _tokens(
                entry["fact"] + " " + " ".join(entry.get("aliases", []))
            )
            if not claim_tokens or not fact_tokens:
                continue
            intersection = len(claim_tokens & fact_tokens)
            jaccard = intersection / max(1, len(claim_tokens | fact_tokens))
            containment = intersection / max(
                1, min(len(claim_tokens), len(fact_tokens))
            )
            overlap = max(jaccard, containment * 0.8)
            if overlap > score:
                best, score = entry, overlap

        if best and score >= 0.28:
            confidence = round(
                min(
                    0.98,
                    float(best.get("confidence", 0.85)) * (0.78 + min(score, 0.20)),
                ),
                2,
            )
            return Verification(
                claim=claim.claim,
                status=best["status"],
                verification=best["verification"],
                confidence=confidence,
                source=best["source"],
            )
        return Verification(
            claim=claim.claim,
            status="❓ Unverifiable",
            verification=(
                "No sufficiently relevant fact was retrieved from the local "
                "knowledge base."
            ),
            confidence=0.35,
            source="local-kb:no-match",
        )
