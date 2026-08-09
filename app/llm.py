from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMConfig:
    provider: str = os.getenv("MODEL_PROVIDER", "heuristic").lower()
    model: str = os.getenv("MODEL_NAME", "gpt-4.1-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Small provider adapter for OpenAI-compatible APIs and Ollama."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()

    @property
    def enabled(self) -> bool:
        return self.config.provider in {"openai", "ollama"}

    def complete_json(self, system: str, user: str) -> dict:
        if self.config.provider == "openai":
            return self._openai(system, user)
        if self.config.provider == "ollama":
            return self._ollama(system, user)
        raise LLMError("LLM provider is disabled; use heuristic path")

    def _request(self, url: str, payload: dict, headers: dict[str, str]) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise LLMError(str(exc)) from exc

    @staticmethod
    def _parse_json_text(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            start, end = text.find("{"), text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise LLMError(f"Model did not return valid JSON: {exc}") from exc

    def _openai(self, system: str, user: str) -> dict:
        if not self.config.openai_api_key:
            raise LLMError("OPENAI_API_KEY is required for MODEL_PROVIDER=openai")
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        raw = self._request(
            f"{self.config.openai_base_url.rstrip('/')}/chat/completions",
            payload,
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.openai_api_key}",
            },
        )
        return self._parse_json_text(raw["choices"][0]["message"]["content"])

    def _ollama(self, system: str, user: str) -> dict:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.2},
        }
        raw = self._request(
            f"{self.config.ollama_url.rstrip('/')}/api/chat",
            payload,
            {"Content-Type": "application/json"},
        )
        return self._parse_json_text(raw["message"]["content"])
