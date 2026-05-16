"""
google_client.py — Calls Gemini 3 Pro, Gemini Flash via Google's Generative
Language API.

Used by: runner.py (via clients.get_client_for).

We hit the v1beta generateContent endpoint with the API key in the query
string (Google's auth pattern for AI Studio keys).

Env: GOOGLE_API_KEY (required), GOOGLE_BASE_URL (optional).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from . import ClientResponse


class GoogleClient:
    name = "google"
    env_key = "GOOGLE_API_KEY"

    def __init__(self) -> None:
        self.api_key = os.environ["GOOGLE_API_KEY"]
        self.base_url = os.getenv(
            "GOOGLE_BASE_URL",
            "https://generativelanguage.googleapis.com",
        ).rstrip("/")

    async def call(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 512,
        timeout: float = 60.0,
    ) -> ClientResponse:
        # Strip "models/" prefix if caller already included it.
        m = model
        if m.startswith("models/"):
            m = m[len("models/"):]
        url = (
            f"{self.base_url}/v1beta/models/{m}:generateContent"
            f"?key={self.api_key}"
        )
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": max_tokens,
            },
        }

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
            payload = r.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)

        text_parts: list[str] = []
        for cand in payload.get("candidates", []) or []:
            content = cand.get("content") or {}
            for part in content.get("parts", []) or []:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
        text = "".join(text_parts)

        usage = payload.get("usageMetadata") or {}
        return ClientResponse(
            text=text,
            input_tokens=int(usage.get("promptTokenCount", 0)),
            output_tokens=int(usage.get("candidatesTokenCount", 0)),
            latency_ms=latency_ms,
            model=model,
            raw=payload,
        )
