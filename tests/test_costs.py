"""
test_costs.py — Sanity checks on the rate card.

The cost guardrail in runner.py decides whether to require --yes-costs based
on these numbers. If they drift, the guardrail breaks.
"""

from __future__ import annotations

import pytest

from costs import DEFAULT_RATE, cost_usd, estimate_total_cost, rate_for


def test_rate_for_exact_match():
    r = rate_for("gpt-5")
    assert r.input_per_million == 3.00
    assert r.output_per_million == 15.00


def test_rate_for_alias_match():
    """Anthropic API ids contain dashes; substring match should resolve."""
    r1 = rate_for("claude-4.7-opus")
    r2 = rate_for("claude-opus-4-7")
    # Both should fall on Opus pricing
    assert r1.input_per_million == 15.00
    assert r2.input_per_million == 15.00


def test_rate_for_unknown_falls_back_to_default():
    r = rate_for("totally-made-up-model-2030")
    assert r == DEFAULT_RATE


def test_cost_usd_basic_math():
    # GPT-5: $3/$15 per 1M
    # 1000 input + 500 output → 1000*3/1e6 + 500*15/1e6 = 0.003 + 0.0075 = 0.0105
    cost = cost_usd("gpt-5", 1000, 500)
    assert cost == pytest.approx(0.0105)


def test_cost_usd_zero_tokens_zero_cost():
    assert cost_usd("gpt-5", 0, 0) == 0.0


def test_estimate_total_cost_scales_with_calls():
    """500 names × 3 prompts × 4 models with default token assumptions."""
    est = estimate_total_cost(
        models=["gpt-5", "claude-4.7-opus", "gemini-3-pro", "llama-4-maverick"],
        n_names=500,
        n_prompts=3,
    )
    # Should be in the ballpark of $50-$200 for the full benchmark.
    # Sanity bounds — wide because rates / token counts shift.
    assert 20.0 < est < 300.0
