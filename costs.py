"""
costs.py — Model rate card and cost estimation.

Used by: runner.py (pre-run estimate + per-call cost tracking) and
aggregator.py (total cost in summary.json).

Rates are USD per 1M tokens, accurate as of 2026-05. Update the dict below as
providers shift pricing. Rates are deliberately rough — they're for budget
estimation, not billing reconciliation. The runner reads `usage` from each
API response and bills against the actual token counts.

If a model name isn't found, we fall back to (5, 25) — a deliberately
high-end-of-frontier estimate so the cost guardrail errs on the safe side.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rate:
    input_per_million: float    # USD per 1M input tokens
    output_per_million: float   # USD per 1M output tokens


# Rate card as of 2026-05-16.
# Keys are lowercase substrings; we do prefix/contains matching in
# rate_for() to handle aliases and minor version bumps without a code change.
RATE_CARD: dict[str, Rate] = {
    # --- OpenAI ---
    "gpt-5":               Rate(3.00, 15.00),
    "gpt-5-mini":          Rate(0.60, 2.40),
    "gpt-4.5":             Rate(10.00, 30.00),
    "gpt-4o":              Rate(2.50, 10.00),
    "o4":                  Rate(15.00, 60.00),
    "o3":                  Rate(10.00, 40.00),
    "o1":                  Rate(15.00, 60.00),

    # --- Anthropic ---
    "claude-4.7-opus":     Rate(15.00, 75.00),
    "claude-4.7-sonnet":   Rate(3.00, 15.00),
    "claude-4.7-haiku":    Rate(0.80, 4.00),
    "claude-4.7":          Rate(15.00, 75.00),     # default to Opus
    "claude-opus-4-7":     Rate(15.00, 75.00),     # API id form
    "claude-sonnet-4-7":   Rate(3.00, 15.00),

    # --- Google ---
    "gemini-3-pro":        Rate(3.50, 10.50),
    "gemini-3-flash":      Rate(0.30, 1.20),
    "gemini-3":            Rate(3.50, 10.50),      # default to Pro
    "gemini-2.5-pro":      Rate(3.50, 10.50),
    "gemini-2.0-flash":    Rate(0.10, 0.40),

    # --- Together / Llama ecosystem ---
    "llama-4-maverick":    Rate(0.50, 0.50),
    "llama-4-scout":       Rate(0.20, 0.20),
    "llama-4":             Rate(0.50, 0.50),
    "deepseek-v3.5":       Rate(0.30, 1.00),
    "deepseek":            Rate(0.30, 1.00),
    "mistral-large":       Rate(2.00, 6.00),
    "qwen-3":              Rate(0.40, 1.60),
}

# Fallback if no key matches — intentionally conservative (overestimates cost).
DEFAULT_RATE = Rate(5.00, 25.00)


def rate_for(model: str) -> Rate:
    """Look up the rate for a model. Substring match, falls back to DEFAULT_RATE."""
    m = model.lower()
    # Try exact match first
    if m in RATE_CARD:
        return RATE_CARD[m]
    # Then longest-prefix match
    candidates = [(k, v) for k, v in RATE_CARD.items() if k in m or m.startswith(k)]
    if candidates:
        # Prefer the longest matching key (most specific)
        candidates.sort(key=lambda kv: len(kv[0]), reverse=True)
        return candidates[0][1]
    return DEFAULT_RATE


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute USD cost for a single call given the rate card."""
    r = rate_for(model)
    return (
        input_tokens * r.input_per_million / 1_000_000.0
        + output_tokens * r.output_per_million / 1_000_000.0
    )


def estimate_total_cost(
    models: list[str],
    n_names: int,
    n_prompts: int,
    avg_input_tokens: int = 120,
    avg_output_tokens: int = 350,
) -> float:
    """
    Rough up-front cost estimate for a full run.

    Defaults assume each prompt is ~120 input tokens, each response ~350
    output tokens. Override if your prompts/responses are bigger.
    """
    total = 0.0
    n_calls_per_model = n_names * n_prompts
    for model in models:
        total += n_calls_per_model * cost_usd(model, avg_input_tokens, avg_output_tokens)
    return total
