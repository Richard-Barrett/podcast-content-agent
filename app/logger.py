from __future__ import annotations

import json
import logging
from pathlib import Path


def configure_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("seekr_agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    fh = logging.FileHandler(log_dir / "agent.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def log_event(logger: logging.Logger, event: str, **fields: object) -> None:
    # These are execution-plan/status events, not hidden chain-of-thought.
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False))
