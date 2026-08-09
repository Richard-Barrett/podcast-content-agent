# Podcast Content Agent

A small, inspectable AI workflow that turns podcast transcript JSON into editorial
content and claim-level fact checks. It can use OpenAI, a local Ollama model, or a
credential-free deterministic analyzer, and it always produces the same structured
JSON and Markdown contracts.

This repository is designed to be easy to run in a review, easy to debug, and easy
to evolve into a production service without hiding orchestration behind a framework.

## What the agent produces

For each episode, the pipeline:

1. Loads the episode metadata and timestamped transcript.
2. Generates a 200-300 word editorial summary.
3. Selects exactly five takeaways, notable quotes, and topic tags.
4. Extracts externally checkable factual claims.
5. Retrieves the closest evidence from the local knowledge base.
6. Assigns each claim a status, explanation, confidence, and source.
7. Writes machine-readable JSON and editor-friendly Markdown.
8. Records structured lifecycle events in the application log.

Invalid or unavailable model output does not stop the batch. The agent logs the
provider failure and processes the episode with its deterministic fallback.

## Architecture

```text
Episode JSON
    |
    v
PodcastAgent
    |-- editorial analysis
    |     |-- OpenAI
    |     |-- Ollama
    |     `-- deterministic fallback
    |
    |-- claim extraction
    |-- local knowledge-base retrieval
    |-- verification scoring
    |-- JSON and Markdown rendering
    `-- structured event logging
```

The provider boundary is deliberately narrow: providers return the same analysis
dictionary, and the rest of the pipeline is provider-independent.

## Repository guide

Every project-owned directory contains its own README with local conventions and a
file inventory.

| Path | Purpose |
|---|---|
| [`app/`](app/) | Agent orchestration, provider adapters, models, retrieval, logging, and rendering |
| [`data/`](data/) | Input data boundary and episode fixtures |
| [`data/input/`](data/input/) | Transcript JSON files consumed by the CLI |
| [`docs/`](docs/) | Design and deployment documentation |
| [`kb/`](kb/) | Curated local facts used for retrieval-backed verification |
| [`logs/`](logs/) | Runtime event logs; generated log files are not source documentation |
| [`outputs/`](outputs/) | Generated JSON and Markdown episode analyses |
| [`tests/`](tests/) | Unit and behavior tests |
| [`.github/`](.github/) | Dependency automation and GitHub repository configuration |
| [`.github/workflows/`](.github/workflows/) | CI, rubric, tagging, and release workflows |

Tool-managed directories such as `.git/`, `.venv/`, `.pytest_cache/`,
`.ruff_cache/`, and `__pycache__/` are intentionally undocumented.

## Quick start

### Docker: no API key required

```bash
docker compose build agent
docker compose run --rm agent
```

The default provider is `heuristic`, so this path is deterministic and does not
make a network request. Results are written to `outputs/` and execution events to
`logs/agent.log`.

### Local Python

Python 3.11 or newer is required.

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m app.main
```

On Windows PowerShell, use the virtual-environment interpreter directly if the
environment is not activated:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

## Command-line interface

```bash
python -m app.main \
  --input data/input \
  --output outputs \
  --kb kb/facts.json \
  --logs logs
