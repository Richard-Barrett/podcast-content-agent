# Local knowledge base

This directory contains curated evidence used by the deterministic fact-checking
stage. It is independent of the transcripts: a statement appearing in an episode is
not automatically treated as proof of itself.

## Files

| File | Description |
|---|---|
| `facts.json` | Fact records, retrieval aliases, editorial verdicts, explanations, source identifiers, and base confidence values |

## Entry schema

```json
{
  "fact": "A concise factual statement.",
  "aliases": ["alternate claim wording"],
  "status": "Verified true",
  "verification": "Why the available evidence supports this verdict.",
  "source": "local-kb:topic-001",
  "confidence": 0.95
}
```

The file wraps entries in a top-level `facts` array.

## Field guidance

| Field | Purpose |
|---|---|
| `fact` | Canonical statement tokenized by retrieval |
| `aliases` | Truth-preserving wording variants that improve lexical recall |
| `status` | Editorial classification returned for a match |
| `verification` | Reader-facing explanation of scope, caveats, or limitations |
| `source` | Stable provenance identifier surfaced in output |
| `confidence` | Base confidence between `0.0` and `1.0`, adjusted by match strength |

## Curation rules

- Add only evidence that has been reviewed and is appropriate for the repository.
- Keep absolute language only when the evidence supports it.
- Use aliases for genuine paraphrases, not for forcing an unrelated claim to match.
- Give every entry a unique and stable source ID.
- Explain important scope limits in `verification`.
- Mark transcript-only personal anecdotes as unverifiable unless independent
  evidence is available.
- Revisit time-sensitive claims and identify them as potentially outdated when
  appropriate.

## Retrieval behavior

`app/factcheck.py` tokenizes the claim, canonical fact, and aliases, then compares
lexical overlap. Matches below the configured threshold produce `local-kb:no-match`.
The final confidence is bounded and combines the entry's base confidence with match
strength.

After changing the KB, run:

```bash
python -m pytest -q tests/test_factcheck.py
python -m app.main --input data/input --kb kb/facts.json
```

Review regenerated fact checks for both intended matches and accidental matches.
