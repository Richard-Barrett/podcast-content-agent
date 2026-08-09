# Documentation

This directory holds design documentation that is more detailed or specialized
than the repository's root README.

## Documents

| File | Description |
|---|---|
| [`deployment_strategy.md`](deployment_strategy.md) | Assignment-compliant AWS response capped below 500 words |
| [`production_architecture_notes.md`](production_architecture_notes.md) | Extended service, security, reliability, cost, and delivery design notes |

## Documentation conventions

- Keep the root README focused on onboarding, contracts, and routine operation.
- Put longer architecture decisions and production proposals here.
- Link documents from the root README and from related directory READMEs.
- Describe the current implementation separately from proposed future state.
- Prefer concrete commands, paths, ownership boundaries, and failure behavior.
- Update documentation in the same change as a CLI, schema, provider, workflow, or
  deployment change.

## Suggested future documents

As the project grows, useful additions would include:

- an architecture decision record for provider selection;
- an output-schema versioning and migration policy;
- a knowledge-base curation and provenance policy;
- an operational runbook with alerts and incident procedures;
- evaluation criteria for summary quality and fact-check precision.
