"""
runner.py — Main entrypoint for the LLM Brand-Name Hallucination Benchmark.

Used by: the founder (CLI), and the Makefile.

Reads test_set.jsonl, calls each (name, model, prompt_version) tuple, parses
and scores responses, writes results to disk. Resumable: if killed mid-run,
the next invocation skips already-completed pairs by reading the existing
results.csv.

CLI:
  python runner.py \\
    --test-set test_set.jsonl \\
    --models gpt-5 claude-4.7-opus gemini-3-pro llama-4-maverick \\
    --prompts v1_naive v2_constrained v3_grounded \\
    --output-dir results/ \\
    --concurrency 10 \\
    --sample 50           # optional: only N names per model (smoke test)
    --yes-costs           # required if estimated total > $50

Design notes:
  - We use httpx.AsyncClient inside each *_client.py and run a per-model
    asyncio.Semaphore to bound concurrency. asyncio.gather wires it together.
  - Raw responses are saved as JSONL alongside results.csv so re-scoring
    later (if the rubric changes) doesn't require re-paying for API calls.
  - On rate-limit / 5xx, we exponential-backoff up to 5 retries.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

import httpx
import orjson

# Load .env if present — keeps API keys out of shell history
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from clients import ClientResponse, get_client_for
from costs import cost_usd, estimate_total_cost
from prompts import PROMPT_REGISTRY, build_prompt
from scoring import score_response


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------
@dataclass
class TestItem:
    id: str
    name: str
    category: str
    ground_truth: dict[str, Any]   # arbitrary — the scorer reads what it needs
    difficulty: Optional[str] = None
    trap_type: Optional[str] = None

    @classmethod
    def from_jsonl_row(cls, row: dict[str, Any]) -> "TestItem":
        # The test set uses either `difficulty` or `expected_difficulty` —
        # accept both so we don't lock the runner to one builder version.
        difficulty = row.get("difficulty") or row.get("expected_difficulty")
        return cls(
            id=str(row["id"]),
            name=str(row["name"]),
            category=str(row["category"]),
            ground_truth=row.get("ground_truth") or {},
            difficulty=difficulty,
            trap_type=row.get("trap_type"),
        )


@dataclass
class Task:
    item: TestItem
    model: str
    prompt_version: str

    @property
    def pair_key(self) -> str:
        """Unique key used for resumability — one row per (id, model, prompt)."""
        return f"{self.item.id}::{self.model}::{self.prompt_version}"


# ----------------------------------------------------------------------------
# I/O helpers
# ----------------------------------------------------------------------------
def load_test_set(path: Path) -> list[TestItem]:
    items: list[TestItem] = []
    with path.open("rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = orjson.loads(line)
            items.append(TestItem.from_jsonl_row(row))
    return items


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_completed_pairs(results_csv: Path) -> set[str]:
    """Return the set of (id, model, prompt) keys already in results.csv."""
    if not results_csv.exists():
        return set()
    done: set[str] = set()
    with results_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row.get('id')}::{row.get('model')}::{row.get('prompt_version')}"
            done.add(key)
    return done


RESULTS_HEADER = [
    "id",
    "name",
    "category",
    "difficulty",
    "trap_type",
    "model",
    "prompt_version",
    "verdict",
    "ground_truth_status",
    "correctness",
    "confidence",
    "hallucinated_evidence",
    "n_cited_marks",
    "n_hallucinated",
    "response_length",
    "response_time_ms",
    "input_tokens",
    "output_tokens",
    "cost_estimated",
    "parse_error",
    "timestamp_utc",
]


def append_result_row(results_csv: Path, row: dict[str, Any]) -> None:
    """Append a single row to results.csv (creates header if file is new)."""
    is_new = not results_csv.exists() or results_csv.stat().st_size == 0
    with results_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_HEADER)
        if is_new:
            writer.writeheader()
        # Whitelist keys so an accidental extra field doesn't blow up the write.
        writer.writerow({k: row.get(k, "") for k in RESULTS_HEADER})


def append_raw_response(raw_jsonl: Path, payload: dict[str, Any]) -> None:
    """Append the raw API response (so we can re-score later without re-paying)."""
    raw_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with raw_jsonl.open("ab") as f:
        f.write(orjson.dumps(payload))
        f.write(b"\n")


# ----------------------------------------------------------------------------
# Retry / backoff
# ----------------------------------------------------------------------------
async def call_with_retry(
    client,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
    max_retries: int = 5,
) -> ClientResponse:
    """
    Call the model with exponential backoff on 429 / 5xx / transient errors.

    Backoff: 1, 2, 4, 8, 16 seconds + jitter. Respects `Retry-After` if the
    server provides one.
    """
    last_exc: Optional[BaseException] = None
    for attempt in range(max_retries):
        try:
            return await client.call(model, prompt, max_tokens=max_tokens, timeout=timeout)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status not in (408, 409, 425, 429, 500, 502, 503, 504):
                raise
            retry_after = exc.response.headers.get("Retry-After")
            if retry_after:
                try:
                    sleep_s = float(retry_after)
                except ValueError:
                    sleep_s = 2 ** attempt
            else:
                sleep_s = 2 ** attempt
            sleep_s += random.uniform(0, 0.5)
            last_exc = exc
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            sleep_s = 2 ** attempt + random.uniform(0, 0.5)
            last_exc = exc
        await asyncio.sleep(sleep_s)
    assert last_exc is not None
    raise last_exc


# ----------------------------------------------------------------------------
# Per-task execution
# ----------------------------------------------------------------------------
async def run_task(
    task: Task,
    client,
    semaphore: asyncio.Semaphore,
    results_csv: Path,
    raw_jsonl: Path,
    max_tokens: int,
    timeout: float,
    file_lock: asyncio.Lock,
) -> Optional[dict[str, Any]]:
    """Run one (item, model, prompt) task and persist the result. Returns the row or None on failure."""
    async with semaphore:
        prompt = build_prompt(task.prompt_version, task.item.name, task.item.category)
        try:
            resp = await call_with_retry(
                client, task.model, prompt,
                max_tokens=max_tokens, timeout=timeout,
            )
        except Exception as exc:
            # Print but do not crash — one task failure doesn't kill the run.
            print(
                f"  [error] {task.pair_key}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return None

        scored = score_response(resp.text, task.prompt_version, task.item.ground_truth)
        cost = cost_usd(task.model, resp.input_tokens, resp.output_tokens)
        truth = task.item.ground_truth.get("trademark_status", "")

        row = {
            "id": task.item.id,
            "name": task.item.name,
            "category": task.item.category,
            "difficulty": task.item.difficulty or "",
            "trap_type": task.item.trap_type or "",
            "model": task.model,
            "prompt_version": task.prompt_version,
            "verdict": scored.verdict.value,
            "ground_truth_status": truth,
            "correctness": scored.correctness.value,
            "confidence": scored.confidence if scored.confidence is not None else "",
            "hallucinated_evidence": "true" if scored.hallucinated_evidence else "false",
            "n_cited_marks": len(scored.cited_marks),
            "n_hallucinated": len(scored.hallucinated_citations),
            "response_length": scored.response_length,
            "response_time_ms": resp.latency_ms,
            "input_tokens": resp.input_tokens,
            "output_tokens": resp.output_tokens,
            "cost_estimated": f"{cost:.6f}",
            "parse_error": scored.parse_error or "",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        raw_payload = {
            "pair_key": task.pair_key,
            "id": task.item.id,
            "model": task.model,
            "prompt_version": task.prompt_version,
            "prompt": prompt,
            "response_text": resp.text,
            "raw_provider_payload": resp.raw,
            "scored": scored.to_dict(),
            "timestamp_utc": row["timestamp_utc"],
        }

        # Serialize writes — CSV and JSONL aren't safe for concurrent appends.
        async with file_lock:
            append_result_row(results_csv, row)
            append_raw_response(raw_jsonl, raw_payload)
        return row


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------
async def run_for_model(
    model: str,
    tasks: list[Task],
    output_dir: Path,
    concurrency: int,
    max_tokens: int,
    timeout: float,
    file_lock: asyncio.Lock,
) -> tuple[int, int]:
    """Run all tasks for one model. Returns (n_succeeded, n_failed)."""
    client = get_client_for(model)
    if client is None:
        env_hint = {
            "gpt": "OPENAI_API_KEY",
            "o1": "OPENAI_API_KEY",
            "o3": "OPENAI_API_KEY",
            "o4": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "llama": "TOGETHER_API_KEY",
            "deepseek": "TOGETHER_API_KEY",
            "mistral": "TOGETHER_API_KEY",
            "qwen": "TOGETHER_API_KEY",
        }
        hint = next(
            (v for k, v in env_hint.items() if model.lower().startswith(k)),
            "the relevant API key",
        )
        print(
            f"[skip] {model}: client unavailable (set {hint} to enable)",
            file=sys.stderr,
        )
        return (0, 0)

    results_csv = output_dir / "results.csv"
    raw_jsonl = output_dir / "raw_responses" / f"{_safe_model_filename(model)}.jsonl"

    semaphore = asyncio.Semaphore(concurrency)
    coros = [
        run_task(t, client, semaphore, results_csv, raw_jsonl,
                 max_tokens, timeout, file_lock)
        for t in tasks
    ]
    print(f"[{model}] running {len(tasks)} tasks (concurrency={concurrency})...")
    t0 = time.perf_counter()
    results = await asyncio.gather(*coros, return_exceptions=False)
    elapsed = time.perf_counter() - t0
    n_ok = sum(1 for r in results if r is not None)
    n_fail = len(results) - n_ok
    print(
        f"[{model}] done: {n_ok} ok, {n_fail} failed in {elapsed:.1f}s "
        f"({len(tasks) / max(elapsed, 0.001):.1f} req/s)"
    )
    return (n_ok, n_fail)


def _safe_model_filename(model: str) -> str:
    """Make a model name safe for use as a filename."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in model)


