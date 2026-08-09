from pathlib import Path

import pytest

from app.input import discover_input_files, load_episode


def test_load_text_episode_with_metadata(tmp_path: Path):
    path = tmp_path / "episode.txt"
    path.write_text(
        """Episode ID: txt-001
Title: A Plain Text Episode
Host: Maya Chen
Guests: Luis Rivera

[00:00] Maya: Welcome to the show.
[00:14] Luis: Thanks for having me.
[00:30] Maya: What should listeners know?
[00:35] Luis: Reliable workflows need explicit contracts and observable failures.
""",
        encoding="utf-8",
    )

    episode = load_episode(path)

    assert episode["episode_id"] == "txt-001"
    assert episode["title"] == "A Plain Text Episode"
    assert episode["host"] == "Maya Chen"
    assert episode["guests"] == ["Luis Rivera"]
    assert episode["transcript"][1] == {
        "timestamp": "00:14",
        "speaker": "Luis",
        "section": "Transcript",
        "text": "Thanks for having me.",
    }


def test_load_text_episode_infers_metadata(tmp_path: Path):
    path = tmp_path / "remote_work_notes.txt"
    path.write_text(
        "[00:00] Sarah: Welcome.\n[00:10] Mark: Thanks for having me.\n",
        encoding="utf-8",
    )

    episode = load_episode(path)

    assert episode["episode_id"] == "remote_work_notes"
    assert episode["title"] == "Remote Work Notes"
    assert episode["host"] == "Sarah"
    assert episode["guests"] == ["Mark"]


def test_discover_input_files_accepts_json_and_text(tmp_path: Path):
    for name in ("one.json", "two.txt", "ignore.md"):
        (tmp_path / name).write_text("placeholder", encoding="utf-8")

    files = discover_input_files(tmp_path)

    assert [path.name for path in files] == ["one.json", "two.txt"]


def test_text_episode_rejects_unstructured_lines(tmp_path: Path):
    path = tmp_path / "invalid.txt"
    path.write_text("This is not a timestamped transcript.", encoding="utf-8")

    with pytest.raises(ValueError, match="expected metadata"):
        load_episode(path)