```

| Option | Default | Description |
|---|---|---|
| `--input` | `data/input` | One episode JSON file or a directory of JSON files |
| `--output` | `outputs` | Destination for generated JSON and Markdown |
| `--kb` | `kb/facts.json` | Local verification knowledge base |
| `--logs` | `logs` | Destination for `agent.log` |

Directory input is processed in filename order. Output filenames are derived from
`episode_id`, making reruns predictable and idempotent at the file level.

## Model providers

Copy `.env.example` to `.env` when using Docker Compose, or export the equivalent
variables in your shell.

| Variable | Default | Used by |
|---|---|---|
| `MODEL_PROVIDER` | `heuristic` | `heuristic`, `openai`, or `ollama` |
| `MODEL_NAME` | `gpt-4.1-mini` | OpenAI and Ollama model identifier |
| `OPENAI_API_KEY` | empty | OpenAI authentication |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama API endpoint |
| `LOCAL_MODEL` | `qwen2.5:3b` | Model pulled by the local Compose profile |

### OpenAI

```env
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4.1-mini
OPENAI_API_KEY=your-key
```

The adapter calls the OpenAI-compatible chat completions endpoint and requests a
JSON object.

### Ollama

```env
MODEL_PROVIDER=ollama
MODEL_NAME=qwen2.5:3b
LOCAL_MODEL=qwen2.5:3b
OLLAMA_URL=http://ollama:11434
```

Start the local model lab and run the agent:

```bash
make local-up
make local-run
```

OpenWebUI is then available at <http://localhost:3001>. Authentication is disabled
for this local demo, so do not expose that port publicly.

Useful commands:

```bash
make local-logs   # follow Ollama and OpenWebUI logs
make local-run    # rerun only the agent
make local-down   # stop the local-model services
```

Ollama model data and OpenWebUI state live in named Docker volumes and survive a
normal `local-down`.

## Provider validation and fallback

LLM output must include `summary`, `top_takeaways`, `notable_quotes`, `topics`, and
`claims`. The summary must be a string containing 200-300 words, and at least five
takeaways must be present. Invalid JSON, missing fields, invalid lengths, provider
timeouts, and provider errors all trigger the deterministic fallback.

This validation is important for downstream consumers: a successful HTTP response
is not treated as a successful episode unless its payload satisfies the editorial
contract.

## Input contract

Each file under `data/input/` has this shape:

```json
{
  "episode_id": "ep002",
  "title": "AI in Healthcare: Hype or Reality?",
  "host": "David Chen",
  "guests": ["Dr. Priya Patel", "Alex Moore"],
  "transcript": [
    {
      "timestamp": "00:00",
      "speaker": "David",
      "section": "Introduction",
      "text": "Welcome to the show."
    }
  ]
}
```

Required transcript fields are `timestamp`, `speaker`, `section`, and `text`.
Episode IDs should be unique and safe to use in filenames.

## Output contract

Each episode creates `<episode_id>_analysis.json` and
`<episode_id>_analysis.md`:

```json
{
  "episode_id": "ep002",
  "title": "AI in Healthcare: Hype or Reality?",
  "summary": "...",
  "top_takeaways": ["..."],
  "notable_quotes": [
    {"timestamp": "00:55", "speaker": "Dr. Priya", "text": "..."}
  ],
  "topics": ["#DeepDive", "#Challenges"],
  "fact_checks": [
    {
      "claim": "...",
      "status": "Verified true",
      "verification": "...",
      "confidence": 0.91,
      "source": "local-kb:health-ai-001"
    }
  ]
}
```

The Markdown version presents the same content as headings, block quotes, tags, and
a fact-check table.

## Fact-checking behavior

The verifier tokenizes a claim and every knowledge-base fact, removes common stop
words, and compares lexical overlap. It uses the stronger of Jaccard similarity and
a containment-weighted score. Matches below `0.28` are returned as unverifiable.

The local KB is intentionally transparent. Transcript presence is not independent
proof, and unnamed personal anecdotes remain unverifiable unless the KB contains
appropriate evidence. In production, the same `Verification` contract can sit in
front of curated customer sources, search, or a vector store.

## Logs and observability

Runtime logs are JSON payloads wrapped by the standard Python logger. Important
events include:

```text
batch_started
plan_created
transcript_parsed
llm_analysis_started
llm_analysis_completed
llm_analysis_failed_fallback
heuristic_analysis_completed
claim_verified
outputs_written
episode_completed
batch_completed
```

Events expose operational decisions, statuses, sources, and confidence without
recording private model reasoning.

## Development

Install the development tools once:

```bash
python -m pip install -r requirements-dev.txt
```

Run the fast checks:

```bash
python -m ruff check app tests
python -m ruff format --check app tests
python -m pytest -q
```

Or use the corresponding Make targets:

```bash
make lint
make format-check
make test
make pre-commit
```

The test suite is deterministic: tests explicitly select the heuristic provider or
inject a fake provider rather than using model configuration inherited from the
developer's shell.

## CI and release automation

GitHub Actions provides:

- Python linting, tests, and a heuristic smoke test on supported Python versions.
- Docker build and smoke-test coverage.
- Checked-in artifact and assignment-rubric validation.
- GHCR image publishing after successful checks on eligible pushes.
- Automated semantic-version tags and GitHub releases.
- A separate pre-commit workflow.

Dependabot checks Python and GitHub Actions dependencies weekly. See
`.github/README.md` and `.github/workflows/README.md` for trigger and permission
details.

## Production direction

The proposed AWS design uses S3 for transcripts and outputs, SQS for back-pressure,
ECS Fargate for stateless episode workers, CloudWatch for telemetry, and Bedrock or
an approved model provider for inference. It includes retry, idempotency, DLQ,
security, and cost controls.

See [`docs/deployment_strategy.md`](docs/deployment_strategy.md) for the full design.

## Troubleshooting

### The model is configured but the output looks deterministic

Check `logs/agent.log` for `llm_analysis_failed_fallback`. The event's `error` field
explains whether the provider failed or its payload violated the output contract.

### Ollama is unreachable from the container

When using the Compose profile, use `OLLAMA_URL=http://ollama:11434`. The
`host.docker.internal` default is intended for an Ollama server running on the host.

### No output files are created

Confirm that `--input` points to a JSON file or a directory containing JSON files.
The CLI exits with a clear message when no inputs are found.

### A claim is unexpectedly unverifiable

Review the normalized claim and `kb/facts.json`. Retrieval is lexical and requires
sufficient shared terminology. Add aliases only when they are truthful variants of
the underlying fact; aliases should not be used to force unsupported matches.

## License

See [`LICENSE`](LICENSE).
