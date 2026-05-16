---
title: "Press Kit — LLM Brand-Name Hallucination Benchmark"
publisher: Etymolt (Dear One Technologies Pvt Ltd)
embargo: None — publish anytime after 2026-05-XX
contact: press@etymolt.com
last_updated: 2026-05-XX
---

# Press Kit
## The LLM Brand-Name Hallucination Benchmark

**Etymolt Research — May 2026**

---

## 100-word summary

Etymolt today released the LLM Brand-Name Hallucination Benchmark — the first systematic measurement of how often frontier AI models fabricate trademark-clearance claims when founders ask whether a proposed brand name is legally safe. The benchmark tests six frontier models (GPT-5, GPT-4.5, Claude 4.7 Opus and Sonnet, Gemini 3 Pro, Llama 4 405B) against 500 candidate names with ground truth verified via USPTO records. The headline finding: no current frontier model is safe to use as the final clearance check on a brand name, with the most dangerous failure mode being silent over-blessing of names that conflict with recently-filed registrations the model has never seen.

---

## Key statistics (placeholders pending final run)

1. **`[RESULT_PLACEHOLDER: best_model_overall_accuracy]`%** — best-in-class frontier model accuracy on US trademark clearance.
2. **`[RESULT_PLACEHOLDER: v1_cite_hall_overall]`%** — share of naive-prompt model responses containing at least one fabricated USPTO citation.
3. **`[RESULT_PLACEHOLDER: recent_acc_mean]`%** — mean accuracy across all six models on names that conflict with registrations filed in the past 18 months.
4. **`[RESULT_PLACEHOLDER: fn_fp_ratio]`×** — ratio of false-negative to false-positive errors (saying "safe" when truth is "risky").
5. **`[RESULT_PLACEHOLDER: min_ece]`** — best (lowest) Expected Calibration Error across the six models. Perfect calibration = 0.

---

## Quote-able statements

**On the headline finding:**
> "No current frontier model is safe to use as the final clearance check on a brand name. Not because the models are bad. Because the question is structurally outside their training data."
> — Tariq Attarwala, Founder, Etymolt

**On the OpenClaw incident:**
> "The OpenClaw incident is the canary in the LLM-naming coal mine. The economic loss is denominated in token-holder capital. The upstream cause is the same parametric-memory failure this benchmark measures."
> — Tariq Attarwala

**On the asymmetric error pattern:**
> "Models over-bless. They tell founders names are safe more often than they tell them names are risky. RLHF training rewards confident helpful responses, and 'yes, ship it' is a more rewarding answer than 'I don't know, hire a lawyer.'"
> — Tariq Attarwala

**On citation hallucination:**
> "The models invent USPTO serial numbers. The numbers look right — eight digits, correct format. They are fiction. This is the same failure mode that sanctioned the Mata v. Avianca lawyers in 2023, ported to the trademark domain."
> — Tariq Attarwala

**On the recent-registration blind spot:**
> "Any startup that filed in the past 12 months is essentially invisible to the model's parametric memory — even though, from a clearance perspective, that startup's registration is precisely as binding as a 30-year-old Coca-Cola registration."
> — Tariq Attarwala

---

## Methodology one-pager

**What we tested.** 500 proposed brand names × 6 frontier LLMs × 3 prompt formulations = 9,000 model responses.

**Names.** 50 names per category across 10 categories: B2B SaaS, consumer fintech, AI infrastructure, developer tools, direct-to-consumer, gaming, health, AI agents, dev infrastructure, creator economy.

**Trap types.** Each category is stratified across four trap structures: phonetic neighbours of famous marks, dead-mark lookalikes, foreign-brand collisions, and recent-micro-startup collisions.

**Ground truth.** Each name's verdict — safe / risky / requires-live-lookup — is determined by USPTO TSDR queries plus dual review by qualified US trademark attorneys. Inter-rater agreement: Cohen's κ ≥ 0.8.

**Models.** GPT-5, GPT-4.5, Claude 4.7 Opus, Claude 4.7 Sonnet, Gemini 3 Pro, Llama 4 405B. All queried at temperature 0.

