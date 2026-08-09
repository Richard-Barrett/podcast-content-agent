PYTHON ?= python
LOCAL_MODEL ?= qwen2.5:3b

.PHONY: help install-dev run docker docker-build lint format-check test rubric-check check pre-commit clean \
	local-up local-run local-logs local-down \
	assignment-check assignment-static assignment-artifacts assignment-docker assignment-ollama assignment-full

help:
	@echo "Common targets:"
	@echo "  make test                 Run unit tests"
	@echo "  make lint                 Run Ruff lint checks"
	@echo "  make rubric-check         Validate current outputs against the Seekr rubric"
	@echo "  make assignment-check     Lint + unit tests + validate current deliverables"
	@echo "  make assignment-docker    Build/run Docker agent + validate generated deliverables"
	@echo "  make assignment-ollama    Run the full assignment with local Ollama + validate outputs"
	@echo "  make assignment-full      Full CI-safe acceptance suite (lint, tests, Docker, rubric)"
	@echo "  make local-up             Start Ollama + pull model + start OpenWebUI"
	@echo "  make local-down           Stop the local LLM stack"

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

run:
	$(PYTHON) -m app.main --input data/input --output outputs --kb kb/facts.json --logs logs

docker:
	docker compose run --rm agent

docker-build:
	docker compose build agent

lint:
	$(PYTHON) -m ruff check app tests scripts

format-check:
	$(PYTHON) -m ruff format --check app tests scripts

test:
	$(PYTHON) -m pytest -q

rubric-check:
	$(PYTHON) scripts/validate_deliverables.py

# Developer quality gate: fast checks against the current working tree/artifacts.
check: lint format-check test rubric-check

pre-commit:
	$(PYTHON) -m pre_commit run --all-files

clean:
	find outputs logs -maxdepth 1 -type f ! -name README.md -delete

# Local model lab: Ollama + OpenWebUI.
local-up:
	docker compose --profile local-llm up -d ollama
	docker compose --profile local-llm run --rm ollama-pull
	docker compose --profile local-llm up -d open-webui

local-run:
	docker compose --profile local-llm run --rm agent

local-logs:
	docker compose --profile local-llm logs -f ollama open-webui

local-down:
	docker compose --profile local-llm down

# -----------------------------------------------------------------------------
# Seekr assignment acceptance targets
# -----------------------------------------------------------------------------

# Code-only checks: useful before regenerating outputs.
assignment-static: lint format-check test

# Validate the output files/logs currently on disk against the assignment rubric.
assignment-artifacts: rubric-check

# Fast overall check of code + currently generated deliverables.
assignment-check: assignment-static assignment-artifacts

# Reproduce the submission in Docker with the deterministic provider, then validate it.
# This proves the containerized deliverable works without API keys or a local LLM.
assignment-docker: assignment-static
	docker compose config --quiet
	docker compose build agent
	docker compose run --rm -e MODEL_PROVIDER=heuristic agent
	$(PYTHON) scripts/validate_deliverables.py

# Run the actual local-LLM path against Ollama, then enforce the assignment rubric.
# `local-up` is idempotent and the Ollama model volume is persistent after first pull.
assignment-ollama: assignment-static local-up
	docker compose --profile local-llm run --rm \
		-e MODEL_PROVIDER=ollama \
		-e MODEL_NAME=$(LOCAL_MODEL) \
		-e OLLAMA_URL=http://ollama:11434 \
		agent
	$(PYTHON) scripts/validate_deliverables.py

# CI-safe end-to-end acceptance suite. It intentionally uses the deterministic
# Docker path so CI does not need to download a multi-GB Ollama model.
assignment-full: assignment-docker
	@echo "Seekr assignment acceptance suite passed."
