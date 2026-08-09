from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SUPPORTED_INPUT_SUFFIXES = {".json", ".txt"}
TRANSCRIPT_LINE = re.compile(
    r"^\[(?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)\]\s*"
    r"(?P<speaker>[^:]+):\s*(?P<text>.+)$"
)
METADATA_LINE = re.compile(
    r"^(?P<key>episode[ _-]?id|title|host|guests?)\s*:\s*(?P<value>.+)$",
    re.IGNORECASE,
)


def discover_input_files(source: Path) -> list[Path]:
    if source.is_dir():
        return sorted(
            path
            for path in source.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_SUFFIXES
        )
    if source.is_file() and source.suffix.lower() in SUPPORTED_INPUT_SUFFIXES:
        return [source]
    return []


def load_episode(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        episode = json.loads(path.read_text(encoding="utf-8"))
    elif suffix == ".txt":
        episode = _parse_text_episode(path)
    else:
        supported = ", ".join(sorted(SUPPORTED_INPUT_SUFFIXES))
        raise ValueError(f"Unsupported input format {suffix!r}; expected {supported}")
    return _validate_episode(episode, path)


def _parse_text_episode(path: Path) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    transcript: list[dict[str, str]] = []
    speakers: list[str] = []

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        turn_match = TRANSCRIPT_LINE.fullmatch(line)
        if turn_match:
            turn = turn_match.groupdict()
            speaker = turn["speaker"].strip()
            if speaker not in speakers:
                speakers.append(speaker)
            transcript.append(
                {
                    "timestamp": turn["timestamp"],
                    "speaker": speaker,
                    "section": "Transcript",
                    "text": turn["text"].strip(),
                }
            )
            continue

        metadata_match = METADATA_LINE.fullmatch(line)
        if metadata_match and not transcript:
            key = re.sub(r"[ _-]", "", metadata_match["key"].lower())
            metadata[key] = metadata_match["value"].strip()
            continue

        raise ValueError(
            f"{path}:{line_number}: expected metadata or '[timestamp] Speaker: text'"
        )

    if not transcript:
        raise ValueError(f"{path}: no timestamped transcript lines found")

    host = metadata.get("host", speakers[0])
    guests_value = metadata.get("guest", metadata.get("guests"))
    if guests_value:
        guests = [name.strip() for name in guests_value.split(",") if name.strip()]
    else:
        host_tokens = {host.casefold(), host.split()[0].casefold()}
        guests = [
            speaker for speaker in speakers if speaker.casefold() not in host_tokens
        ]

    return {
        "episode_id": metadata.get("episodeid", path.stem),
        "title": metadata.get("title", _title_from_stem(path.stem)),
        "host": host,
        "guests": guests,
        "transcript": transcript,
    }


def _title_from_stem(stem: str) -> str:
    return re.sub(r"[_-]+", " ", stem).strip().title()


def _validate_episode(episode: object, path: Path) -> dict[str, Any]:
    if not isinstance(episode, dict):
        raise TypeError(f"{path}: episode input must be a JSON object")

    required_strings = ("episode_id", "title", "host")
    for field in required_strings:
        if not isinstance(episode.get(field), str) or not episode[field].strip():
            raise ValueError(f"{path}: {field} must be a non-empty string")

    guests = episode.get("guests")
    if not isinstance(guests, list) or not all(
        isinstance(guest, str) and guest.strip() for guest in guests
    ):
        raise ValueError(f"{path}: guests must be a list of non-empty strings")

    transcript = episode.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        raise ValueError(f"{path}: transcript must be a non-empty list")
    for index, turn in enumerate(transcript):
        if not isinstance(turn, dict):
            raise TypeError(f"{path}: transcript[{index}] must be an object")
        for field in ("timestamp", "speaker", "section", "text"):
            if not isinstance(turn.get(field), str) or not turn[field].strip():
                raise ValueError(
                    f"{path}: transcript[{index}].{field} must be a non-empty string"
                )
    return episode
