"""
openai_client.py — Calls GPT-5, GPT-4.5, o-series via OpenAI's HTTP API.

Used by: runner.py (via clients.get_client_for).

We hit the /v1/chat/completions endpoint directly with httpx so we don't pin
to any particular SDK version — the benchmark needs to be re-runnable in 18
months. OpenAI's chat-completions schema has been stable since 2023.

Env: OPENAI_API_KEY (required), OPENAI_BASE_URL (optional, defaults to api.openai.com).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from . import ClientResponse


class OpenAIClient:
    name = "openai"
    env_key = "OPENAI_API_KEY"

    def __init__(self) -> None:
        self.api_key = os.environ["OPENAI_API_KEY"]
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")

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
        # o-series and gpt-5 use max_completion_tokens; older models use max_tokens.
        # We send both keys defensively — OpenAI ignores unknown fields.
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_completion_tokens": max_tokens,
        }
        if not model.lower().startswith(("o1", "o3", "o4", "gpt-5")):
            body["max_tokens"] = max_tokens

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            payload = r.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)

        try:
            text = payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"OpenAI response missing content: {payload}") from exc

        usage = payload.get("usage") or {}
        return ClientResponse(
            text=text,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
            model=model,
            raw=payload,
        )
