"""
test_aggregator.py — Unit tests for aggregator.py.

These keep the published-summary numbers honest. If they fail, the paper's
headline metric is wrong.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from aggregator import aggregate, aggregate_rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    keys = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _row(**kwargs) -> dict:
    base = {
        "id": "n1",
        "name": "Acme",
        "category": "fintech",
        "difficulty": "easy",
        "trap_type": "",
        "model": "gpt-5",
        "prompt_version": "v2_constrained",
        "verdict": "safe",
        "ground_truth_status": "clear",
        "correctness": "correct",
        "confidence": "80",
        "hallucinated_evidence": "false",
        "n_cited_marks": "0",
        "n_hallucinated": "0",
        "response_length": "100",
        "response_time_ms": "1200",
        "input_tokens": "120",
        "output_tokens": "200",
        "cost_estimated": "0.001",
        "parse_error": "",
        "timestamp_utc": "2026-05-16T00:00:00+00:00",
    }
    base.update({k: str(v) for k, v in kwargs.items()})
    return base


def test_aggregate_rows_empty():
    assert aggregate_rows([]) == {"n": 0}


def test_aggregate_rows_perfect_score():
    rows = [_row(correctness="correct") for _ in range(10)]
    summary = aggregate_rows(rows)
    assert summary["n"] == 10
    assert summary["accuracy"] == 1.0
    assert summary["false_negative_rate"] is None  # no risky-truth rows
    assert summary["hallucination_rate"] == 0.0


def test_aggregate_false_negative_rate():
    """5 risky-truth rows, 2 of which the model called 'safe' → FNR = 2/5."""
    rows = (
        [_row(ground_truth_status="high_conflict", correctness="correct") for _ in range(3)]
        + [_row(ground_truth_status="high_conflict",
                 verdict="safe", correctness="false_negative") for _ in range(2)]
    )
    summary = aggregate_rows(rows)
    assert summary["false_negative_rate"] == pytest.approx(2 / 5)


def test_aggregate_false_positive_rate():
    """4 clear-truth rows, 1 falsely called risky → FPR = 1/4."""
    rows = (
        [_row(ground_truth_status="clear", correctness="correct") for _ in range(3)]
        + [_row(ground_truth_status="clear",
                 verdict="risky", correctness="false_positive")]
    )
    summary = aggregate_rows(rows)
    assert summary["false_positive_rate"] == pytest.approx(1 / 4)


def test_aggregate_hallucination_rate():
    rows = [
        _row(hallucinated_evidence="false"),
        _row(hallucinated_evidence="false"),
        _row(hallucinated_evidence="true"),
        _row(hallucinated_evidence="true"),
    ]
    summary = aggregate_rows(rows)
    assert summary["hallucination_rate"] == 0.5


def test_aggregate_per_model_split(tmp_path: Path):
    csv_path = tmp_path / "results.csv"
    rows = [
        _row(model="gpt-5", correctness="correct"),
        _row(model="gpt-5", correctness="false_negative",
              ground_truth_status="high_conflict", verdict="safe"),
        _row(model="claude-4.7", correctness="correct"),
        _row(model="claude-4.7", correctness="correct"),
    ]
    _write_csv(csv_path, rows)

    summary = aggregate(csv_path)
    assert set(summary["models"].keys()) == {"gpt-5", "claude-4.7"}
    assert summary["models"]["gpt-5"]["n"] == 2
    assert summary["models"]["claude-4.7"]["n"] == 2
    assert summary["models"]["claude-4.7"]["accuracy"] == 1.0
    assert summary["models"]["gpt-5"]["accuracy"] == 0.5


def test_aggregate_by_trap_type(tmp_path: Path):
    csv_path = tmp_path / "results.csv"
    rows = [
        _row(trap_type="phonetic_neighbor_famous", correctness="false_negative",
              ground_truth_status="high_conflict", verdict="safe"),
        _row(trap_type="phonetic_neighbor_famous", correctness="correct",
              ground_truth_status="high_conflict", verdict="risky"),
        _row(trap_type="generic_overreach", correctness="correct"),
    ]
    _write_csv(csv_path, rows)

    summary = aggregate(csv_path)
    assert "phonetic_neighbor_famous" in summary["by_trap_type"]
    assert "generic_overreach" in summary["by_trap_type"]
    # phonetic_neighbor_famous has 2 rows for gpt-5, one FN
    phonetic = summary["by_trap_type"]["phonetic_neighbor_famous"]["gpt-5"]
    assert phonetic["n"] == 2
    assert phonetic["accuracy"] == 0.5


def test_aggregate_total_cost_sum(tmp_path: Path):
    csv_path = tmp_path / "results.csv"
    rows = [
        _row(cost_estimated="0.0015"),
        _row(cost_estimated="0.0025"),
        _row(cost_estimated="0.0010"),
    ]
    _write_csv(csv_path, rows)
    summary = aggregate(csv_path)
    cost = summary["models"]["gpt-5"]["total_cost_usd"]
    assert cost == pytest.approx(0.005)
