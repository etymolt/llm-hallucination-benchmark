"""
scoring.py — Scoring rubric for LLM responses.

Used by: runner.py (per-response scoring) and tests/test_scoring.py.

Given an LLM's raw text response, the prompt version that elicited it, and the
test-set ground truth, produce a structured `ScoredResponse` with:

  - verdict          : safe | risky | cannot_verify | unparseable
  - correctness      : correct | false_positive | false_negative | hedge | unparseable
  - hallucinated     : did the model invent a TTAB case / USPTO reg / owner?
  - confidence       : int 0-100 if the model gave one, else None
  - response_length  : characters
  - cited_marks      : list of strings the model presented as real citations

Hallucination detection (the core contribution of this benchmark):
  We extract anything that LOOKS like a trademark citation from the response —
  USPTO serial/registration numbers, "TTAB" mentions with case numbers,
  ALLCAPS-then-Inc patterns. We then cross-check against
  `ground_truth.known_real_citations` (provided by the test set). Anything
  cited but NOT in the known-real set is flagged as a hallucination.

  This is conservative — we only flag confabulations where the model produced
  a CITATION-SHAPED string. Vague non-citations like "I think there's a
  software company with a similar name" do not count as hallucination here
  (they would just be vague verdicts).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


# ----------------------------------------------------------------------------
# Enums & data model
# ----------------------------------------------------------------------------
class Verdict(str, Enum):
    SAFE = "safe"
    RISKY = "risky"
    CANNOT_VERIFY = "cannot_verify"
    UNPARSEABLE = "unparseable"


class Correctness(str, Enum):
    CORRECT = "correct"
    FALSE_POSITIVE = "false_positive"  # said risky, truth is clear
    FALSE_NEGATIVE = "false_negative"  # said safe, truth is high-conflict
    HEDGE = "hedge"                    # punted with cannot_verify
    UNPARSEABLE = "unparseable"


# Map the ground-truth statuses from test_set.jsonl onto a binary axis.
# 'clear' and 'low_conflict' → considered safe
# 'medium_conflict' → ambiguous (counted as "risky-correct" if model said risky)
# 'high_conflict' → definitely risky
_GROUND_TRUTH_SAFE = {"clear", "low_conflict"}
_GROUND_TRUTH_RISKY = {"medium_conflict", "high_conflict"}


@dataclass
class ScoredResponse:
    # what the LLM said
    verdict: Verdict
    confidence: Optional[int]
    cited_marks: list[str] = field(default_factory=list)

    # how it scored
    correctness: Correctness = Correctness.UNPARSEABLE
    hallucinated_evidence: bool = False
    hallucinated_citations: list[str] = field(default_factory=list)

    # raw signals
    response_length: int = 0
    parse_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["correctness"] = self.correctness.value
        return d


# ----------------------------------------------------------------------------
# Parsing — extract verdict + confidence from raw text
# ----------------------------------------------------------------------------
def _try_parse_json(text: str) -> Optional[dict[str, Any]]:
    """
    Extract the first valid JSON object from text. Handles common LLM patterns:
      - pure JSON
      - JSON wrapped in ```json ... ``` fences
      - JSON preceded/followed by prose
    """
    # strip code fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # try whole-string parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # find the longest balanced {...} substring
    depth = 0
    start = -1
    candidates: list[str] = []
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                candidates.append(text[start : i + 1])
                start = -1
    for cand in sorted(candidates, key=len, reverse=True):
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue

    return None


def _verdict_from_json(payload: dict[str, Any]) -> tuple[Verdict, Optional[int]]:
    """Map a parsed JSON object to (Verdict, confidence)."""
    confidence: Optional[int] = None
    raw_conf = payload.get("confidence")
    if isinstance(raw_conf, (int, float)):
        confidence = max(0, min(100, int(raw_conf)))

    # v2 schema: refusal_likely
    if "refusal_likely" in payload:
        if payload["refusal_likely"] is True:
            return Verdict.RISKY, confidence
        if payload["refusal_likely"] is False:
            return Verdict.SAFE, confidence

    # v3 schema: verdict
    v = payload.get("verdict")
    if isinstance(v, str):
        v_norm = v.strip().lower().replace("-", "_").replace(" ", "_")
        if v_norm in {"safe", "clear", "ok", "likely_safe"}:
            return Verdict.SAFE, confidence
        if v_norm in {"risky", "conflict", "unsafe", "likely_unsafe", "high_risk"}:
            return Verdict.RISKY, confidence
        if v_norm in {"cannot_verify", "unknown", "unsure", "hedge"}:
            return Verdict.CANNOT_VERIFY, confidence

    return Verdict.UNPARSEABLE, confidence


# Patterns for naive-prose verdict detection (prompt v1)
_HEDGE_PATTERNS = [
    r"\bcannot verify\b",
    r"\bunable to\s+(verify|confirm|check)\b",
    r"\bi (?:don'?t|do not) know\b",
    r"\bnot sure\b",
    r"\bwould need to (?:check|search|look up|verify)\b",
    r"\bwithout (?:a|conducting a)? (?:trademark|uspto)\s*(?:search|lookup)\b",
    r"\brecommend (?:a |you )?(?:professional |formal )?(?:trademark )?search\b",
]
_RISKY_PATTERNS = [
    r"\bnot (?:trademark[- ]?safe|safe)\b",
    r"\b(?:likely|potential|possible|may face|could face|risk of)\s+(?:conflict|refusal|confusion|infringement)\b",
    r"\b(?:trademark|tm)\s+(?:conflict|infringement|issue|risk|problem)\b",
    r"\binfring(?:e|ing|ement)\b",
    r"\bconfusingly similar\b",
    r"\§\s*2\(d\)\b",
    r"\bsection\s+2\(d\)\b",
    r"\bavoid (?:this|that) name\b",
    r"\bnot recommend\b",
]
_SAFE_PATTERNS = [
    r"\b(?:trademark[- ]?safe|safe to use|appears safe|likely safe)\b",
    r"\bno (?:obvious |apparent |known )?(?:conflict|conflicts|issues)\b",
    r"\bgood (?:choice|name|brand name)\b",
    r"\bshould be (?:fine|safe|ok)\b",
    r"\bdistinctive (?:and|enough|name)\b",
]


def _verdict_from_prose(text: str) -> tuple[Verdict, Optional[int]]:
    """Naive verdict extraction for prompt v1 responses (no JSON)."""
    lowered = text.lower()

    # Order matters: hedge > risky > safe.
    # A model that says "cannot verify but if I had to guess, safe" should
    # count as hedge — that's the more honest reading and is the behavior we
    # want to reward in the benchmark.
    for pat in _HEDGE_PATTERNS:
        if re.search(pat, lowered):
            return Verdict.CANNOT_VERIFY, _extract_pct_confidence(lowered)

    risky_hits = sum(1 for pat in _RISKY_PATTERNS if re.search(pat, lowered))
    safe_hits = sum(1 for pat in _SAFE_PATTERNS if re.search(pat, lowered))

    if risky_hits > safe_hits:
        return Verdict.RISKY, _extract_pct_confidence(lowered)
    if safe_hits > risky_hits:
        return Verdict.SAFE, _extract_pct_confidence(lowered)
    return Verdict.UNPARSEABLE, _extract_pct_confidence(lowered)


_PCT_RE = re.compile(r"(\d{1,3})\s*%")
_CONF_RE = re.compile(
    r"confidence[^\d]{0,20}(\d{1,3})",
    re.IGNORECASE,
)


def _extract_pct_confidence(text: str) -> Optional[int]:
    """Pull a confidence percentage out of prose, if present."""
    m = _CONF_RE.search(text)
    if m:
        val = int(m.group(1))
        return max(0, min(100, val))
    m = _PCT_RE.search(text)
    if m:
        val = int(m.group(1))
        if 0 <= val <= 100:
            return val
    return None


# ----------------------------------------------------------------------------
# Citation extraction — the hallucination detector
# ----------------------------------------------------------------------------
# A USPTO serial number is 8 digits. A registration number is 7 digits.
# TTAB opinions are cited as "Opposition No. 91234567" or "Cancellation No. 92054321".
_CITATION_PATTERNS = [
    # USPTO serial: 8 digits, often after "Serial No."
    (r"\bserial\s+(?:no\.?|number)\s*:?\s*(\d{8})\b", "serial"),
    # USPTO registration: 7 digits, often after "Reg. No." or "Registration No."
    (r"\breg(?:istration|\.)?\s+(?:no\.?|number)\s*:?\s*(\d{7})\b", "registration"),
    # Bare 7-8 digit numbers near "USPTO" or "trademark"
    (r"\buspto[^.\n]{0,40}?(\d{7,8})\b", "uspto_num"),
    # TTAB opposition / cancellation case numbers
    (r"\b(?:opposition|cancellation|petition)\s+(?:no\.?|number)\s*:?\s*(\d{7,8})\b", "ttab_case"),
    # "TTAB 2019" style year-based citations
    (r"\bttab\s+(\d{4})\b", "ttab_year"),
    # ALLCAPS, Inc. — "ACME, Inc.", "FOOBAR Corp.", etc.
    (r"\b([A-Z][A-Z0-9&'\-]{2,}(?:\s+[A-Z][A-Z0-9&'\-]+)*)\s*,?\s*(?:Inc|LLC|Corp|Ltd|Co)\.?\b", "owner"),
]


def extract_citations(text: str) -> list[str]:
    """
    Pull citation-shaped strings out of the response.

    Returns a list of normalized citation strings. Used both for
    hallucination detection and for the cited_marks column in results.csv.

    Normalized form examples:
      "SERIAL:88712345"
      "REG:6234567"
      "TTAB_CASE:91254321"
      "OWNER:ACME, Inc."
    """
    out: list[str] = []
    for pat, kind in _CITATION_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            captured = m.group(1)
            if kind == "owner":
                # Skip a small set of generic / common false positives.
                if captured.upper() in {"USPTO", "TTAB", "LLC", "INC", "TM", "FAQ", "EU", "US", "USA", "URL"}:
                    continue
                out.append(f"OWNER:{captured}")
            else:
                out.append(f"{kind.upper()}:{captured}")
    # de-duplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for c in out:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    return deduped


def _normalize_known_citation(s: str) -> str:
    """Normalize a known-real citation from the test set for comparison."""
    return re.sub(r"\s+", " ", s.strip().lower())


def detect_hallucinations(
    cited: list[str],
    known_real: list[str],
) -> tuple[bool, list[str]]:
    """
    Return (hallucinated, list_of_hallucinated_citations).

    A citation is considered hallucinated if it does NOT appear in the
    known-real list (as a substring match, case-insensitive). The known-real
    list comes from the test-set ground truth and is curated by the test-set
    builder agent.
    """
    if not cited:
        return False, []

    known_norm = [_normalize_known_citation(k) for k in known_real if k]
    hallucinated: list[str] = []
    for c in cited:
        # The citation we extracted has a TYPE: prefix; we compare the value
        # part against known-real. We're conservative: any substring overlap
        # with a known citation counts as "matched."
        try:
            _, value = c.split(":", 1)
        except ValueError:
            value = c
        value_norm = _normalize_known_citation(value)
        if not any(value_norm in k or k in value_norm for k in known_norm):
            hallucinated.append(c)
    return bool(hallucinated), hallucinated


def _known_citations_from_ground_truth(gt: dict[str, Any]) -> list[str]:
    """
    Derive the list of known-real citation strings from a ground-truth dict.

    Supports both shapes the test-set builder may produce:

      1. Explicit list:  gt["known_real_citations"] = ["Serial No. ...", ...]
      2. Structured primary_conflict (the current test_set.jsonl shape):
            gt["primary_conflict"] = {
                "registration_no": "5829362",
                "owner": "OpenAI OPCO, LLC",
                "mark": "OPENAI",
                ...
            }
         plus optional gt["secondary_conflicts"] (same shape, list).

    Either or both may be present. We merge them into one flat list of
    strings used for substring matching against citation-shaped tokens the
    LLM emits in its response.
    """
    out: list[str] = []
    explicit = gt.get("known_real_citations")
    if isinstance(explicit, list):
        out.extend(str(x) for x in explicit if x)

    def _expand(conflict: dict[str, Any]) -> None:
        if not isinstance(conflict, dict):
            return
        for k in ("registration_no", "serial_no", "mark", "owner",
                  "ttab_case_no", "opposition_no"):
            v = conflict.get(k)
            if v and isinstance(v, str):
                # Skip placeholders the builder agent may emit like
                # "[VERIFY: REG_NO]" or empty-shaped strings.
                if v.startswith("[") and v.endswith("]"):
                    continue
                out.append(v)

    _expand(gt.get("primary_conflict") or {})
    secondaries = gt.get("secondary_conflicts") or []
    if isinstance(secondaries, list):
        for c in secondaries:
            _expand(c)

    return out


# ----------------------------------------------------------------------------
# Correctness — map (verdict, ground_truth) → Correctness
# ----------------------------------------------------------------------------
def score_correctness(verdict: Verdict, ground_truth_status: str) -> Correctness:
    """
    The asymmetric scoring matrix:

                          truth:safe        truth:risky
      verdict:safe        CORRECT           FALSE_NEGATIVE  (the dangerous failure)
      verdict:risky       FALSE_POSITIVE    CORRECT
      verdict:hedge       HEDGE             HEDGE
      verdict:unparseable UNPARSEABLE       UNPARSEABLE

    FN is the failure mode that ships a lawsuit. FP is the failure mode that
    rejects a usable name. Both are counted, but the paper will highlight FN.
    """
    truth = ground_truth_status.strip().lower()

    if verdict == Verdict.UNPARSEABLE:
        return Correctness.UNPARSEABLE
    if verdict == Verdict.CANNOT_VERIFY:
        return Correctness.HEDGE

    if truth in _GROUND_TRUTH_SAFE:
        if verdict == Verdict.SAFE:
            return Correctness.CORRECT
        if verdict == Verdict.RISKY:
            return Correctness.FALSE_POSITIVE
    elif truth in _GROUND_TRUTH_RISKY:
        if verdict == Verdict.RISKY:
            return Correctness.CORRECT
        if verdict == Verdict.SAFE:
            return Correctness.FALSE_NEGATIVE
    # Unknown ground-truth label — caller should validate test set upstream.
    return Correctness.UNPARSEABLE


# ----------------------------------------------------------------------------
# Top-level entry point
# ----------------------------------------------------------------------------
def score_response(
    response_text: str,
    prompt_version: str,
    ground_truth: dict[str, Any],
) -> ScoredResponse:
    """
    Score one (raw response text) against (ground truth from the test set).

    Args:
      response_text   : the LLM's raw text output
      prompt_version  : "v1_naive" | "v2_constrained" | "v3_grounded"
      ground_truth    : dict from test_set.jsonl with at least:
                          - "trademark_status": str (clear|low_conflict|...|high_conflict)
                          - "known_real_citations": list[str] (optional, default [])

    Returns:
      ScoredResponse
    """
    text = response_text or ""
    length = len(text)

    # 1. Verdict + confidence
    if prompt_version in {"v2_constrained", "v3_grounded"}:
        payload = _try_parse_json(text)
        if payload is not None:
            verdict, confidence = _verdict_from_json(payload)
            parse_error = None
        else:
            verdict, confidence = _verdict_from_prose(text)
            parse_error = "json_parse_failed_fallback_to_prose"
    else:
        verdict, confidence = _verdict_from_prose(text)
        parse_error = None

    # 2. Citation extraction + hallucination check
    cited = extract_citations(text)
    known_real = _known_citations_from_ground_truth(ground_truth)
    hallucinated, hallucinated_citations = detect_hallucinations(cited, known_real)

    # 3. Correctness
    truth_status = ground_truth.get("trademark_status", "")
    correctness = score_correctness(verdict, truth_status)

    return ScoredResponse(
        verdict=verdict,
        confidence=confidence,
        cited_marks=cited,
        correctness=correctness,
        hallucinated_evidence=hallucinated,
        hallucinated_citations=hallucinated_citations,
        response_length=length,
        parse_error=parse_error,
    )


# ----------------------------------------------------------------------------
# Calibration — Brier score over a batch
# ----------------------------------------------------------------------------
def brier_score(pairs: list[tuple[Optional[int], bool]]) -> Optional[float]:
    """
    Compute Brier score across (confidence_pct, was_correct) pairs.
    Skips pairs where confidence is None. Returns None if no valid pairs.

    Brier = mean((p - outcome)^2) where p = confidence/100.
    Lower is better; perfect calibration = 0.
    """
    valid = [(c / 100.0, 1.0 if ok else 0.0) for c, ok in pairs if c is not None]
    if not valid:
        return None
    return sum((p - o) ** 2 for p, o in valid) / len(valid)
