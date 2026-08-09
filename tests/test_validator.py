from pathlib import Path

from scripts.validate_deliverables import validate_quotes


def test_validator_rejects_quote_without_exact_transcript_provenance():
    transcript = [
        {
            "timestamp": "01:10",
            "speaker": "Guest",
            "text": "The original transcript wording.",
        }
    ]
    output_quotes = [
        {
            "timestamp": "01:11",
            "speaker": "Guest",
            "text": "The original transcript wording.",
        }
    ]
    errors: list[str] = []

    validate_quotes(output_quotes, Path("episode.json"), errors, transcript)

    assert errors == [
        (
            "episode.json: notable_quotes[0] does not exactly match "
            "a source transcript turn"
        )
    ]


def test_validator_accepts_exact_transcript_quote():
    transcript = [
        {
            "timestamp": "01:10",
            "speaker": "Guest",
            "text": "The original transcript wording.",
        }
    ]
    errors: list[str] = []

    validate_quotes(transcript.copy(), Path("episode.json"), errors, transcript)

    assert errors == []
