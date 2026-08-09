# GitHub repository automation

This directory contains repository-level automation consumed by GitHub.

## Contents

| Path | Description |
|---|---|
| `dependabot.yml` | Weekly Python and GitHub Actions dependency update policy |
| [`workflows/`](workflows/) | Continuous integration, deliverable validation, tagging, and release automation |

## Dependabot policy

Dependabot checks:

- Python development dependencies on Monday at 06:00 America/Chicago;
- GitHub Actions on Monday at 06:15 America/Chicago.

Minor and patch updates are grouped to reduce pull-request noise. Dependency pull
requests receive ecosystem-specific labels and conventional commit prefixes.

When editing automation:

- pin actions to deliberate major versions;
- use the smallest required `permissions` block;
- avoid placing secrets directly in workflow YAML;
- keep credential-free checks on pull requests;
- document new triggers and release effects in `workflows/README.md`;
- validate YAML and run pre-commit before pushing.

GitHub configuration changes can affect publishing and repository write access even
when application code is untouched, so review them as production changes.
