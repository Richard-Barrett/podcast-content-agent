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


def test_agent_falls_back_when_llm_summary_has_wrong_length(tmp_path):
    logger = configure_logger(tmp_path / "logs")
    agent = PodcastAgent(
        Path("kb/facts.json"),
        logger,
        llm=ShortSummaryLLM(),
    )

    result = agent.run_file(Path("data/input/ep002_ai_healthcare.json"))

    assert 200 <= len(result.summary.split()) <= 300
