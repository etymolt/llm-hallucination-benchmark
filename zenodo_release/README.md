# LLM Brand-Name Hallucination Benchmark v0.5 — raw scoring outputs

**Deposit DOI:** _assigned on publish_
**Version:** 0.5
**Date:** 2026-05-26 (scoring) / 2026-06-10 (deposit)
**License:** [CC-BY-4.0](LICENSE)
**Source repo:** https://github.com/etymolt/llm-hallucination-benchmark
**Paper:** https://github.com/etymolt/llm-hallucination-benchmark/blob/main/PAPER.md

## What's in this deposit

| File | Size | Rows | Description |
|------|------|------|-------------|
| `cells.jsonl` | ~388 MB | 975,192 | Per-cell scored outputs — one JSON object per (name x model x condition x repeat x scored unit). The atomic unit of replication. |
| `analysis.json` | 5 KB | — | Aggregate headline metrics with Wilson + bootstrap 95% CIs, hypothesis tests (H2-H9 with Holm-adjusted p-values). |
| `MANIFEST.txt` | <1 KB | — | sha256 sums for every deposit file. |
| `DATASET_SCHEMA.md` | — | — | Formal schema for `cells.jsonl` rows. |
| `REPLICATION_QUICKSTART.md` | — | — | Five-line `jq` recipe to re-derive the 97.01% headline from `cells.jsonl`. |
| `metadata.json` | — | — | Zenodo Deposit API metadata used to create this record. |

## The headline (and how to verify it in 60 seconds)

> **97.01%** of confident, verifiable USPTO citations produced by frontier LLMs
> when asked about brand-name conflicts are **fabricated or mis-attributed**.
> Wilson 95% CI: **[96.86%, 97.16%]**. k = 48,822 / n = 50,327.

To verify directly from `cells.jsonl`:

```bash
jq -nc '
  [inputs | select(.unit | startswith("citation:")) | select(.tier==1 and .confident==true)]
  | {n: length,
     k: (map(select(.hallucinated)) | length),
     rate: ((map(select(.hallucinated)) | length) / length)}' \
  cells.jsonl
```

Expected output:

```json
{"n":50327,"k":48822,"rate":0.9701156836091205}
```

See [`REPLICATION_QUICKSTART.md`](REPLICATION_QUICKSTART.md) for additional
recipes (per-model, per-surface, hypothesis re-derivation).

## Experiment design (one-page summary)

- **Names tested:** 1,200 candidate brand names spanning five trap buckets
  (famous marks, recently registered marks, established marks, domain-only
  collisions, and a control bucket of fresh coinings).
- **Models:** GPT-5.5, GPT-5.4, Claude Opus 4.7, Claude Sonnet 4.6,
  Gemini 3.1 Pro, Gemini 3.1 Flash-Lite.
- **Conditions:** 3 elicitation prompts (a1 naive, a2 structured,
  a3 abstention-licensed) x 2 retrieval modes (b1 closed-book, b2 retrieval-augmented).
- **Repeats:** 3 independent generations per cell.
- **Total generations:** 1,200 x 6 models x 6 conditions x 3 repeats = 129,600.
- **Scored cells:** 975,192 (each generation produces multiple scored units
  — conflicts, citations, surface-level claims).

## Headline figures (from `analysis.json`)

| Metric | k | n | Rate | Wilson 95% CI | Bootstrap 95% CI |
|---|---|---|---|---|---|
| Overall hallucination | 150,464 | 555,770 | 27.07% | [26.96%, 27.19%] | [26.22%, 27.97%] |
| Accuracy | 405,306 | 555,770 | 72.93% | [72.81%, 73.04%] | [72.03%, 73.78%] |
| False-availability | 273 | 158,225 | 0.17% | [0.15%, 0.19%] | [0.12%, 0.23%] |
| **Confident tier-1 USPTO citations hallucinated** | **48,822** | **50,327** | **97.01%** | **[96.86%, 97.16%]** | — |

Per-surface hallucination rates and hypothesis tests (H2-H9) live in
`analysis.json` and are reproduced in [`PAPER.md`](https://github.com/etymolt/llm-hallucination-benchmark/blob/main/PAPER.md).

## Provenance

- **Run window:** 2026-05-23 14:41:59 UTC — 2026-05-26 (continuous, multi-batch).
- **Run ID family:** `run-20260523T144159..02` (see source repo `v2/runs/`).
- **Model versions:** snapshot strings recorded in the per-row `model`
  + `family` fields. We froze model IDs at run start; no live model rotation.
- **Ground truth sources:**
  - USPTO Trademark Status & Document Retrieval (TSDR) — for serial/registration
    number validity. Snapshot date 2026-05-22.
  - USPTO bulk trademark XML feed — for owner / status / live-dead checks.
  - WHOIS / RDAP — for domain availability cross-checks.
  - Manual adjudication for the cultural-meaning surface (3-rater majority,
    Cohen's kappa = 0.81; rater notes in source repo).
- **Scoring code:** `scoring.py` in the source repo (frozen at commit
  pinned in the run manifest).

## Why this deposit exists

The benchmark repo intentionally `.gitignore`s `results/` so the codebase
stays clean. That made the 97.01% headline non-reproducible from public
sources alone — a reviewer would have had to spend ~$1,500 of API calls
to re-derive it. This deposit closes that gap: anyone can now download
`cells.jsonl`, run the `jq` recipe above, and either confirm or
falsify the headline in under a minute.

## License

Released under [Creative Commons Attribution 4.0
International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/).

**Attribution string:**

> Etymolt Inc. (2026). *LLM Brand-Name Hallucination Benchmark v0.5 —
> raw scoring outputs* [Dataset]. Zenodo. DOI: _assigned on publish_

## Citation

```bibtex
@dataset{etymolt_llm_hallucination_v05,
  author       = {{Etymolt Inc.}},
  title        = {LLM Brand-Name Hallucination Benchmark v0.5 — raw scoring outputs},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {0.5},
  doi          = {10.5281/zenodo.PLACEHOLDER},
  url          = {https://doi.org/10.5281/zenodo.PLACEHOLDER}
}
```

## Contact

- Repo issues: https://github.com/etymolt/llm-hallucination-benchmark/issues
- Email: research@etymolt.com
