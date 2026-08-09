from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_MARKDOWN_SECTIONS = (
    "## Summary",
    "## Top 5 Takeaways",
    "## Notable Quotes",
    "## Topics",
    "## Fact Check",
)
REQUIRED_EPISODE_EVENTS = (
    "plan_created",
    "transcript_parsed",
    "episode_completed",
    "outputs_written",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate podcast-agent deliverables against the assignment contract."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/input"),
        help="Directory containing the source episode JSON files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs"),
        help="Directory containing generated JSON and Markdown analyses.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="Optional agent log to validate for lifecycle events.",
    )
    return parser.parse_args()


def load_json(path: Path, errors: list[str]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"Missing file: {path}")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Could not read valid JSON from {path}: {exc}")
    return None


def require_non_empty_string(
    value: object,
    field: str,
    path: Path,
    errors: list[str],
) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: {field} must be a non-empty string")


def expected_episodes(input_dir: Path, errors: list[str]) -> dict[str, str]:
    episodes: dict[str, str] = {}
    files = sorted(input_dir.glob("*.json")) if input_dir.is_dir() else []
    if not files:
        errors.append(f"No input JSON files found in {input_dir}")
        return episodes

    for path in files:
        episode = load_json(path, errors)
        if not isinstance(episode, dict):
            if episode is not None:
                errors.append(f"{path}: input must be a JSON object")
            continue
        episode_id = episode.get("episode_id")
        title = episode.get("title")
        if not isinstance(episode_id, str) or not episode_id.strip():
            errors.append(f"{path}: episode_id must be a non-empty string")
            continue
        if episode_id in episodes:
            errors.append(f"{path}: duplicate episode_id {episode_id!r}")
            continue
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{path}: title must be a non-empty string")
            continue
        episodes[episode_id] = title
    return episodes


def validate_string_list(
    value: object,
    field: str,
    path: Path,
    errors: list[str],
    *,
    exact_length: int | None = None,
) -> None:
    if not isinstance(value, list):
        errors.append(f"{path}: {field} must be a list")
        return
    if exact_length is not None and len(value) != exact_length:
        errors.append(
            f"{path}: {field} must contain exactly {exact_length} items; "
            f"received {len(value)}"
        )
    if not value:
        errors.append(f"{path}: {field} must not be empty")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}: {field}[{index}] must be a non-empty string")


def validate_quotes(value: object, path: Path, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: notable_quotes must be a non-empty list")
        return
    for index, quote in enumerate(value):
        if not isinstance(quote, dict):
            errors.append(f"{path}: notable_quotes[{index}] must be an object")
            continue
        for field in ("timestamp", "speaker", "text"):
            require_non_empty_string(
                quote.get(field),
                f"notable_quotes[{index}].{field}",
                path,
                errors,
            )


def validate_fact_checks(value: object, path: Path, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: fact_checks must be a non-empty list")
        return
    for index, fact in enumerate(value):
        if not isinstance(fact, dict):
            errors.append(f"{path}: fact_checks[{index}] must be an object")
            continue
        for field in ("claim", "status", "verification", "source"):
            require_non_empty_string(
                fact.get(field),
                f"fact_checks[{index}].{field}",
                path,
                errors,
            )
        confidence = fact.get("confidence")
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0 <= confidence <= 1
        ):
            errors.append(
                f"{path}: fact_checks[{index}].confidence must be between 0 and 1"
            )


def validate_json_output(
    path: Path,
    episode_id: str,
    expected_title: str,
    errors: list[str],
) -> None:
    result = load_json(path, errors)
    if not isinstance(result, dict):
        if result is not None:
            errors.append(f"{path}: output must be a JSON object")
        return

    if result.get("episode_id") != episode_id:
        errors.append(f"{path}: episode_id must equal {episode_id!r}")
    if result.get("title") != expected_title:
        errors.append(f"{path}: title does not match the input episode")

    summary = result.get("summary")
    if not isinstance(summary, str):
        errors.append(f"{path}: summary must be a string")
    else:
        word_count = len(summary.split())
        if not 200 <= word_count <= 300:
            errors.append(
                f"{path}: summary must contain 200-300 words; received {word_count}"
            )

    validate_string_list(
        result.get("top_takeaways"),
        "top_takeaways",
        path,
        errors,
        exact_length=5,
    )
    validate_quotes(result.get("notable_quotes"), path, errors)
    validate_string_list(result.get("topics"), "topics", path, errors)
    validate_fact_checks(result.get("fact_checks"), path, errors)


def validate_markdown_output(path: Path, errors: list[str]) -> None:
    try:
        markdown = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"Missing file: {path}")
        return
    except OSError as exc:
        errors.append(f"Could not read {path}: {exc}")
        return

    if not markdown.startswith("# "):
        errors.append(f"{path}: Markdown output must start with an H1 title")
    for section in REQUIRED_MARKDOWN_SECTIONS:
        if section not in markdown:
            errors.append(f"{path}: missing Markdown section {section!r}")


def parse_log_events(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"Missing file: {path}")
        return []
    except OSError as exc:
        errors.append(f"Could not read {path}: {exc}")
        return []

    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        parts = line.split(" | ", 2)
        if len(parts) != 3:
            errors.append(f"{path}:{line_number}: malformed log line")
            continue
        try:
            payload = json.loads(parts[2])
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid event JSON: {exc}")
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("event"), str):
            errors.append(f"{path}:{line_number}: event payload must contain event")
            continue
        events.append(payload)
    return events


def validate_log(
    path: Path,
    episode_ids: set[str],
    errors: list[str],
) -> None:
    events = parse_log_events(path, errors)
    event_names = {event["event"] for event in events}
    for required in ("batch_started", "batch_completed"):
        if required not in event_names:
            errors.append(f"{path}: missing {required!r} event")

    for episode_id in sorted(episode_ids):
        episode_events = {
            event["event"]
            for event in events
            if event.get("episode_id") == episode_id
        }
        for required in REQUIRED_EPISODE_EVENTS:
            if required not in episode_events:
                errors.append(
                    f"{path}: episode {episode_id!r} is missing {required!r} event"
                )
        if not {
            "heuristic_analysis_completed",
            "llm_analysis_completed",
        } & episode_events:
            errors.append(
                f"{path}: episode {episode_id!r} has no completed analysis event"
            )


def validate_deliverables(
    input_dir: Path,
    output_dir: Path,
    log_path: Path | None,
) -> list[str]:
    errors: list[str] = []
    episodes = expected_episodes(input_dir, errors)

    if not output_dir.is_dir():
        errors.append(f"Output directory does not exist: {output_dir}")
    for episode_id, title in episodes.items():
        validate_json_output(
            output_dir / f"{episode_id}_analysis.json",
            episode_id,
            title,
            errors,
        )
        validate_markdown_output(
            output_dir / f"{episode_id}_analysis.md",
            errors,
        )

    if log_path is not None:
        validate_log(log_path, set(episodes), errors)
    return errors


def main() -> int:
    args = parse_args()
    errors = validate_deliverables(args.input, args.output, args.log)
    if errors:
        print(f"Deliverable validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    log_suffix = f" and {args.log}" if args.log else ""
    print(f"Deliverables in {args.output}{log_suffix} satisfy the assignment contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
