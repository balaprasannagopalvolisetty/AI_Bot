"""
Shared OpenAI client helper.

Centralizes OpenAI access so every module uses the modern openai>=1.0 SDK
(`OpenAI` client + `client.chat.completions.create`) instead of the deprecated
`openai.ChatCompletion.create` interface that was removed in openai 1.x.

Usage:
    from src.utils.ai_client import AIClient
    ai = AIClient(config)
    text = ai.chat(
        system="You are a helpful assistant.",
        user="Say hello.",
        temperature=0.7,
        max_tokens=200,
    )

The API key is resolved (in order) from:
    1. config['AI_SETTINGS']['api_key']
    2. the OPENAI_API_KEY environment variable
"""

import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class AIClient:
    """Thin wrapper around the OpenAI chat completions API."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        ai_settings = self.config.get("AI_SETTINGS", {})
        self.api_key = ai_settings.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        self.model = ai_settings.get("model", "gpt-4o-mini")
        self._client = None

        if not self.api_key:
            logger.warning(
                "No OpenAI API key found. Set AI_SETTINGS['api_key'] in config.py "
                "or the OPENAI_API_KEY environment variable to enable AI features."
            )

    @property
    def available(self) -> bool:
        """True if an API key is configured and the SDK is importable."""
        return bool(self.api_key) and self.client is not None

    @property
    def client(self):
        """Lazily construct and cache the OpenAI client."""
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:  # ImportError or client init error
                logger.error(f"Could not initialize OpenAI client: {e}")
                self._client = None
        return self._client

    def chat(
        self,
        user: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: Optional[str] = None,
    ) -> str:
        """
        Run a single-turn chat completion and return the response text.

        Returns an empty string on any failure so callers can fall back
        gracefully rather than crashing the application flow.
        """
        if not self.available:
            logger.error("AIClient.chat called but no OpenAI client is available.")
            return ""

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"OpenAI chat completion failed: {e}")
            return ""
