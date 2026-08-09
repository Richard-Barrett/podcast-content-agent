# Repository scripts

This directory contains standalone maintenance and acceptance tools that support the
application but are not part of its runtime package.

## Scripts

| File | Purpose |
|---|---|
| `validate_deliverables.py` | Validate checked-in or freshly generated episode artifacts against the assignment contract |

## Deliverable validation

Validate the checked-in outputs:

```bash
python scripts/validate_deliverables.py
```

Validate outputs and structured lifecycle events from a fresh run:

```bash
python scripts/validate_deliverables.py \
  --output .ci-outputs \
  --log .ci-logs/agent.log
```

The validator discovers expected episode IDs and titles from JSON and text inputs
under `data/input`, then
checks:

- matching JSON and Markdown files for every input episode;
- episode identity and title consistency;
- 200-300 word summaries and exactly five takeaways;
- non-empty quotes, topics, and fact checks;
- bounded confidence values and populated verification fields;
- required Markdown sections;
- batch and per-episode lifecycle events when `--log` is supplied.
- the official AWS deployment response's 500-word maximum.

The script uses only the Python standard library so assignment validation can run in
GitHub Actions without installing project dependencies.
