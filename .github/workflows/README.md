# GitHub Actions workflows

These workflows validate the code and deliverables, publish container images, and
create tagged releases.

## Workflow inventory

| File | Trigger | Purpose |
|---|---|---|
| `ci.yml` | Pull requests; pushes to `main`; `v*` tags | Lint, test, smoke-test Python and Docker, then publish eligible images to GHCR |
| `assignment-rubric.yml` | Pull requests; pushes to `main`; manual dispatch | Validate checked-in artifacts, regenerate deterministic outputs, and test the Docker deliverable |
| `pre-commit.yml` | Pull requests; pushes to `main` | Run the repository's pre-commit hooks against all files |
| `tag.yml` | Pushes to `main` | Create the next semantic-version tag |
| `release.yml` | Successful completion of the Tag workflow | Create a GitHub release for the tag at the workflow commit |

## CI dependency flow

```text
pull request / push
    |-- Python lint, tests, and smoke test
    |-- Docker build and smoke test
    |-- checked-in and regenerated artifact checks
    `-- pre-commit

eligible push after CI
    `-- GHCR image publish

push to main
    `-- tag workflow
          `-- successful tag workflow
                `-- GitHub release
```

## Permissions and credentials

Most jobs use read-only repository contents. Publishing receives `packages: write`,
tagging and release jobs receive `contents: write`, and GHCR authentication uses the
built-in `GITHUB_TOKEN`.

The deterministic CI path sets `MODEL_PROVIDER=heuristic`; pull requests therefore
do not need model credentials and do not make paid inference calls.

## Maintenance checklist

When changing a workflow:

1. Confirm its event filter and branch/tag scope.
2. Confirm job dependencies and failure behavior.
3. Keep permissions at the workflow or job minimum.
4. Ensure referenced Make targets and scripts exist in the same revision.
5. Keep Docker mounts and CLI paths aligned with the runtime image.
6. Update this table when adding, renaming, or removing a workflow.
7. Run YAML/pre-commit checks locally.

Artifact validation workflows upload generated output and logs on failure so a CI
failure can be diagnosed without rerunning the job locally.
