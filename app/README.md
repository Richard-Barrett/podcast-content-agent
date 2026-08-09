# Application package

This directory contains the complete runtime implementation. The package uses only
the Python standard library, keeping the container small and the execution path easy
to inspect.

## Module map

| File | Responsibility |
|---|---|
| `main.py` | Parses CLI arguments, discovers inputs, runs the batch, writes outputs, and logs batch events |
| `input.py` | Discovers and normalizes JSON or timestamped text transcripts into one episode contract |
| `agent.py` | Orchestrates editorial analysis, validates model output, applies fallback behavior, and verifies claims |
| `llm.py` | Adapts OpenAI-compatible chat completions and Ollama to a common JSON response |
| `factcheck.py` | Retrieves the closest local fact and produces a scored verification |
| `models.py` | Defines the dataclasses shared across orchestration and rendering |
| `render.py` | Serializes an `EpisodeAnalysis` to JSON and Markdown |
| `logger.py` | Configures console/file logging and emits structured events |
| `__init__.py` | Marks this directory as the `app` Python package |

## Runtime flow

```text
main.main
  -> discover_input_files / load_episode
  -> PodcastAgent.run_file
       -> LLMClient.complete_json (when configured)
       -> PodcastAgent._validate_llm_analysis
       -> PodcastAgent._heuristic_analysis (disabled/failed/invalid LLM)
       -> LocalKnowledgeBase.verify (once per extracted claim)
       -> EpisodeAnalysis
  -> write_json
  -> write_markdown
```

## Contracts

`EpisodeAnalysis` is the internal handoff between orchestration and rendering. Keep
schema changes synchronized across:

- the dataclasses in `models.py`;
- the model prompt and validation in `agent.py`;
- both renderers in `render.py`;
- tests and checked-in examples under `outputs/`;
- the input/output documentation in the root README.

LLM output is untrusted input. Validate it before constructing dataclasses or using
it downstream. Provider failures and validation failures must remain recoverable so
one episode cannot terminate a batch.

## Adding a model provider

1. Add its configuration to `LLMConfig`.
2. Include it in `LLMClient.enabled`.
3. Implement a provider method that returns a parsed dictionary.
4. Route `complete_json` to the method.
5. Preserve `LLMError` for transport/provider failures.
6. Add isolated tests that do not make live network calls.
7. Document the required environment variables in the root README and `.env.example`.

Provider-specific payload details belong in `llm.py`; orchestration should not need
to know which provider produced the dictionary.

## Fact-check retrieval

`LocalKnowledgeBase.verify` compares normalized claim tokens with fact and alias
tokens. A result at or above the overlap threshold returns the KB entry's status,
verification, and source with a bounded confidence score. A lower result returns an
explicit no-match verification.

When adjusting tokenization, thresholds, or scoring, test both false-negative and
false-positive behavior. A permissive match can be more damaging than an
unverifiable result.

## Running this package

From the repository root:

```bash
python -m app.main
python -m app.main --input data/input/ep002_ai_healthcare.json
python -m app.main --input path/to/timestamped_transcript.txt
```

Run lint and tests after changes:

```bash
python -m ruff check app tests
python -m pytest -q
```