def build_task_list(
    items: list[TestItem],
    models: list[str],
    prompt_versions: list[str],
    completed: set[str],
    sample: Optional[int],
) -> list[Task]:
    """Cross-product of (items × models × prompts), minus the already-done ones."""
    selected_items = items if sample is None else items[:sample]
    tasks: list[Task] = []
    for item in selected_items:
        for model in models:
            for pv in prompt_versions:
                t = Task(item=item, model=model, prompt_version=pv)
                if t.pair_key in completed:
                    continue
                tasks.append(t)
    return tasks


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
# CLI
# ----------------------------------------------------------------------------
def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run the LLM Brand-Name Hallucination Benchmark.",
    )
    p.add_argument(
        "--test-set",
        type=Path,
        default=Path("test_set.jsonl"),
        help="Path to test_set.jsonl (default: ./test_set.jsonl)",
    )
    p.add_argument(
        "--models",
        nargs="+",
        default=["gpt-5", "claude-4.7-opus", "gemini-3-pro", "llama-4-maverick"],
        help="Models to evaluate.",
    )
    p.add_argument(
        "--prompts",
        nargs="+",
        default=list(PROMPT_REGISTRY.keys()),
        choices=list(PROMPT_REGISTRY.keys()),
        help="Prompt versions to evaluate.",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Output directory (default: ./results).",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Max parallel requests per model (default: 10).",
    )
    p.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Only run the first N names per model (smoke test).",
    )
    p.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Max output tokens per response (default: 512).",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds (default: 60).",
    )
    p.add_argument(
        "--yes-costs",
        action="store_true",
        help="Bypass the $50 cost confirmation prompt.",
    )
    p.add_argument(
        "--cost-threshold",
        type=float,
        default=50.0,
        help="USD threshold above which --yes-costs is required (default: $50).",
    )
    return p.parse_args(argv)


