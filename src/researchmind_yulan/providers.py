from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, system: str, user: str) -> str:
        """Return a text completion."""


@dataclass
class DeterministicProvider:
    """Offline-safe provider used for tests and competition demo fallback."""

    def complete(self, system: str, user: str) -> str:
        return (
            "Deterministic fallback active. The evidence pipeline completed without "
            "an external LLM. Review the structured gaps, counter-evidence, method "
            "risks, and audit trail before making a research decision."
        )


@dataclass
class ChatCompletionsProvider:
    """Minimal provider for OpenAI-compatible chat-completions endpoints."""

    endpoint: str
    api_key: str
    model: str
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "ChatCompletionsProvider | None":
        endpoint = os.getenv("RM_YULAN_LLM_ENDPOINT", "").strip()
        api_key = os.getenv("RM_YULAN_LLM_API_KEY", "").strip()
        model = os.getenv("RM_YULAN_LLM_MODEL", "").strip()
        if not endpoint or not api_key or not model:
            return None
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            model=model,
            timeout=int(os.getenv("RM_YULAN_LLM_TIMEOUT", "60")),
        )

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"LLM provider request failed: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise RuntimeError("Unexpected LLM provider response shape") from exc


def resolve_provider(prefer_llm: bool = True) -> LLMProvider:
    if prefer_llm:
        provider = ChatCompletionsProvider.from_env()
        if provider is not None:
            return provider
    return DeterministicProvider()
