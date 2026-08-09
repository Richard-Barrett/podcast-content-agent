# Generated outputs

This directory contains the checked-in examples and default runtime output of the
podcast agent. Each episode creates two files with the same information in different
formats.

## Naming convention

```text
<episode_id>_analysis.json
<episode_id>_analysis.md
```

For example, `ep002_ai_healthcare.json` produces:

```text
ep002_analysis.json
ep002_analysis.md
```

## Formats

| Format | Audience | Contents |
|---|---|---|
| JSON | APIs, automation, tests, and downstream storage | Complete structured `EpisodeAnalysis` object |
| Markdown | Editors, reviewers, and demonstrations | Summary, five takeaways, quotes, topics, and fact-check table |

The JSON file is the canonical machine-readable artifact. The Markdown renderer
escapes table separators and presents confidence values to two decimal places.

## Regenerating outputs

Generate all default fixtures without external credentials:

```bash
MODEL_PROVIDER=heuristic python -m app.main
```

With Docker Compose:

```bash
docker compose run --rm -e MODEL_PROVIDER=heuristic agent
```

Configured OpenAI or Ollama runs may produce different editorial wording while
preserving the schema. Provider results that violate the contract fall back to the
deterministic analyzer.

## Review checklist

When committing regenerated examples, confirm that:

- every input episode has both formats;
- summaries contain 200-300 words;
- each result has exactly five top takeaways;
- quotes retain transcript timestamps and wording;
- JSON and Markdown describe the same result;
- fact-check sources and confidence values are present;
- no secrets, raw API responses, or private transcripts were written.

Treat these files as build artifacts with review value. Edit the source transcript,
knowledge base, or runtime code and regenerate rather than manually fixing only one
format.
