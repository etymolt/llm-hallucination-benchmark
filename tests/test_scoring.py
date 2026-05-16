"""
test_scoring.py — Unit tests for scoring.py.

These tests are the harness the founder runs BEFORE burning API credits.
If any of these fail, the benchmark numbers will be garbage.

Run:  pytest tests/ -v
"""

from __future__ import annotations

import pytest

from scoring import (
    Correctness,
    Verdict,
    brier_score,
    detect_hallucinations,
    extract_citations,
    score_correctness,
    score_response,
)


# ----------------------------------------------------------------------------
# Ground-truth fixtures
# ----------------------------------------------------------------------------
GT_CLEAR = {
    "trademark_status": "clear",
    "known_real_citations": [],
}
GT_HIGH_CONFLICT = {
    "trademark_status": "high_conflict",
    "known_real_citations": [
        "Serial No. 88712345 — ACME Robotics, Inc.",
        "Reg. No. 6234567",
    ],
}
GT_LOW_CONFLICT = {
    "trademark_status": "low_conflict",
    "known_real_citations": [],
}
GT_MEDIUM_CONFLICT = {
    "trademark_status": "medium_conflict",
    "known_real_citations": [],
}


# ============================================================================
# Test case 1: HIT (correct safe call on a clear name)
# ============================================================================
def test_correct_safe_call_on_clear_name():
    response = (
        '{"refusal_likely": false, "confidence": 85, '
        '"reasoning": "No obvious conflicts; distinctive."}'
    )
    scored = score_response(response, "v2_constrained", GT_CLEAR)
    assert scored.verdict == Verdict.SAFE
    assert scored.correctness == Correctness.CORRECT
    assert scored.confidence == 85
    assert scored.hallucinated_evidence is False


