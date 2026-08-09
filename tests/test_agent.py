import json
from pathlib import Path
from types import SimpleNamespace

from app.agent import PodcastAgent
from app.llm import LLMClient, LLMConfig
from app.logger import configure_logger


def test_agent_produces_required_sections(tmp_path):
    logger = configure_logger(tmp_path / "logs")
    llm = LLMClient(LLMConfig(provider="heuristic"))
    agent = PodcastAgent(Path("kb/facts.json"), logger, llm=llm)
    result = agent.run_file(Path("data/input/ep002_ai_healthcare.json"))
    assert 5 == len(result.top_takeaways)
    assert 200 <= len(result.summary.split()) <= 300
    assert result.notable_quotes
    assert result.topics
    assert result.fact_checks


class ShortSummaryLLM:
    enabled = True
    config = SimpleNamespace(provider="test", model="short-summary")

    @staticmethod
    def complete_json(system: str, user: str) -> dict:
        return {
            "summary": "Too short.",
            "top_takeaways": ["takeaway"] * 5,
            "notable_quotes": [],
            "topics": [],
            "claims": [],
        }


class FabricatedQuoteLLM:
    enabled = True
    config = SimpleNamespace(provider="test", model="fabricated-quote")

    @staticmethod
    def complete_json(system: str, user: str) -> dict:
        return {
            "summary": " ".join(["summary"] * 200),
            "top_takeaways": ["takeaway"] * 5,
            "notable_quotes": [
                {
                    "timestamp": "00:00",
                    "speaker": "Invented speaker",
                    "text": "This quote is not in the transcript.",
                }
            ],
            "topics": ["#Test"],
            "claims": [],
        }


def test_agent_falls_back_when_llm_summary_has_wrong_length(tmp_path):
    logger = configure_logger(tmp_path / "logs")
    agent = PodcastAgent(
        Path("kb/facts.json"),
        logger,
        llm=ShortSummaryLLM(),
    )

    result = agent.run_file(Path("data/input/ep002_ai_healthcare.json"))

    assert 200 <= len(result.summary.split()) <= 300


def test_agent_falls_back_when_llm_quote_is_not_verbatim(tmp_path):
    logger = configure_logger(tmp_path / "logs")
    agent = PodcastAgent(
        Path("kb/facts.json"),
        logger,
        llm=FabricatedQuoteLLM(),
    )

    result = agent.run_file(Path("data/input/ep002_ai_healthcare.json"))

    assert result.summary != " ".join(["summary"] * 200)
    assert all(quote.speaker != "Invented speaker" for quote in result.notable_quotes)


def test_agent_processes_timestamped_text_input(tmp_path):
    source = json.loads(
        Path("data/input/ep002_ai_healthcare.json").read_text(encoding="utf-8")
    )
    transcript_lines = [
        f"[{turn['timestamp']}] {turn['speaker']}: {turn['text']}"
        for turn in source["transcript"]
    ]
    text_input = tmp_path / "healthcare.txt"
    text_input.write_text(
        "\n".join(
            [
                "Episode ID: txt-healthcare",
                f"Title: {source['title']}",
                f"Host: {source['host']}",
                f"Guests: {', '.join(source['guests'])}",
                "",
                *transcript_lines,
            ]
        ),
        encoding="utf-8",
    )
    logger = configure_logger(tmp_path / "logs")
    llm = LLMClient(LLMConfig(provider="heuristic"))
    agent = PodcastAgent(Path("kb/facts.json"), logger, llm=llm)

    result = agent.run_file(text_input)

    assert result.episode_id == "txt-healthcare"
    assert 200 <= len(result.summary.split()) <= 300
    assert len(result.top_takeaways) == 5
    assert result.notable_quotes
