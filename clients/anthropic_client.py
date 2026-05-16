"""
anthropic_client.py — Calls Claude 4.7 Opus, Sonnet, Haiku via Anthropic's HTTP API.

Used by: runner.py (via clients.get_client_for).

We hit /v1/messages directly with httpx, pinning the anthropic-version header
to 2023-06-01 (the long-stable version that supports the messages schema).

Env: ANTHROPIC_API_KEY (required), ANTHROPIC_BASE_URL (optional).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from . import ClientResponse


class AnthropicClient:
    name = "anthropic"
    env_key = "ANTHROPIC_API_KEY"

    def __init__(self) -> None:
        self.api_key = os.environ["ANTHROPIC_API_KEY"]
        self.base_url = os.getenv(
            "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
        ).rstrip("/")

    async def call(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 512,
        timeout: float = 60.0,
    ) -> ClientResponse:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}],
        }

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            payload = r.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)

        # Claude messages have content as a list of blocks; collect text blocks.
        text_parts: list[str] = []
        for block in payload.get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        text = "".join(text_parts)

        usage = payload.get("usage") or {}
        return ClientResponse(
            text=text,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            latency_ms=latency_ms,
            model=model,
            raw=payload,
        )
