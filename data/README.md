# Data

This directory is the repository's input-data boundary. Runtime code should treat
its contents as source material, not as application configuration or verified
evidence.

## Contents

| Path | Description |
|---|---|
| [`input/`](input/) | JSON or text episode metadata and timestamped transcripts consumed by the CLI |

Generated analyses do not belong here; they are written to `../outputs/`. Facts
used as independent verification evidence belong in `../kb/`.

## Data handling conventions

- Use UTF-8 JSON or the documented timestamped text format.
- Keep one episode per file.
- Give each episode a stable, unique `episode_id`.
- Preserve timestamps and transcript wording when editing fixtures.
- Do not commit secrets, access tokens, private customer transcripts, or regulated
  data.
- Use synthetic or explicitly approved content for examples.

The Docker Compose service mounts `input/` read-only at `/app/data/input`, which
prevents the runtime container from altering source transcripts.