def test_correct_risky_call_on_high_conflict():
    """A risky verdict on a high-conflict name is CORRECT."""
    response = (
        '{"refusal_likely": true, "confidence": 90, '
        '"reasoning": "Highly similar to a registered mark."}'
    )
    scored = score_response(response, "v2_constrained", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.RISKY
    assert scored.correctness == Correctness.CORRECT


# ============================================================================
# Test case 2: FALSE NEGATIVE (the dangerous failure)
# ============================================================================
def test_false_negative_safe_call_on_high_conflict():
    response = (
        '{"refusal_likely": false, "confidence": 70, '
        '"reasoning": "Looks fine to me."}'
    )
    scored = score_response(response, "v2_constrained", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.SAFE
    assert scored.correctness == Correctness.FALSE_NEGATIVE


def test_false_negative_prose():
    """v1 prose response with a confident 'safe' verdict on a risky name."""
    response = (
        "This name looks trademark-safe — distinctive enough, and I don't see "
        "any obvious conflicts. Good choice."
    )
    scored = score_response(response, "v1_naive", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.SAFE
    assert scored.correctness == Correctness.FALSE_NEGATIVE


# ============================================================================
# Test case 3: FALSE POSITIVE (annoying but safe failure)
# ============================================================================
def test_false_positive_risky_call_on_clear_name():
    response = (
        '{"refusal_likely": true, "confidence": 60, '
        '"reasoning": "Might face §2(d) issues."}'
    )
    scored = score_response(response, "v2_constrained", GT_CLEAR)
    assert scored.verdict == Verdict.RISKY
    assert scored.correctness == Correctness.FALSE_POSITIVE


# ============================================================================
# Test case 4: HEDGE (model said "cannot verify")
# ============================================================================
def test_hedge_via_v3():
    response = (
        '{"verdict": "cannot_verify", "evidence": [], "confidence": 30, '
        '"reasoning": "Need a live USPTO lookup to be sure."}'
    )
    scored = score_response(response, "v3_grounded", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.CANNOT_VERIFY
    assert scored.correctness == Correctness.HEDGE


def test_hedge_via_prose():
    response = (
        "I cannot verify this without conducting a formal trademark search. "
        "I'd recommend running a professional clearance search before "
        "committing."
    )
    scored = score_response(response, "v1_naive", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.CANNOT_VERIFY
    assert scored.correctness == Correctness.HEDGE


# ============================================================================
# Test case 5: HALLUCINATED EVIDENCE
# ============================================================================
def test_hallucinated_uspto_reg_number():
    response = (
        '{"verdict": "risky", "evidence": ["Reg. No. 9999999 — FAKEMARK, Inc."], '
        '"confidence": 80, "reasoning": "Conflicts with the cited mark."}'
    )
    scored = score_response(response, "v3_grounded", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.RISKY
    # 9999999 is not in known_real_citations, so it's hallucinated.
    assert scored.hallucinated_evidence is True
    assert any("9999999" in c for c in scored.hallucinated_citations)


def test_hallucinated_ttab_case():
    response = (
        '{"verdict": "risky", "evidence": ["TTAB Opposition No. 91999888"], '
        '"confidence": 75, "reasoning": "Cited TTAB case."}'
    )
    scored = score_response(response, "v3_grounded", GT_CLEAR)
    assert scored.hallucinated_evidence is True
    # The fake TTAB case number should appear in the hallucinated citations list.
    found = any("91999888" in c for c in scored.hallucinated_citations)
    assert found, f"expected fake TTAB case in {scored.hallucinated_citations}"


def test_real_citation_is_not_hallucinated():
    """If the LLM cites a citation actually in the known-real list, no hallucination."""
    response = (
        '{"verdict": "risky", '
        '"evidence": ["Serial No. 88712345 — ACME Robotics, Inc."], '
        '"confidence": 90, "reasoning": "Direct conflict."}'
    )
    scored = score_response(response, "v3_grounded", GT_HIGH_CONFLICT)
    assert scored.hallucinated_evidence is False
    assert scored.correctness == Correctness.CORRECT


# ============================================================================
# Test case 6: UNPARSEABLE
# ============================================================================
def test_unparseable_response():
    response = "I'm sorry, I cannot help with that request."
    scored = score_response(response, "v2_constrained", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.UNPARSEABLE
    assert scored.correctness == Correctness.UNPARSEABLE


def test_empty_response():
    scored = score_response("", "v2_constrained", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.UNPARSEABLE
    assert scored.correctness == Correctness.UNPARSEABLE
    assert scored.response_length == 0


# ============================================================================
# JSON parser quirks
# ============================================================================
def test_json_wrapped_in_code_fence():
    """LLMs frequently wrap JSON in ```json ... ``` fences."""
    response = (
        "Here's my analysis:\n\n```json\n"
        '{"refusal_likely": true, "confidence": 80, "reasoning": "Conflict."}\n'
        "```"
    )
    scored = score_response(response, "v2_constrained", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.RISKY
    assert scored.confidence == 80


def test_json_with_prose_preamble():
    response = (
        "Let me think about this. After consideration:\n"
        '{"refusal_likely": false, "confidence": 65, "reasoning": "OK"}\n'
        "Hope this helps!"
    )
    scored = score_response(response, "v2_constrained", GT_CLEAR)
    assert scored.verdict == Verdict.SAFE
    assert scored.correctness == Correctness.CORRECT


def test_json_fallback_to_prose_extraction():
    """If JSON parse fails on a v2 prompt, fall back to prose extraction."""
    response = "I think this name is likely safe with no obvious conflicts."
    scored = score_response(response, "v2_constrained", GT_CLEAR)
    assert scored.verdict == Verdict.SAFE
    assert scored.parse_error == "json_parse_failed_fallback_to_prose"


# ============================================================================
# Citation extraction primitives
# ============================================================================
def test_extract_serial_number():
    cits = extract_citations(
        "There's a conflict with Serial No. 88712345 owned by ACME Corp."
    )
    assert any("88712345" in c for c in cits)


def test_extract_registration_number():
    cits = extract_citations(
        "See Reg. No. 6234567 for the relevant registration."
    )
    assert any("6234567" in c for c in cits)


def test_extract_ttab_case():
    cits = extract_citations(
        "In TTAB Opposition No. 91234567, the board held..."
    )
    assert any("91234567" in c for c in cits)


def test_extract_owner_allcaps():
    cits = extract_citations(
        "The mark is owned by ACME ROBOTICS, Inc. of Delaware."
    )
    assert any("ACME ROBOTICS" in c for c in cits)


def test_extract_skips_common_acronyms():
    """USPTO, TTAB, LLC should not trigger owner-name extraction."""
    cits = extract_citations(
        "The USPTO refused the application. LLC and Inc. are common suffixes."
    )
    # No citations should be USPTO / LLC etc.
    for c in cits:
        if c.startswith("OWNER:"):
            owner = c.split(":", 1)[1]
            assert owner.upper() not in {"USPTO", "LLC", "INC", "TTAB"}


def test_detect_hallucinations_distinguishes_real_vs_fake():
    """Mixed list — only the fake one should be flagged."""
    cited = ["SERIAL:88712345", "SERIAL:99999999"]
    known_real = ["Serial No. 88712345 — ACME Robotics, Inc."]
    is_hallu, hallu_list = detect_hallucinations(cited, known_real)
    assert is_hallu is True
    assert "SERIAL:99999999" in hallu_list
    assert "SERIAL:88712345" not in hallu_list


def test_detect_hallucinations_empty_citations_not_hallucinated():
    is_hallu, hallu_list = detect_hallucinations([], ["whatever"])
    assert is_hallu is False
    assert hallu_list == []


# ============================================================================
# Score correctness matrix
# ============================================================================
@pytest.mark.parametrize("verdict,truth,expected", [
    (Verdict.SAFE, "clear", Correctness.CORRECT),
    (Verdict.SAFE, "low_conflict", Correctness.CORRECT),
    (Verdict.SAFE, "high_conflict", Correctness.FALSE_NEGATIVE),
    (Verdict.SAFE, "medium_conflict", Correctness.FALSE_NEGATIVE),
    (Verdict.RISKY, "clear", Correctness.FALSE_POSITIVE),
    (Verdict.RISKY, "low_conflict", Correctness.FALSE_POSITIVE),
    (Verdict.RISKY, "high_conflict", Correctness.CORRECT),
    (Verdict.RISKY, "medium_conflict", Correctness.CORRECT),
    (Verdict.CANNOT_VERIFY, "clear", Correctness.HEDGE),
    (Verdict.CANNOT_VERIFY, "high_conflict", Correctness.HEDGE),
    (Verdict.UNPARSEABLE, "clear", Correctness.UNPARSEABLE),
])
def test_correctness_matrix(verdict, truth, expected):
    assert score_correctness(verdict, truth) == expected


# ============================================================================
# Brier score
# ============================================================================
def test_brier_perfect_confidence_perfect_outcome():
    # 100% confident, all correct → Brier = 0
    pairs = [(100, True), (100, True), (100, True)]
    assert brier_score(pairs) == pytest.approx(0.0)


def test_brier_worst_case():
    # 100% confident, all wrong → Brier = 1
    pairs = [(100, False), (100, False)]
    assert brier_score(pairs) == pytest.approx(1.0)


def test_brier_well_calibrated_50_50():
    # 50% confidence, half right → Brier = 0.25
    pairs = [(50, True), (50, False)]
    assert brier_score(pairs) == pytest.approx(0.25)


def test_brier_skips_none_confidence():
    pairs = [(None, True), (80, True)]
    # Only the (80, True) pair counts: (0.8 - 1)^2 = 0.04
    assert brier_score(pairs) == pytest.approx(0.04)


def test_brier_returns_none_if_no_valid_pairs():
    assert brier_score([(None, True), (None, False)]) is None
    assert brier_score([]) is None


# ============================================================================
# v3 grounded prompt — the "I cannot verify" escape hatch
# ============================================================================
def test_v3_cannot_verify_with_empty_evidence_is_a_hedge():
    response = (
        '{"verdict": "cannot_verify", "evidence": [], "confidence": 20, '
        '"reasoning": "I cannot confirm without USPTO lookup."}'
    )
    scored = score_response(response, "v3_grounded", GT_HIGH_CONFLICT)
    assert scored.verdict == Verdict.CANNOT_VERIFY
    assert scored.correctness == Correctness.HEDGE
    assert scored.hallucinated_evidence is False


def test_v3_safe_with_no_evidence_and_no_known_citations():
    """If the model says safe and cites nothing and the truth is clear, that's a HIT."""
    response = (
        '{"verdict": "safe", "evidence": [], "confidence": 80, '
        '"reasoning": "Distinctive."}'
    )
    scored = score_response(response, "v3_grounded", GT_CLEAR)
    assert scored.verdict == Verdict.SAFE
    assert scored.correctness == Correctness.CORRECT
    assert scored.hallucinated_evidence is False


# ============================================================================
# Ground-truth shape compatibility — the real test_set.jsonl uses
# `primary_conflict` rather than an explicit `known_real_citations` list.
# ============================================================================
def test_real_citation_match_via_primary_conflict():
    """The current test_set.jsonl shape — registration_no inside primary_conflict."""
    gt = {
        "trademark_status": "high_conflict",
        "primary_conflict": {
            "registration_no": "5829362",
            "mark": "OPENAI",
            "owner": "OpenAI OPCO, LLC",
        },
    }
    response = (
        '{"verdict": "risky", '
        '"evidence": ["Reg. No. 5829362 — OpenAI OPCO, LLC"], '
        '"confidence": 95, "reasoning": "Direct conflict."}'
    )
    scored = score_response(response, "v3_grounded", gt)
    assert scored.hallucinated_evidence is False
    assert scored.correctness == Correctness.CORRECT


def test_fake_citation_against_primary_conflict_is_hallucinated():
    gt = {
        "trademark_status": "high_conflict",
        "primary_conflict": {
            "registration_no": "5829362",
            "mark": "OPENAI",
        },
    }
    # Model invents a different reg number
    response = (
        '{"verdict": "risky", '
        '"evidence": ["Reg. No. 7777777 — OpenAI Corp."], '
        '"confidence": 90, "reasoning": "Bogus."}'
    )
    scored = score_response(response, "v3_grounded", gt)
    assert scored.hallucinated_evidence is True


def test_placeholder_verify_strings_are_not_used_as_known_citations():
    """Test-set builder may emit '[VERIFY: REG_NO]' for unverified rows; those must NOT
    count as known-real citations, or every hallucination would pass."""
    from scoring import _known_citations_from_ground_truth
    gt = {
        "primary_conflict": {
            "registration_no": "[VERIFY: REG_NO]",
            "mark": "ANTHROPIC",
        },
    }
    known = _known_citations_from_ground_truth(gt)
    assert "[VERIFY: REG_NO]" not in known
    assert "ANTHROPIC" in known  # real mark name should still be included


def test_secondary_conflicts_contribute_to_known_citations():
    from scoring import _known_citations_from_ground_truth
    gt = {
        "primary_conflict": {"registration_no": "1111111", "mark": "PRIMARY"},
        "secondary_conflicts": [
            {"registration_no": "2222222", "mark": "SECONDARY"},
        ],
    }
    known = _known_citations_from_ground_truth(gt)
    assert "1111111" in known
    assert "2222222" in known
    assert "PRIMARY" in known
    assert "SECONDARY" in known
