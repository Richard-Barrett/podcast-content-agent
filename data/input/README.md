# Episode inputs

This directory contains the transcript JSON files processed by the agent's default
CLI invocation. Files are discovered with `*.json` and processed in filename order.

## Included fixtures

| File | Subject |
|---|---|
| `ep001_remote_work.json` | Remote and distributed work practices |
| `ep002_ai_healthcare.json` | AI adoption, regulation, privacy, and bias in healthcare |
| `ep003_bootstrapping.json` | Bootstrapping and venture-funding trade-offs |

## Schema

```json
{
  "episode_id": "ep001",
  "title": "The Future of Remote Work",
  "host": "Sarah Johnson",
  "guests": ["Mark Rivera"],
  "transcript": [
    {
      "timestamp": "00:00",
      "speaker": "Sarah",
      "section": "Introduction",
      "text": "Transcript text"
    }
  ]
}
```

## Field guidance

| Field | Guidance |
|---|---|
| `episode_id` | Unique, stable, and safe for use in an output filename |
| `title` | Human-readable episode title |
| `host` | Full host name; the analyzer may compare its first token with transcript speakers |
| `guests` | Array of full guest names; use an empty array when there are no guests |
| `transcript` | Ordered array of transcript turns |
| `timestamp` | Preserve the source timestamp, normally `MM:SS` |
| `speaker` | Consistent speaker label for the episode |
| `section` | Editorial section such as `Introduction`, `Deep Dive`, `Challenges`, or `Closing` |
| `text` | Verbatim turn text |

## Add an episode

1. Create a UTF-8 JSON file with the schema above.
2. Choose an `episode_id` that does not collide with an existing output.
3. Validate the JSON.
4. Run the single file first:

   ```bash
   python -m app.main --input data/input/your_episode.json
   ```

5. Inspect both generated formats and the claim-verification log events.

The deterministic analyzer relies on section names and transcript length when
selecting content. Meaningful sections produce better fallback results.
