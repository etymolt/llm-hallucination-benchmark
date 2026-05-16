"""
aggregator.py — Build summary.json from results.csv.

Used by: the founder (CLI), the Makefile (`make aggregate`), and the article
publishing pipeline (`make publish`).

Reads results.csv produced by runner.py. Produces summary.json with per-model,
per-category, per-difficulty, and per-trap-type breakdowns. This is the file
that gets cited in the paper and on the website.

Usage:
  python aggregator.py --results results/results.csv --output results/summary.json
  python aggregator.py             # uses defaults: results/results.csv → results/summary.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import orjson

from scoring import brier_score


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _is_correct(correctness: str) -> bool:
    return correctness == "correct"


def _to_int(s: str | None) -> Optional[int]:
    if s is None or s == "":
        return None
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def _to_float(s: str | None) -> Optional[float]:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


# ----------------------------------------------------------------------------
# Aggregation primitive — one bucket of rows
# ----------------------------------------------------------------------------
def aggregate_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    """
    Compute summary statistics for a list of result rows.

    Used recursively: top-level per-model, then nested per-category etc.
    """
    n = len(rows)
    if n == 0:
        return {"n": 0}

    n_correct = sum(1 for r in rows if _is_correct(r["correctness"]))
    n_fn = sum(1 for r in rows if r["correctness"] == "false_negative")
    n_fp = sum(1 for r in rows if r["correctness"] == "false_positive")
    n_hedge = sum(1 for r in rows if r["correctness"] == "hedge")
    n_unparseable = sum(1 for r in rows if r["correctness"] == "unparseable")
    n_hallu = sum(1 for r in rows if r.get("hallucinated_evidence", "false") == "true")

    n_risky_truth = sum(
        1 for r in rows
        if r["ground_truth_status"] in {"medium_conflict", "high_conflict"}
    )
    n_safe_truth = sum(
        1 for r in rows
        if r["ground_truth_status"] in {"clear", "low_conflict"}
    )

    # Confidence calibration (Brier score on binary correctness)
    conf_pairs: list[tuple[Optional[int], bool]] = []
    for r in rows:
        c = _to_int(r.get("confidence"))
        # Skip hedges & unparseables from calibration — they're not binary outcomes
        if r["correctness"] in {"hedge", "unparseable"}:
            continue
        conf_pairs.append((c, _is_correct(r["correctness"])))
    brier = brier_score(conf_pairs)

    latencies = [v for v in (_to_int(r.get("response_time_ms")) for r in rows) if v is not None]
    costs = [v for v in (_to_float(r.get("cost_estimated")) for r in rows) if v is not None]

    return {
        "n": n,
        "accuracy": n_correct / n,
        "false_negative_rate": (n_fn / n_risky_truth) if n_risky_truth else None,
        "false_positive_rate": (n_fp / n_safe_truth) if n_safe_truth else None,
        "hedge_rate": n_hedge / n,
        "unparseable_rate": n_unparseable / n,
        "hallucination_rate": n_hallu / n,
        "confidence_brier_score": brier,
        "mean_response_time_ms": int(statistics.mean(latencies)) if latencies else None,
        "p95_response_time_ms": int(_percentile(latencies, 95)) if latencies else None,
        "total_cost_usd": sum(costs) if costs else 0.0,
        "counts": {
            "correct": n_correct,
            "false_negative": n_fn,
            "false_positive": n_fp,
            "hedge": n_hedge,
            "unparseable": n_unparseable,
            "hallucinated": n_hallu,
            "n_risky_truth": n_risky_truth,
            "n_safe_truth": n_safe_truth,
        },
    }


def _percentile(values: list[int | float], pct: float) -> float:
    """Simple non-interpolating percentile. Good enough for a benchmark."""
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round(pct / 100.0 * (len(s) - 1)))))
    return s[k]


# ----------------------------------------------------------------------------
# Top-level aggregation
# ----------------------------------------------------------------------------
def aggregate(results_csv: Path) -> dict[str, Any]:
    """Build the full summary dict from results.csv."""
    with results_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = list(reader)

    if not rows:
        return {
            "models": {},
            "by_trap_type": {},
            "total_rows": 0,
            "warning": "results.csv is empty",
        }

    # by_model
    by_model_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_model_rows[r["model"]].append(r)

    models_summary: dict[str, Any] = {}
    for model, mrows in by_model_rows.items():
        summary = aggregate_rows(mrows)

        # by_category
        by_cat_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
        for r in mrows:
            by_cat_rows[r["category"]].append(r)
        summary["by_category"] = {
            cat: aggregate_rows(rs) for cat, rs in sorted(by_cat_rows.items())
        }

        # by_difficulty
        by_diff_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
        for r in mrows:
            d = r.get("difficulty") or "unknown"
            by_diff_rows[d].append(r)
        summary["by_difficulty"] = {
            d: aggregate_rows(rs) for d, rs in sorted(by_diff_rows.items())
        }

        # by_prompt_version
        by_pv_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
        for r in mrows:
            by_pv_rows[r["prompt_version"]].append(r)
        summary["by_prompt_version"] = {
            pv: aggregate_rows(rs) for pv, rs in sorted(by_pv_rows.items())
        }

        models_summary[model] = summary

    # by_trap_type (model × trap_type, transposed)
    trap_types: set[str] = set()
    for r in rows:
        tt = r.get("trap_type") or ""
        if tt:
            trap_types.add(tt)
    by_trap_type: dict[str, dict[str, Any]] = {}
    for tt in sorted(trap_types):
        per_model: dict[str, Any] = {}
        for model, mrows in by_model_rows.items():
            filtered = [r for r in mrows if r.get("trap_type") == tt]
            if filtered:
                per_model[model] = aggregate_rows(filtered)
        by_trap_type[tt] = per_model

    return {
        "schema_version": "1.0",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "results_csv_sha256": _file_sha256(results_csv),
        "total_rows": len(rows),
        "models": models_summary,
        "by_trap_type": by_trap_type,
    }


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Aggregate results.csv into summary.json.",
    )
    p.add_argument(
        "--results",
        type=Path,
        default=Path("results/results.csv"),
        help="Path to results.csv (default: results/results.csv).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("results/summary.json"),
        help="Path for summary.json (default: results/summary.json).",
    )
    args = p.parse_args(argv)

    if not args.results.exists():
        print(f"[fatal] results.csv not found: {args.results}")
        return 2

    summary = aggregate(args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
    n_models = len(summary.get("models") or {})
    n_rows = summary.get("total_rows", 0)
    print(f"[ok] wrote {args.output} ({n_rows} rows, {n_models} models)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