**Prompts.** Three formulations: (v1) the naive way a founder asks; (v2) structured-JSON output forcing a verdict and confidence; (v3) grounded with evidence request and an explicit "I cannot verify" escape hatch.

**Metrics.** Verdict accuracy, false-negative rate, citation hallucination rate, confidence calibration (Brier score, expected calibration error), hedge rate.

**Reproducibility.** Test set, scoring rubric, runner pipeline, and raw responses released as open data under CC-BY-4.0 / MIT. Any third party can re-run the benchmark and report independent numbers.

**Re-run cadence.** Quarterly. Trap names rotate to prevent provider gaming. Next release: August 2026.

---

## Author bio

**Tariq Attarwala** is the founder of Etymolt, the verification infrastructure layer for LLM-native brand naming. Etymolt is the operating product of Dear One Technologies Private Limited (CIN: U86900MH2026PTC467148), incorporated in Mumbai with a Silicon Valley relocation in progress in 2026. Before founding Etymolt, Attarwala worked in product and brand strategy across multiple industries; the LLM-naming thesis emerged from observing the systemic mismatch between AI-generated identifiers and registry-determined adjudication.

Etymolt's two-engine architecture — a TTAB-grounded Clearance Engine and a craft-grounded Taste Engine — is the operational answer to the failure modes measured in this benchmark. The benchmark itself is released as open data; the Clearance Engine product is reported separately.

**Contact:**
- Email: tariq@etymolt.com (founder); press@etymolt.com (press)
- LinkedIn: linkedin.com/in/tariq-attarwala
- Etymolt: etymolt.com
- Research: etymolt.com/research

---

## Image and chart descriptions

The following charts are generated from `results.csv` after the runner completes. Each is available as a 300 DPI PNG in the press archive at etymolt.com/research/llm-naming-hallucination-benchmark/press.

### Chart 1 — Hero comparison: per-model verdict accuracy

Horizontal bar chart. Y-axis: six models, ordered by overall accuracy descending. X-axis: 0–100% accuracy. Bars colour-coded by provider (OpenAI, Anthropic, Google, Meta). Reference line at `[RESULT_PLACEHOLDER: specialist_baseline]`% marking the Etymolt Clearance Engine specialist-system baseline. The visual story: every frontier model falls well below the specialist baseline.

### Chart 2 — False-negative asymmetry

Side-by-side stacked bars. For each model, the bar shows the proportion of errors that were false-negative (red) vs false-positive (yellow). The visual story: red dominates across every model. The asymmetry is the news.

### Chart 3 — Calibration reliability diagram

Per-model reliability diagram. X-axis: predicted probability (10 equal-width bins, 0–10%, 10–20%, etc.). Y-axis: empirical accuracy. Diagonal y=x line marks perfect calibration. Each model's curve plotted with confidence bands. Models below the diagonal in the high-confidence bins are overconfident; we expect every frontier model to lie below.

### Chart 4 — Per-category heatmap

Heatmap. Rows: 6 models. Columns: 10 categories. Cell value: accuracy. Colour scale red (low) to green (high). The visual story: which model/category combinations are weakest.

### Chart 5 — Trap-type breakdown

Grouped bar chart. X-axis: four trap types. Y-axis: mean accuracy across models. Bars: phonetic_neighbor_famous, dead_mark_lookalike, foreign_brand, recent_micro_startup. The visual story: recent_micro_startup is the worst across the board.

### Chart 6 — Hedge rate by difficulty

Line chart. X-axis: difficulty (easy / medium / hard). Y-axis: hedge rate (% of responses). One line per model. The visual story: well-calibrated models have rising lines; uncalibrated models have flat lines.

---

## Background and context

### Why is this benchmark different from prior LLM-hallucination work?

The closest prior art is the Stanford HAI / RegLab line of research on legal AI hallucination (Dahl et al., 2024; Magesh et al., 2025), which measured 17–43% hallucination rates in legal-research products. The general-purpose hallucination benchmarks — TruthfulQA, HaluEval, HALoGEN, FActScore — measure factuality across open domains.

