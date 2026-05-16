"""
test_prompts.py — Sanity checks on prompt templates.

Cheap tests that catch obvious mistakes (missing variable substitution,
wrong registry mapping, etc.) before they corrupt a $200 run.
"""

from __future__ import annotations

import pytest

from prompts import PROMPT_REGISTRY, build_prompt


@pytest.mark.parametrize("version", list(PROMPT_REGISTRY.keys()))
def test_every_prompt_substitutes_name_and_category(version):
    prompt = build_prompt(version, "Ranavex", "fintech")
    assert "Ranavex" in prompt
    assert "fintech" in prompt


@pytest.mark.parametrize("version", ["v2_constrained", "v3_grounded"])
def test_structured_prompts_request_json(version):
    prompt = build_prompt(version, "TestName", "ai-agent")
    assert "JSON" in prompt or "json" in prompt


def test_v3_offers_cannot_verify_escape_hatch():
    """v3 must surface the 'cannot_verify' option — it's the whole point."""
    prompt = build_prompt("v3_grounded", "TestName", "ai-agent")
    assert "cannot_verify" in prompt


def test_unknown_version_raises():
    with pytest.raises(ValueError):
        build_prompt("v99_nonexistent", "x", "y")


def test_registry_keys_stable():
    """Lock in the three prompt names — papers will cite them."""
    assert set(PROMPT_REGISTRY.keys()) == {
        "v1_naive", "v2_constrained", "v3_grounded",
    }
