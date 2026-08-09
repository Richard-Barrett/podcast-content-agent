from __future__ import annotations

import argparse
from pathlib import Path

from .agent import PodcastAgent
from .input import discover_input_files
from .llm import LLMClient
from .logger import configure_logger, log_event
from .render import write_json, write_markdown


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seekr FDE podcast content agent")
    p.add_argument(
        "--input",
        default="data/input",
        help="Input .json/.txt file or directory",
    )
    p.add_argument("--output", default="outputs", help="Output directory")
    p.add_argument("--kb", default="kb/facts.json", help="Local knowledge-base JSON")
    p.add_argument("--logs", default="logs", help="Log directory")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logger = configure_logger(Path(args.logs))
    agent = PodcastAgent(Path(args.kb), logger, LLMClient())
    source = Path(args.input)
    files = discover_input_files(source)
    if not files:
        raise SystemExit(f"No .json or .txt inputs found at {source}")

    log_event(logger, "batch_started", files=[str(x) for x in files])
    for file in files:
        result = agent.run_file(file)
        jp = write_json(result, Path(args.output))
        mp = write_markdown(result, Path(args.output))
        log_event(
            logger,
            "outputs_written",
            episode_id=result.episode_id,
            json=str(jp),
            markdown=str(mp),
        )
    log_event(logger, "batch_completed", count=len(files))


if __name__ == "__main__":
    main()
