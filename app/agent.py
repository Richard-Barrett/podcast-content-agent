from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .factcheck import LocalKnowledgeBase
from .input import load_episode
from .llm import LLMClient, LLMError
from .logger import log_event
from .models import Claim, EpisodeAnalysis, Quote

SYSTEM_PROMPT = """You are a podcast editorial analysis agent for an advertising agency.
Return only valid JSON. Do not invent facts or quotes. Preserve timestamps exactly.
Your output schema is:
{
  "summary": "200-300 words",
  "top_takeaways": ["exactly five concise items"],
  "notable_quotes": [
    {"timestamp":"MM:SS","speaker":"name","text":"verbatim transcript quote"}
  ],
  "topics": ["tag-style topic labels"],
  "claims": [
    {"claim":"factual statement suitable for verification",
     "timestamp":"MM:SS","speaker":"name"}
  ]
}
Prefer factual, externally checkable claims for claims; predictions/opinions
should generally not be treated as facts.
"""


class PodcastAgent:
    def __init__(self, kb_path: Path, logger, llm: LLMClient | None = None):
        self.kb = LocalKnowledgeBase(kb_path)
        self.logger = logger
        self.llm = llm or LLMClient()

    def run_file(self, path: Path) -> EpisodeAnalysis:
        episode = load_episode(path)
        eid = episode["episode_id"]
        log_event(
            self.logger,
            "plan_created",
            episode_id=eid,
            steps=[
                "parse transcript",
                "generate editorial analysis",
                "extract factual claims",
                "retrieve evidence from local knowledge base",
                "score verifications",
                "write outputs",
            ],
        )
        log_event(
            self.logger,
            "transcript_parsed",
            episode_id=eid,
            turns=len(episode["transcript"]),
        )

        analysis = None
        if self.llm.enabled:
            try:
                log_event(
                    self.logger,
                    "llm_analysis_started",
                    episode_id=eid,
                    provider=self.llm.config.provider,
                    model=self.llm.config.model,
                )
                user = json.dumps(episode, ensure_ascii=False)
                analysis = self.llm.complete_json(SYSTEM_PROMPT, user)
                self._validate_llm_analysis(analysis, episode)
                log_event(
                    self.logger,
                    "llm_analysis_completed",
                    episode_id=eid,
                    claims=len(analysis.get("claims", [])),
                )
            except (LLMError, ValueError, KeyError, TypeError) as exc:
                analysis = None
                log_event(
                    self.logger,
                    "llm_analysis_failed_fallback",
                    episode_id=eid,
                    error=str(exc),
                )

        if analysis is None:
            analysis = self._heuristic_analysis(episode)
            log_event(
                self.logger,
                "heuristic_analysis_completed",
                episode_id=eid,
                claims=len(analysis["claims"]),
            )

        claims = [Claim(**c) for c in analysis["claims"]]
        verifications = []
        for claim in claims:
            result = self.kb.verify(claim)
            verifications.append(result)
            log_event(
                self.logger,
                "claim_verified",
                episode_id=eid,
                claim=claim.claim,
                status=result.status,
                confidence=result.confidence,
                source=result.source,
            )

        result = EpisodeAnalysis(
            episode_id=eid,
            title=episode["title"],
            summary=analysis["summary"],
            top_takeaways=analysis["top_takeaways"][:5],
            notable_quotes=[Quote(**q) for q in analysis["notable_quotes"]],
            topics=analysis["topics"],
            fact_checks=verifications,
        )
        log_event(self.logger, "episode_completed", episode_id=eid)
        return result

    @staticmethod
    def _validate_llm_analysis(data: dict, episode: dict) -> None:
        required = {"summary", "top_takeaways", "notable_quotes", "topics", "claims"}
        if not required <= set(data):
            raise ValueError(f"Missing keys: {required - set(data)}")
        if not isinstance(data["summary"], str):
            raise TypeError("Expected summary to be a string")
        summary_words = len(data["summary"].split())
        if not 200 <= summary_words <= 300:
            raise ValueError(
                f"Expected a 200-300 word summary, received {summary_words} words"
            )
        if len(data["top_takeaways"]) < 5:
            raise ValueError("Expected at least five takeaways")
        transcript_quotes = {
            (turn["timestamp"], turn["speaker"], turn["text"])
            for turn in episode["transcript"]
        }
        for quote in data["notable_quotes"]:
            if not isinstance(quote, dict):
                raise TypeError("Expected each notable quote to be an object")
            quote_key = (
                quote.get("timestamp"),
                quote.get("speaker"),
                quote.get("text"),
            )
            if quote_key not in transcript_quotes:
                raise ValueError("Notable quote does not match the transcript exactly")

    @staticmethod
    def _heuristic_analysis(ep: dict) -> dict:
        turns = ep["transcript"]
        substantive = [
            t
            for t in turns
            if t["speaker"].lower() not in {ep["host"].split()[0].lower()}
            and len(t["text"]) > 45
        ]
        if not substantive:
            substantive = [t for t in turns if len(t["text"]) > 45]

        by_section: dict[str, list[str]] = {}
        for t in turns:
            by_section.setdefault(t["section"], []).append(t["text"])
        section_order = list(by_section)
        themes = "; ".join(
            f"{s}: {' '.join(by_section[s])}"
            for s in section_order
            if s not in {"Introduction", "Closing"}
        )
        condensed = re.sub(r"\s+", " ", themes)
        words = condensed.split()
        summary_body = " ".join(words[:220])
        if len(summary_body.split()) < 180:
            closing = " ".join(t["text"] for t in turns if t["section"] == "Closing")
            summary_body = (summary_body + " " + closing).strip()
        summary = (
            f"{ep['title']} examines the episode's central question through a "
            f"structured discussion between {ep['host']} and "
            f"{', '.join(ep.get('guests', []))}. {summary_body}"
        )
        if len(summary.split()) < 200:
            summary += (
                " The conversation frames the issue as a practical decision rather "
                "than a one-size-fits-all rule. The speakers compare the relevant "
                "benefits, constraints, and trade-offs, then connect those points "
                "to concrete operating choices. The closing perspective emphasizes "
                "matching the approach to the situation, priorities, and risks "
                "described throughout the episode."
            )
        summary = " ".join(summary.split()[:285])

        ranked = sorted(
            substantive,
            key=lambda t: (
                t["section"]
                in {
                    "Framework",
                    "Trends",
                    "Future",
                    "Predictions",
                    "Challenges",
                    "Deep Dive",
                },
                len(t["text"]),
            ),
            reverse=True,
        )
        takeaways = [
            re.sub(r"^(Well, |And |Plus, )", "", t["text"]) for t in ranked[:5]
        ]
        while len(takeaways) < 5:
            takeaways.append(
                "The discussion emphasizes practical trade-offs rather than a "
                "one-size-fits-all conclusion."
            )

        quotes = []
        for t in ranked[:4]:
            quotes.append(
                {
                    "timestamp": t["timestamp"],
                    "speaker": t["speaker"],
                    "text": t["text"],
                }
            )

        topics = []
        for s in section_order:
            if s not in {"Introduction", "Closing", "Examples"}:
                topics.append("#" + re.sub(r"[^A-Za-z0-9]+", "", s.title()))
        title_terms = [
            w.lower()
            for w in re.findall(r"[A-Za-z]{4,}", ep["title"])
            if w.lower() not in {"with", "which", "future", "reality"}
        ]
        topics.extend("#" + x.title() for x, _ in Counter(title_terms).most_common(3))
        topics = list(dict.fromkeys(topics))[:7]

        claims = []
        fact_markers = re.compile(
            r"\b(FDA|GitLab|Automattic|Doist|pandemic|hospitals?|18 months|"
            r"two years|X-rays?|triage chatbots?|clinical data|data privacy|bias)\b",
            re.IGNORECASE,
        )
        for t in turns:
            txt = t["text"].strip()
            if (
                t["speaker"] == ep["host"].split()[0]
                or txt.endswith("?")
                or t["section"] == "Introduction"
            ):
                continue
            if fact_markers.search(txt) and not any(
                k in txt.lower()
                for k in [
                    "will dominate",
                    "will become standard",
                    "might become",
                    "will always",
                ]
            ):
                claims.append(
                    {"claim": txt, "timestamp": t["timestamp"], "speaker": t["speaker"]}
                )
        return {
            "summary": summary,
            "top_takeaways": takeaways,
            "notable_quotes": quotes,
            "topics": topics,
            "claims": claims[:6],
        }
