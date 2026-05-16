"""
together_client.py — Calls Llama 4, DeepSeek, Mistral, Qwen via Together AI.

Used by: runner.py (via clients.get_client_for).

Together's chat-completions endpoint is OpenAI-schema-compatible. Any other
OpenAI-compatible host (Fireworks, Groq, Anyscale, vLLM, etc.) can be used by
overriding TOGETHER_BASE_URL.

Env: TOGETHER_API_KEY (required), TOGETHER_BASE_URL (optional).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from . import ClientResponse


class TogetherClient:
    name = "together"
    env_key = "TOGETHER_API_KEY"

    def __init__(self) -> None:
        self.api_key = os.environ["TOGETHER_API_KEY"]
        self.base_url = os.getenv(
            "TOGETHER_BASE_URL", "https://api.together.xyz"
        ).rstrip("/")

    async def call(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 512,
        timeout: float = 60.0,
    ) -> ClientResponse:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": max_tokens,
        }

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            payload = r.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)

        try:
            text = payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Together response missing content: {payload}") from exc

        usage = payload.get("usage") or {}
        return ClientResponse(
            text=text,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
            model=model,
            raw=payload,
        )
