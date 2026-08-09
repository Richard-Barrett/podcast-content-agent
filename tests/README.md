# Tests

This directory contains the deterministic pytest suite for agent behavior and local
fact retrieval.

## Test map

| File | Coverage |
|---|---|
| `test_agent.py` | Required output sections, 200-300 word summaries, and fallback after invalid model output |
| `test_factcheck.py` | Known-fact retrieval and explicit unverifiable behavior for unknown claims |
| `test_input.py` | JSON/text discovery, text metadata inference, normalization, and malformed-input handling |

## Run the suite

From the repository root:

```bash
python -m pytest -q
```

Run a file or a single test while iterating:

```bash
python -m pytest -q tests/test_agent.py
python -m pytest -q tests/test_agent.py::test_agent_falls_back_when_llm_summary_has_wrong_length
```

## Test design rules

- Do not call live OpenAI or Ollama endpoints.
- Select the heuristic provider explicitly for deterministic integration behavior.
- Inject a small fake provider when testing model response validation or fallback.
- Use pytest's `tmp_path` for logs and other transient files.
- Assert contracts and observable behavior rather than private implementation steps.
- Add regression coverage with every bug fix.

The shell may define `MODEL_PROVIDER`. Tests must not inherit that value implicitly,
because doing so makes pre-commit dependent on network availability and local model
state.

## Useful quality checks

```bash
python -m ruff check app tests
python -m ruff format --check app tests
python -m pytest -q
```

When changing retrieval data or scoring, add both a positive match and an unrelated
claim to protect against overly permissive behavior.
