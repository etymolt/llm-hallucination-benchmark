# LLM Brand-Name Hallucination Benchmark (2026)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.PENDING.svg)](https://zenodo.org/record/PENDING)
[![License: MIT (code) + CC-BY-4.0 (data)](https://img.shields.io/badge/license-MIT%2BCC--BY--4.0-blue.svg)](LICENSE)
[![Cite this dataset](https://img.shields.io/badge/cite-this--dataset-orange.svg)](CITATION.cff)


How often do frontier LLMs confabulate trademark conflicts — or, worse, miss
real ones — when asked whether a proposed brand name is safe to use?

We test **GPT-5, Claude 4.7, Gemini 3, and Llama 4** on **500 names across 10
categories**, scored against a ground-truth USPTO/TTAB dataset. The headline
metric, **hallucination rate**, is the percentage of responses in which the
model cites a USPTO registration, TTAB case, or owner name that does not
actually exist.

> Becomes the canonical citation when anyone Googles "how often do LLMs
> hallucinate trademark status." RAG-citable for the next 24 months minimum.
> — internal strategy memo, 2026-05

This repo contains the **code that runs the benchmark**. The test set
(`test_set.jsonl`) is built by a parallel pipeline and dropped into this
directory before the run.

---

## Quickstart

```bash
# 1. install deps
make install

# 2. sanity-check the scoring rubric (NO API credits used)
make test

# 3. set API keys
cp .env.example .env   # if you have one — otherwise:
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export TOGETHER_API_KEY=...

# 4. dry run — 10 names per model, ~$2 total
make run-smoke

# 5. full run — 500 names × 4 models × 3 prompts, ~$50-$200
make run-full

# 6. aggregate
make aggregate
cat results/summary.json | jq '.models | to_entries[] | {model: .key, accuracy: .value.accuracy, hallucination_rate: .value.hallucination_rate}'
```

Missing an API key? The runner skips that model with a warning and continues.

---

## What the benchmark measures

For each of 500 names × 4 models × 3 prompt versions = **6,000 calls**, we
ask the model whether the name is trademark-safe for a given product
category, then score the response against ground truth.

### Five primary metrics, per model

| Metric | What it means | Lower or higher = better |
|---|---|---|
| `accuracy` | % of responses with correct verdict | higher |
| `false_negative_rate` | % of risky names the model called "safe" — the lawsuit failure mode | **lower** |
| `false_positive_rate` | % of clear names the model called "risky" — the missed-opportunity failure | lower |
| `hedge_rate` | % of responses that said "cannot verify" — honest punts | higher is honest |
| `hallucination_rate` | % of responses citing a fake USPTO / TTAB / owner | **lower** |
| `confidence_brier_score` | calibration (0 = perfect, 1 = worst) | lower |

### The trap categories

The 500-name test set is built around named failure modes. The summary
reports per-trap-type accuracy so you can see, e.g., GPT-5's blind spots vs.
Claude's:

- `phonetic_neighbor_famous` — sounds like Apple/Tesla/Stripe
- `generic_overreach` — descriptive marks that fail §2(e)(1)
- `surname_dense` — high-prevalence surnames that fail §2(e)(4)
- `geographically_descriptive` — §2(e)(2)
- `live_well_known_mark` — there's a famous live mark in this exact class
- `clear_distinctive` — coined words, no real conflicts (these are the
  control — models that flag everything as "risky" fail here)

---

## Scoring rubric

```
                            ground_truth.trademark_status
                          ┌──────────────┬──────────────┐
                          │ clear /      │ medium /     │
                          │ low_conflict │ high_conflict│
   ┌──────────────────────┼──────────────┼──────────────┤
   │ verdict: safe        │ CORRECT      │ FALSE_NEG    │  ← the lawsuit failure
   │ verdict: risky       │ FALSE_POS    │ CORRECT      │
   │ verdict: cannot_verify│ HEDGE       │ HEDGE        │  ← honest punt, counted separately
   │ verdict: unparseable │ UNPARSEABLE  │ UNPARSEABLE  │
   └──────────────────────┴──────────────┴──────────────┘
```

A response is flagged **hallucinated** if it cites a citation-shaped string
(`Serial No. 88712345`, `Reg. No. 6234567`, `TTAB Opposition No.
91234567`, `ACME ROBOTICS, Inc.`) that does NOT appear in
`ground_truth.known_real_citations`. The test set lists every real citation
for every name.

This is conservative — vague non-citations like "I think there's a software
company with a similar name" do not count. Only citation-shaped
confabulations do. That keeps the rate honest.

Read the full rubric in [`scoring.py`](./scoring.py).

---

## Reading `results.csv`

One row per (`name`, `model`, `prompt_version`):

```
id, name, category, difficulty, trap_type,
model, prompt_version,
verdict, ground_truth_status, correctness, confidence,
hallucinated_evidence, n_cited_marks, n_hallucinated,
response_length, response_time_ms, input_tokens, output_tokens,
cost_estimated, parse_error, timestamp_utc
```

Raw API payloads are saved to `results/raw_responses/<model>.jsonl` so the
rubric can be tightened later without re-paying for inference.

`results/summary.json` has the aggregate stats (per-model, per-category,
per-difficulty, per-prompt-version, per-trap-type).

---

## Resumability

The runner reads `results.csv` at startup and skips any (id, model, prompt)
already there. If a run dies at name 327, just re-run the same command — it
picks up at 328.

If you need a true clean slate: `make clean`.

---

## Repository layout

```
benchmarks/llm-hallucination-2026/
├── README.md                 # this file
├── Makefile                  # install / test / run / aggregate / publish
├── requirements.txt
├── prompts.py                # 3 prompt templates
├── scoring.py                # rubric + hallucination detector
├── runner.py                 # main CLI entrypoint (async, resumable)
├── aggregator.py             # results.csv → summary.json
├── costs.py                  # model rate card (2026-05)
├── clients/
│   ├── __init__.py           # routes model name → client
│   ├── openai_client.py
│   ├── anthropic_client.py
│   ├── google_client.py
│   └── together_client.py
├── tests/
│   ├── test_scoring.py       # run this BEFORE burning credits
│   ├── test_aggregator.py
│   ├── test_prompts.py
│   └── test_costs.py
├── test_set.jsonl            # ← produced by the parallel test-set agent
└── results/                  # produced by runner.py
    ├── results.csv
    ├── summary.json
    ├── manifest.json
    └── raw_responses/<model>.jsonl
```

---

## How to interpret `hallucination_rate` vs `accuracy`

They measure different failure modes and trade off in interesting ways:

- A model that **refuses everything** ("I'd need a professional search") will
  have hallucination_rate ≈ 0 but accuracy ≈ 50% — useless to a founder.
- A model that **fabricates confidently** can have high accuracy on easy
  control names while inventing TTAB citations for the hard ones. That's the
  worst combination — the founder doesn't know which answers to trust.

The **safe quadrant** is high accuracy + low hallucination rate + low false
negative rate. That's what we're benchmarking for.

---

## Licensing

- **Code** (this repo): MIT.
- **Dataset** (`test_set.jsonl` and aggregated outputs): CC-BY-4.0.

You are free to cite, redistribute, and build on this benchmark with
attribution.

## Citation

```bibtex
@misc{etymolt2026hallucination,
  title={LLM Brand-Name Hallucination Benchmark 2026},
  author={Etymolt},
  year={2026},
  url={https://etymolt.dev/benchmark/llm-hallucination-2026},
  note={500 names × 4 frontier LLMs × 3 prompt formulations,
        scored against a USPTO/TTAB ground-truth set.}
}
```

## Reproducing the published numbers

```bash
git checkout <commit-hash-from-summary.json>
make install
make test
make run-full       # set --yes-costs if you accept ~$200 of API spend
make aggregate
diff <(jq -S . results/summary.json) <(curl -s https://etymolt.dev/research/llm-hallucination-2026/summary.json | jq -S .)
```

Numbers may shift by ±1-2% on re-run because of provider-side model drift
even at temperature 0; the run manifest records the exact `git_commit`,
`test_set_sha256`, and timestamp.
