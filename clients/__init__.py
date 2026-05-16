"""
clients — Model API clients for the hallucination benchmark.

Each client exposes the same async interface:

    async def call(model: str, prompt: str, max_tokens: int, timeout: float)
        -> ClientResponse

Returning latency_ms, usage tokens, and the raw text. The runner picks the
right client based on the model name's prefix.

If the relevant API key env var is missing, get_client_for() returns None and
the runner skips that model with a warning — it never crashes the run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class ClientResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    model: str
    raw: dict  # provider-specific payload, saved for debugging


class ModelClient(Protocol):
    name: str
    env_key: str

    async def call(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 512,
        timeout: float = 60.0,
    ) -> ClientResponse: ...


def get_client_for(model: str) -> Optional["ModelClient"]:
    """
    Map a model name (e.g. "gpt-5", "claude-4.7-opus", "gemini-3-pro",
    "llama-4-maverick") to the appropriate client instance. Returns None if
    the model's API key is missing — caller logs a warning and skips.
    """
    # Local imports keep the surface clean and avoid forcing all SDK deps.
    from .openai_client import OpenAIClient
    from .anthropic_client import AnthropicClient
    from .google_client import GoogleClient
    from .together_client import TogetherClient

    m = model.lower()

    if m.startswith(("gpt-", "o1-", "o3-", "o4-")):
        if not os.getenv("OPENAI_API_KEY"):
            return None
        return OpenAIClient()
    if m.startswith("claude"):
        if not os.getenv("ANTHROPIC_API_KEY"):
            return None
        return AnthropicClient()
    if m.startswith(("gemini", "google")):
        if not os.getenv("GOOGLE_API_KEY"):
            return None
        return GoogleClient()
    if m.startswith(("llama", "meta-", "mistral", "qwen", "deepseek")):
        if not os.getenv("TOGETHER_API_KEY"):
            return None
        return TogetherClient()

    return None


__all__ = ["ClientResponse", "ModelClient", "get_client_for"]