async def main_async(args: argparse.Namespace) -> int:
    # 1. Load test set
    if not args.test_set.exists():
        print(
            f"[fatal] Test set not found: {args.test_set}\n"
            f"        (Is the test-set-builder agent done? Check "
            f"benchmarks/llm-hallucination-2026/test_set.jsonl)",
            file=sys.stderr,
        )
        return 2

    items = load_test_set(args.test_set)
    print(f"[load] {len(items)} test items from {args.test_set}")
    test_sha = file_sha256(args.test_set)
    print(f"[load] test_set sha256: {test_sha}")

    # 2. Validate prompt versions
    for pv in args.prompts:
        if pv not in PROMPT_REGISTRY:
            print(f"[fatal] Unknown prompt version: {pv}", file=sys.stderr)
            return 2

    # 3. Set up output dir and resumability
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "raw_responses").mkdir(parents=True, exist_ok=True)
    results_csv = args.output_dir / "results.csv"
    completed = load_completed_pairs(results_csv)
    if completed:
        print(f"[resume] {len(completed)} (item, model, prompt) pairs already done — skipping.")

    # 4. Build task list (sample-aware, resume-aware)
    tasks = build_task_list(items, args.models, args.prompts, completed, args.sample)
    print(f"[plan] {len(tasks)} new tasks to run")
    if not tasks:
        print("[plan] nothing to do — exiting.")
        # Still write the manifest so summary.json has provenance.
        _write_manifest(args, items, test_sha)
        return 0

    # 5. Cost estimate
    n_per_model = len(tasks) // max(len(args.models), 1)
    est = estimate_total_cost(
        models=args.models,
        n_names=max(n_per_model // max(len(args.prompts), 1), 1),
        n_prompts=len(args.prompts),
    )
    print(f"[cost] estimated total: ${est:.2f}")
    if est > args.cost_threshold and not args.yes_costs:
        print(
            f"[cost] estimate exceeds ${args.cost_threshold:.2f}. "
            f"Re-run with --yes-costs to proceed.",
            file=sys.stderr,
        )
        return 3

    # 6. Group tasks by model and dispatch
    by_model: dict[str, list[Task]] = {m: [] for m in args.models}
    for t in tasks:
        by_model[t.model].append(t)

    file_lock = asyncio.Lock()
    t_start = time.perf_counter()
    grand_ok, grand_fail = 0, 0
    # Run models concurrently — they hit different providers so don't share
    # rate limits.
    coros = [
        run_for_model(
            model, mtasks, args.output_dir,
            args.concurrency, args.max_tokens, args.timeout, file_lock,
        )
        for model, mtasks in by_model.items() if mtasks
    ]
    results = await asyncio.gather(*coros)
    for ok, fail in results:
        grand_ok += ok
        grand_fail += fail
    elapsed = time.perf_counter() - t_start
    print(
        f"[done] {grand_ok} ok / {grand_fail} failed across "
        f"{len(args.models)} models in {elapsed:.1f}s"
    )

    # 7. Write the manifest (provenance)
    _write_manifest(args, items, test_sha)
    print(f"[done] results: {results_csv}")
    return 0 if grand_fail == 0 else 1


def _write_manifest(args: argparse.Namespace, items: list[Any], test_sha: str) -> None:
    manifest = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "test_set_path": str(args.test_set),
        "test_set_sha256": test_sha,
        "test_set_n_items": len(items),
        "models": args.models,
        "prompts": args.prompts,
        "sample": args.sample,
        "concurrency": args.concurrency,
        "git_commit": _git_commit(),
        "python": sys.version.split()[0],
    }
    (args.output_dir / "manifest.json").write_bytes(
        orjson.dumps(manifest, option=orjson.OPT_INDENT_2)
    )


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[interrupt] caught Ctrl-C — partial results saved; "
              "re-run to resume.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
