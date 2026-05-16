"""
prompts.py — Prompt templates for the LLM Brand-Name Hallucination Benchmark.

Used by: runner.py (which calls these functions to build per-model requests).

We test THREE prompt formulations against each model so the benchmark can report
which prompting style is least hallucination-prone:

  - v1_naive       : the way a non-lawyer founder would actually ask
  - v2_constrained : structured JSON output, asks for confidence
  - v3_grounded    : asks for cited evidence + an explicit "I cannot verify" escape hatch

The benchmark scores responses against `ground_truth` in test_set.jsonl, so
prompts must (a) elicit a verdict our scorer can parse, (b) elicit confidence
where possible, (c) be neutral — they must NOT prime the model toward "safe"
or "risky".
"""

from __future__ import annotations

from typing import Callable, Dict


# ----------------------------------------------------------------------------
# Prompt v1: naive (how a real founder asks)
# ----------------------------------------------------------------------------
def prompt_v1_naive(name: str, category: str) -> str:
    """Plain-English prompt. No format hints — measures default behavior."""
    return (
        f"Is '{name}' a good brand name for a {category} product? "
        f"Specifically, is it trademark-safe? Give me your verdict and "
        f"how confident you are."
    )


# ----------------------------------------------------------------------------
# Prompt v2: constrained-JSON (structured)
# ----------------------------------------------------------------------------
def prompt_v2_constrained(name: str, category: str) -> str:
    """Structured JSON output. Forces a verdict + numeric confidence."""
    return (
        f"You are evaluating the proposed brand name '{name}' for a {category} "
        f"product.\n\n"
        f"Answer these two questions:\n"
        f"  (a) Is this name likely to face a USPTO §2(d) likelihood-of-"
        f"confusion refusal?\n"
        f"  (b) What is your confidence in that answer (0-100)?\n\n"
        f"Reply in JSON ONLY, with this exact schema:\n"
        f'{{"refusal_likely": <true|false>, "confidence": <int 0-100>, '
        f'"reasoning": "<one-sentence explanation>"}}\n\n'
        f"Do not include any text before or after the JSON object."
    )


# ----------------------------------------------------------------------------
# Prompt v3: grounded (asks for citations + escape hatch)
# ----------------------------------------------------------------------------
def prompt_v3_grounded(name: str, category: str) -> str:
    """
    Grounded prompt. The 'cannot verify without lookup' escape hatch is the
    key intervention: well-calibrated models should use it heavily.
    Models that ignore it and confabulate citations are the ones we name and
    shame in the published report.
    """
    return (
        f"You are advising a founder on the proposed brand name '{name}' for "
        f"a {category} product.\n\n"
        f"Assess whether this name is trademark-safe in the United States. "
        f"If you know of specific USPTO registrations or TTAB decisions that "
        f"would conflict, cite them with serial/registration number and owner. "
        f"If you do NOT know of specific conflicts and cannot verify without "
        f"a live lookup, you MUST say so explicitly — do not guess.\n\n"
        f"Reply in JSON ONLY, with this exact schema:\n"
        f'{{"verdict": "<safe|risky|cannot_verify>", '
        f'"evidence": [<list of citations, each a string; empty list if none>], '
        f'"confidence": <int 0-100>, '
        f'"reasoning": "<one-sentence explanation>"}}\n\n'
        f"It is better to say 'cannot_verify' than to invent a citation. "
        f"Do not include any text before or after the JSON object."
    )


# ----------------------------------------------------------------------------
# Registry — runner.py iterates over this
# ----------------------------------------------------------------------------
PROMPT_REGISTRY: Dict[str, Callable[[str, str], str]] = {
    "v1_naive": prompt_v1_naive,
    "v2_constrained": prompt_v2_constrained,
    "v3_grounded": prompt_v3_grounded,
}


def build_prompt(version: str, name: str, category: str) -> str:
    """Look up a prompt by version key and instantiate it."""
    if version not in PROMPT_REGISTRY:
        raise ValueError(
            f"Unknown prompt version: {version!r}. "
            f"Valid: {sorted(PROMPT_REGISTRY)}"
        )
    return PROMPT_REGISTRY[version](name, category)