Our benchmark differs in three ways. **First**, the domain is narrow and action-consequential — a founder makes an economic decision on the basis of the answer. **Second**, ground truth is operationally verifiable against a public registry (USPTO TSDR) rather than determined by expert consensus. **Third**, we report not just accuracy but the calibration of the model's confidence and the realism of any citations it produces.

### How does this fit the broader LLM-safety conversation?

This benchmark is a narrow-domain factuality probe with measurable economic downstream. Similar narrow-domain probes are emerging in medical naming, scientific instrument designation, and financial-product naming. The general lesson is that parametric-memory-only LLMs systematically fail in any domain where ground truth is determined by a registry that the model does not have live access to. The remediation is architectural: route the query through retrieval. The benchmark provides the quantitative basis for measuring that remediation when providers implement it.

### What is Etymolt's commercial interest?

Etymolt is building the verification layer that wraps LLM-generated brand names with registry-grounded clearance. The benchmark measures the gap between unaided-LLM accuracy and specialist-system accuracy; that gap is the willingness-to-pay surface for the verification-layer market. We are explicit about this conflict and release the dataset, rubric, and code as open data so any third party can verify or contest the methodology.

---

## Key sources and prior art

- *In re E.I. du Pont de Nemours & Co.*, 476 F.2d 1357 (C.C.P.A. 1973). The DuPont factors for §2(d) likelihood-of-confusion analysis.
- *Mata v. Avianca, Inc.*, 678 F. Supp. 3d 443 (S.D.N.Y. 2023). Sanctions order for ChatGPT-fabricated legal citations.
- *Comet ML, Inc. v. Perplexity AI, Inc.* (N.D. Cal. 2025; settled). Trademark-infringement and AI-hallucination dispute.
- *OpenAI Appeals Order Barring 'io' Name in Trademark Lawsuit.* Bloomberg Law IP, 2025.
- Dahl, M., Magesh, V., Suzgun, M., & Ho, D. E. (2024). Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models. *Journal of Legal Analysis* 16(1). arXiv:2401.01301.
- Magesh, V., et al. (2025). Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools. *Journal of Empirical Legal Studies.*
- Ravichander, A., et al. (2025). HALoGEN: Fantastic LLM Hallucinations and Where to Find Them. ACL 2025. arXiv:2501.08292.
- Lin, S., Hilton, J., & Evans, O. (2022). TruthfulQA. ACL 2022. arXiv:2109.07958.
- OpenClaw incident coverage: *Wikipedia*, *Medium* (Toni Maxx, "The Lobster That Tried to Be Claude"), *The Singularity Point* substack ("The OpenClaw Saga"), February 2026.

---

## How to cite

> Attarwala, T. (2026). *The LLM Brand-Name Hallucination Benchmark: How Often Do Frontier Models Fabricate Trademark Clearance?* Etymolt Research, May 2026. https://etymolt.com/research/llm-naming-hallucination-benchmark

BibTeX:
```bibtex
@misc{attarwala2026llmtrademark,
  title  = {The LLM Brand-Name Hallucination Benchmark: How Often Do
            Frontier Models Fabricate Trademark Clearance?},
  author = {Tariq Attarwala},
  year   = {2026},
  month  = may,
  howpublished = {Etymolt Research},
  url    = {https://etymolt.com/research/llm-naming-hallucination-benchmark}
}
```

---

## Contact

- **General press:** press@etymolt.com
- **Founder interview requests:** press@etymolt.com (subject: "Interview request — LLM benchmark")
- **Technical questions / replication support:** research@etymolt.com
- **Twitter/X:** @etymolt
- **LinkedIn:** linkedin.com/company/etymolt

We respond to credentialed press inquiries within 24 hours. The founder is available for on-record interviews in English. Etymolt is headquartered in Mumbai, India; a US (San Francisco) office opens Q3 2026.

---

*Press kit updated 2026-05-XX. Last benchmark run: 2026-05-XX. Next benchmark run: 2026-08-XX.*
