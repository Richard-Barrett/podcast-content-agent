# Runtime logs

The CLI writes structured execution events to `agent.log` in this directory by
default. The same events are also emitted to the console.

`agent.log` is generated runtime state and may be overwritten or removed between
runs. This README is the only durable documentation expected in the directory.

## Event lifecycle

A normal batch includes events similar to:

```text
batch_started
  plan_created
  transcript_parsed
  llm_analysis_started          # configured providers only
  llm_analysis_completed        # valid provider response
  llm_analysis_failed_fallback  # provider or validation failure
  heuristic_analysis_completed  # deterministic path
  claim_verified                # repeated for extracted claims
  episode_completed
  outputs_written
batch_completed
```

Each log payload includes an `event` field plus relevant context such as episode ID,
provider, model, status, confidence, source, or output path.

## Operational use

- Search `llm_analysis_failed_fallback` when output unexpectedly uses the
  deterministic analyzer.
- Search `claim_verified` to audit retrieval results and confidence.
- Compare `batch_started.files` with `batch_completed.count` during troubleshooting.
- Correlate an episode's events with its files under `../outputs/` by `episode_id`.

Logs intentionally expose actions and results without recording hidden
chain-of-thought. Do not add raw credentials, authorization headers, or sensitive
transcripts to event fields.

To write logs elsewhere:

```bash
python -m app.main --logs path/to/log-directory
```
