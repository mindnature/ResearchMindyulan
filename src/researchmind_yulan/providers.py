from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
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
        data = _request_json(request, self.timeout, "OpenAI-compatible")
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise RuntimeError("Unexpected OpenAI-compatible provider response shape") from exc


@dataclass
class GeminiProvider:
    """Native Google Gemini generateContent REST provider."""

    api_key: str
    model: str
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "GeminiProvider | None":
        api_key = (
            os.getenv("RM_YULAN_GEMINI_API_KEY", "").strip()
            or os.getenv("GEMINI_API_KEY", "").strip()
        )
        model = os.getenv("RM_YULAN_GEMINI_MODEL", "").strip()
        if not api_key or not model:
            return None
        return cls(
            api_key=api_key,
            model=model,
            base_url=os.getenv(
                "RM_YULAN_GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta",
            ).rstrip("/"),
            timeout=int(os.getenv("RM_YULAN_LLM_TIMEOUT", "60")),
        )

    def complete(self, system: str, user: str) -> str:
        model = self.model
        if model.startswith("models/"):
            model = model[len("models/") :]
        encoded_model = urllib.parse.quote(model, safe="-._")
        endpoint = f"{self.base_url}/models/{encoded_model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user}],
                }
            ],
            "generationConfig": {"temperature": 0.2},
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        data = _request_json(request, self.timeout, "Gemini")
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(str(part.get("text") or "") for part in parts if isinstance(part, dict))
            if not text.strip():
                raise ValueError("empty Gemini response")
            return text.strip()
        except (KeyError, IndexError, TypeError, AttributeError, ValueError) as exc:
            raise RuntimeError("Unexpected Gemini provider response shape") from exc


def _request_json(request: urllib.request.Request, timeout: int, provider_name: str) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{provider_name} provider request failed: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected {provider_name} provider response shape")
    return data


def resolve_provider(prefer_llm: bool = True) -> LLMProvider:
    if not prefer_llm:
        return DeterministicProvider()

    requested = os.getenv("RM_YULAN_LLM_PROVIDER", "auto").strip().lower()
    if requested in {"gemini", "google"}:
        return GeminiProvider.from_env() or DeterministicProvider()
    if requested in {"openai", "openai_compatible", "chat_completions"}:
        return ChatCompletionsProvider.from_env() or DeterministicProvider()

    gemini = GeminiProvider.from_env()
    if gemini is not None:
        return gemini
    compatible = ChatCompletionsProvider.from_env()
    if compatible is not None:
        return compatible
    return DeterministicProvider()
