from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from researchmind_yulan.providers import (
    ChatCompletionsProvider,
    DeterministicProvider,
    GeminiProvider,
    resolve_provider,
)


class ProviderSelectionTest(unittest.TestCase):
    def test_offline_always_uses_deterministic_provider(self):
        provider = resolve_provider(prefer_llm=False)
        self.assertIsInstance(provider, DeterministicProvider)

    def test_explicit_gemini_provider(self):
        env = {
            "RM_YULAN_LLM_PROVIDER": "gemini",
            "RM_YULAN_GEMINI_API_KEY": "test-key",
            "RM_YULAN_GEMINI_MODEL": "gemini-test",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = resolve_provider(prefer_llm=True)
        self.assertIsInstance(provider, GeminiProvider)
        self.assertEqual(provider.model, "gemini-test")

    def test_explicit_openai_compatible_provider(self):
        env = {
            "RM_YULAN_LLM_PROVIDER": "openai_compatible",
            "RM_YULAN_LLM_ENDPOINT": "https://example.org/v1/chat/completions",
            "RM_YULAN_LLM_API_KEY": "test-key",
            "RM_YULAN_LLM_MODEL": "test-model",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = resolve_provider(prefer_llm=True)
        self.assertIsInstance(provider, ChatCompletionsProvider)
        self.assertEqual(provider.model, "test-model")

    def test_missing_credentials_falls_back(self):
        with patch.dict(os.environ, {"RM_YULAN_LLM_PROVIDER": "gemini"}, clear=True):
            provider = resolve_provider(prefer_llm=True)
        self.assertIsInstance(provider, DeterministicProvider)


if __name__ == "__main__":
    unittest.main()
