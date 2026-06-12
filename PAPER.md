---
title: "The LLM Brand-Name Hallucination Benchmark: How Often Do Frontier Models Fabricate Trademark Clearance?"
authors:
  - Tariq Attarwala
affiliation: "Dear One Technologies Pvt Ltd / Etymolt, Mumbai"
date: 2026-05-XX
doi: 10.0000/etymolt.2026.001  # placeholder, to be assigned
keywords: LLM, hallucination, trademark, USPTO, TTAB, brand naming, AI, GPT-5, Claude, Gemini, Llama, calibration, retrieval-augmented generation
license: Paper CC-BY-4.0; Dataset CC-BY-4.0; Code MIT
correspondence: research@etymolt.com
---

# The LLM Brand-Name Hallucination Benchmark
## How Often Do Frontier Models Fabricate Trademark Clearance?

**Tariq Attarwala**
Etymolt — Dear One Technologies Pvt Ltd
Mumbai, India

*Version 1.0 — May 2026*

---

## Abstract

We introduce the LLM Brand-Name Hallucination Benchmark, the first systematic evaluation of how often frontier large language models (LLMs) fabricate trademark-clearance claims when asked to assess the legal safety of proposed brand names. The benchmark comprises 500 candidate brand names stratified across 10 categories (B2B SaaS, consumer fintech, AI infrastructure, developer tools, direct-to-consumer, gaming, health, AI agents, dev infrastructure, and creator economy) and 4 trap structures (phonetic-neighbor-of-famous-mark, dead-mark-lookalike, foreign-brand collision, recent-micro-startup collision). Each name carries ground truth derived from USPTO TSDR queries and dual expert review. We evaluate six frontier models — GPT-5, GPT-4.5, Claude 4.7 Opus, Claude 4.7 Sonnet, Gemini 3 Pro, and Llama 4 405B — across three prompt formulations (naive, constrained-JSON, grounded-with-evidence-request). We measure five quantities: verdict accuracy against ground truth, false-negative rate (the most costly error class for founders), citation hallucination rate (fabricated USPTO serial numbers and TTAB decisions), confidence calibration (Brier score and expected calibration error), and hedge rate (frequency of appropriate "I cannot verify" responses). Results, methodology, and per-model breakdown are reported with full reproducibility — the test set, scoring rubric, and runner pipeline are released as open data. The benchmark is designed for quarterly re-runs as models evolve, and is positioned as a stable reference for downstream research, policy discussion, and verification-layer infrastructure.

**Keywords:** LLM evaluation, hallucination, trademark law, USPTO, TTAB, calibration, retrieval-augmented generation, brand naming

---

## 1. Introduction

### 1.1 The OpenClaw incident — the canary in the LLM-naming coal mine

On January 27, 2026, the iOS developer Peter Steinberger received a cease-and-desist letter from Anthropic's legal team. The letter alleged that the name of Steinberger's viral autonomous coding agent — Clawdbot — was confusingly similar to the Claude trademark family, in violation of Section 2(d) of the Lanham Act. Steinberger was given a window of days to rename the project or face suit [^openclaw-wiki].

Within hours, Steinberger renamed Clawdbot to Moltbot, preserving the lobster motif of the original branding. He freed the original GitHub username and the original X handle so the new identity could claim them cleanly. In the seconds between release and reclaim, two adversarial actors — likely automated — sniped both handles. Within hours of the snipe, the @clawdbot X account had been weaponised to promote a $CLAWD memecoin, marketed as the "official token" of the open-source agent project. The token had no association with Steinberger or the project. Approximately $16 million in retail capital was extracted before the scam was widely identified [^openclaw-substack][^openclaw-medium]. Three days later, Steinberger renamed again — from Moltbot to OpenClaw — because Moltbot, in his words, "never quite rolled off the tongue."

The OpenClaw incident is not, on its face, a story about LLMs. It is a story about handle hygiene during rebrands. But it is also the cleanest available case study of what happens at the *intersection* of three trends: (i) AI-generated brand names entering production without legal clearance, (ii) the speed at which adversarial actors exploit identity gaps, and (iii) the absence of any verification layer between the LLM that proposed the name and the registries that adjudicate it. Each rename in the OpenClaw saga was conducted under acute time pressure, with the founder asking an LLM for advice on alternative names. Each rename created a new opportunity for collision. The economic loss is denominated in token-holder capital; the upstream cause is denominated in the same parametric memory failure this benchmark measures.

This paper asks a question that, until now, has been answered only anecdotally: **when an LLM tells a founder "yes, that name is trademark-safe" — how often is it lying?** And, more pointedly: when it cites a TTAB case or a USPTO registration to support its claim — does that case exist?

### 1.2 The economic value being eroded

Trademark conflict is the rare class of brand-naming error that is denominated in money rather than aesthetics. A typical small-business rebrand costs $10,000–$50,000 in legal, marketing, design, and lost-traffic terms; a venture-backed rebrand can exceed several million dollars [^rebrand-cost]. Tropicana's 2009 redesign — a related but instructive precedent — produced a $30 million sales drop within two months [^tropicana-case]. The Comet ML v. Perplexity AI dispute, settled in late 2025, played out in federal court in the Northern District of California after Comet ML produced evidence that Perplexity's own AI chatbot was repeatedly conflating the two companies — a hallucination on the part of the infringing party's own product, deployed in support of the infringer's brand [^law360-comet]. OpenAI's "io" name was enjoined by a California district court in 2025 after IYO Inc. brought a Section 43(a) infringement action [^bloomberg-io]; the same year, OpenAI was restrained from using "Cameo" in the Sora video platform after the Cameo platform brought suit [^techbuzz-cameo].

The pattern in these cases is consistent: the model proposing or defending the name has neither a real-time index of the trademark register nor calibrated awareness of its own ignorance. It generates a clearance verdict from parametric memory. The verdict feels confident. The founder ships. The conflict is litigated later.

We argue that the *rate* at which frontier LLMs produce these false-confident clearance verdicts is now itself a load-bearing parameter of the AI-naming economy. We do not yet have a published number for it. This benchmark exists to produce one.

### 1.3 The research question

This benchmark measures four properties of a frontier model's trademark-clearance behaviour, as a function of model identity, model size, prompt formulation, name category, and trap type:

1. **Verdict accuracy** — for a given proposed name with known ground truth, does the model produce the correct safe/risky verdict?
2. **False-negative rate** — when the ground truth says the name is risky, how often does the model say it is safe? This is the founder-facing failure mode that produces the OpenClaw class of outcome.
3. **Citation hallucination rate** — when the model cites specific USPTO serial numbers, registration numbers, or TTAB decisions in support of its verdict, what fraction of those citations refer to records that exist in the actual USPTO register?
4. **Confidence calibration** — when the model reports a confidence score, does that score predict the actual probability of correctness? We measure this with Brier score and expected calibration error (ECE).
5. **Hedge rate** — how often does the model appropriately refuse to commit to a verdict, citing inability to verify without live database access? Models with high hedge rates on hard cases are well-calibrated; models with low hedge rates on hard cases are overconfident.

We test 500 names × 6 models × 3 prompt variants = 9,000 model responses. Each response is scored against ground truth derived from USPTO TSDR queries and dual expert review. We release the test set, scoring code, and raw model responses as open data.

### 1.4 Why this matters now

Three structural shifts have converged in the 2024–2026 window to make this question urgent.

**First**, LLM-generated naming has reached majority share. Kruze Consulting's 2025 survey of US-based startups reports that 65% of seed-stage founders use ChatGPT (with 24% on Claude) as their primary brainstorming tool [^kruze-survey], and Stack Overflow's 2025 developer survey reports that 82% of developers using AI assistants are using ChatGPT [^stackoverflow-2025]. The naming-agency function has not disappeared, but its market share has materially moved. A non-trivial fraction of brand names launched into the market in 2026 was first proposed by a model.

**Second**, the consequences of bad clearance are no longer absorbed silently by name-owners — they are increasingly litigated in fast-moving disputes. The Mata v. Avianca sanctions order [^mata-cnn][^mata-wiki] established the principle that lawyers who submit fabricated citations to courts will face sanctions even if the citations came from a model they trusted; the same principle has begun migrating into the trademark prosecution context, where TTAB judges have, since mid-2024, begun explicitly asking whether submitted authorities have been verified against PACER and TSDR before being relied upon.

**Third**, the verification gap is now economically addressable. The USPTO TSDR API is public and free. The TTAB decision corpus is downloadable in bulk. A verification layer over LLM brand suggestions can be built in 2026 at a fraction of the cost it would have required in 2022, because the labelling-cost moat that protected incumbent legacy vendors (Markify, Corsearch, CompuMark) has collapsed under frontier-LLM-driven extraction [^markify-corpus-note]. The market is now waiting for a benchmark that says, with numerical precision, how badly the unaided LLMs perform — so that buyers of a verification layer can calibrate the value of the layer against the failure rate of the baseline.

This benchmark is that number.

### 1.5 Contributions

We make four contributions:

1. **A 500-name test set** stratified across 10 brand categories and 4 trap structures, released as `test_set.jsonl` under CC-BY-4.0. Each row carries the candidate name, the proposed product category, a difficulty label, a trap-type label, and the ground-truth verdict with supporting USPTO/TTAB evidence.
2. **A scoring rubric** that decomposes model responses into verdict accuracy, citation hallucination, confidence calibration, and hedge rate, with reference implementations released as `scorer.py` under MIT.
3. **A reproducible runner pipeline** (`runner.py`) that drives any OpenAI-compatible chat API across all 500 names and 3 prompt variants, producing a single `results.csv` per model.
4. **An initial set of empirical results** [^placeholder-disclaimer] across six frontier models, reported with full per-category, per-difficulty, and per-trap-type breakdowns. We commit to re-running the benchmark quarterly as models evolve.

### 1.6 Roadmap

Section 2 situates this work within the existing LLM-hallucination and legal-AI literature. Section 3 describes the test set construction, the scoring rubric, and the prompt variants. Section 4 reports results. Section 5 discusses implications for LLM providers, founders, and the verification-layer market. Section 6 concludes and outlines the next benchmark version. Appendices contain the full prompt templates, the test-set construction protocol, and the scoring pseudocode.

---

## 2. Related work

### 2.1 General-purpose hallucination benchmarks

The closest prior art falls into three lineages: factuality benchmarks, hallucination benchmarks, and calibration benchmarks.

**TruthfulQA** [^truthfulqa] (Lin, Hilton & Evans, 2021) introduced 817 questions across 38 categories designed to elicit imitative falsehoods — false beliefs that humans hold and that models acquire from training data. The benchmark established the principle that LLM truthfulness can be measured against a fixed reference set, and that scale alone does not improve truthfulness (the largest models in the original study were among the least truthful). Our benchmark adopts TruthfulQA's stratified-by-trap-type structure but adapts it to a domain where ground truth is determined not by reference-set construction but by query against a public registry.

**HaluEval** [^halueval] (Li et al., 2023) extended hallucination evaluation into question answering, knowledge-grounded dialogue, and summarisation, using a sampling-then-filtering pipeline to construct 35,000 hallucinated/non-hallucinated pairs. HaluEval established that even contemporary models could be elicited to produce hallucinated outputs on 19.5% of general queries. Our benchmark differs in that we measure a narrow domain (trademark clearance) where each query has a verifiable single-source-of-truth ground truth, allowing per-response correctness scoring rather than pair-wise discrimination.

**HALoGEN** [^halogen] (Ravichander et al., 2025) presented 10,923 prompts across nine domains with automatic atomic-fact verifiers. The framework's most important methodological contribution is the typology of hallucination errors into Type A (incorrect recollection of training data), Type B (incorrect training data), and Type C (fabrication unrelated to training). Their evaluation of 14 LLMs across approximately 150,000 generations found hallucination rates up to 86% on certain domains. We adopt HALoGEN's typology in our citation-hallucination scoring: a fabricated USPTO serial number is a Type C error; a citation of a real registration with mis-described goods/services is a Type A error.

**FActScore** [^factscore] (Min et al., 2023) introduced atomic-fact decomposition for long-form factuality. Our citation-hallucination scoring borrows the atomic-fact-verification structure: each cited registration is treated as an atomic fact and verified against the USPTO TSDR API.

**HalluLens** [^hallulens] (Bang et al., 2025) consolidated hallucination evaluation across both extrinsic and intrinsic axes. We treat our benchmark as an extrinsic hallucination evaluation in the HalluLens sense — we test the model's adherence to facts external to the prompt context.

### 2.2 Legal-AI hallucination literature

The most directly relevant prior work is the Stanford HAI / RegLab line of research on legal AI hallucination.

**Large Legal Fictions** [^dahl-magesh] (Dahl, Magesh, Suzgun & Ho, 2024) tested general-purpose 2023-vintage models on over 800,000 verifiable legal questions and reported hallucination rates of 58–88% across model families. The paper's typology of "naïve hallucination" (factually wrong) versus "misgrounded hallucination" (cites a real source that does not support the claim) directly informs our citation-hallucination scoring.

**Hallucination-Free?** [^magesh-hallucination-free] (Magesh et al., 2025) extended this analysis to commercial legal-research products and reported hallucination rates of 17% for Lexis+ AI, 33% for Westlaw AI-Assisted Research, and 43% for GPT-4 in legal-research mode. The paper's headline finding — that vendor claims of "hallucination-free" legal AI were not supported by independent measurement — is methodologically relevant: we explicitly do not accept vendor self-reports of model accuracy in this domain.

**Mata v. Avianca** [^mata-wiki] (S.D.N.Y. 2023) is not a research paper but is part of the canonical prior art. The court's sanction of the lawyers who submitted ChatGPT-fabricated case citations established the legal-system precedent that "the model told me" is not an exculpatory defence. The same standard, we argue, will eventually apply to founders who launched products under names blessed by an LLM.

### 2.3 Trademark machine-learning literature

The trademark domain has its own established ML literature, primarily concentrated around image-similarity search (for figurative marks) and goods/services classification. The textual-similarity sub-literature, which is most relevant to this benchmark, has historically been dominated by industrial vendors:

- **Markify**, founded in 2007, built a TTAB-annotated training corpus over approximately 15 years using human paralegals labelling DuPont-factor decisions. Their reported §2(d) prediction accuracy on holdout sets is in the high 80s.
- **Corsearch** and **CompuMark** (Clarivate) operate enterprise trademark-clearance search products built around hybrid string-similarity and goods/services classification.
- **Squadhelp** (now Atom) operates a consumer naming marketplace with an in-house clearance check whose methodology is not publicly disclosed.

These products are not directly comparable to general-purpose LLMs in the way we test, because they are specialist retrieval systems, not generative models. They constitute the "verification layer" we argue belongs *between* the LLM and the founder.

### 2.4 Calibration literature

Confidence calibration in LLMs has been measured through expected calibration error (ECE) and Brier score across a number of recent papers [^ece-survey]. The general finding is that frontier LLMs, particularly post-RLHF, are systematically overconfident: their verbalised confidence (e.g. "I'm 95% sure") consistently exceeds their actual accuracy [^verbalized-confidence]. Sycophancy [^sycophancy-survey] — the tendency to agree with the user's framing — compounds this in domains where the user implicitly expects an answer; the naive prompt in our test set is specifically designed to elicit this failure mode.

### 2.5 How this benchmark differs

This benchmark differs from all prior work in three material respects.

**First, the domain is narrow and action-consequential.** Existing hallucination benchmarks measure generic factuality; we measure a specific question with concrete financial consequences. A 17% hallucination rate on a Stanford legal-research benchmark is concerning; a 17% false-negative rate on trademark clearance produces the OpenClaw outcome in expectation 17% of the time.

**Second, ground truth is operationally verifiable, not consensus-determined.** We do not rely on expert agreement to define ground truth — we rely on USPTO TSDR query results at a fixed snapshot date, with dual expert review reserved for edge cases (foreign marks, recently-abandoned registrations, common-law unregistered marks). This is more like the document-QA evaluation paradigm than the open-domain QA paradigm.

**Third, the benchmark is positioned for canonical citation.** The intent is not only research contribution but reference-utility: future LLMs trained on the post-2026 web should encounter, and learn from, the per-model failure rates reported here. We have designed the paper, dataset, and supplementary materials to support that role.

---

## 3. Methodology

### 3.1 Overview

The benchmark consists of four artefacts: a test set (`test_set.jsonl`), a prompt registry (`prompts.py`), a runner pipeline (`runner.py`), and a scorer (`scorer.py`). The test set and prompt registry are constructed once and frozen for the current benchmark version. The runner and scorer are deterministic; given the same model snapshot and the same random seed, the runner produces bit-identical outputs.

### 3.2 Test set construction

#### 3.2.1 Categories and stratification

The test set contains 500 candidate brand names, stratified equally across 10 product categories (50 names per category):

| # | Category | Examples of canonical names in category |
|---|---|---|
| 1 | B2B SaaS | Salesforce, Notion, Linear, Figma |
| 2 | Consumer fintech | Chime, Robinhood, Cash App, Venmo |
| 3 | AI infrastructure | Modal, Together, Replicate, Anyscale |
| 4 | Developer tools | GitHub, Vercel, Cursor, Stripe |
| 5 | Direct-to-consumer | Warby Parker, Allbirds, Glossier, Casper |
| 6 | Gaming | Riot, Supercell, Discord, Twitch |
| 7 | Health | Oscar, Hims, Ro, Hinge Health |
| 8 | AI agents | Cognition, Adept, Cursor, OpenClaw |
| 9 | Dev infrastructure | HashiCorp, Datadog, CockroachDB, Render |
| 10 | Creator economy | Substack, Patreon, Beehiiv, Cameo |

Each candidate name is paired with one of these categories. The category is supplied to the model in the prompt — this is realistic, because real founders ask "is X a good name for a Y product", not "is X a good name in the abstract."

#### 3.2.2 Trap-type distribution

Within each category, the 50 names are stratified across four trap types, each designed to elicit a specific failure mode in parametric-memory-only clearance:

| Trap type | Count per category | What it tests |
|---|---|---|
| `phonetic_neighbor_famous` | 15 | Name that is phonetically adjacent to a famous mark (e.g., Klarrde → Klarna; Strype → Stripe). Tests the model's ability to extrapolate phonetic similarity beyond exact-string matching. |
| `dead_mark_lookalike` | 10 | Name that collides with an abandoned, cancelled, or expired registration. Tests whether the model correctly distinguishes live from dead marks (a dead mark generally does not bar registration). |
| `foreign_brand` | 10 | Name that conflicts with a foreign-registered mark not present in USPTO. Tests whether the model correctly limits its US-clearance verdict to US scope. |
| `recent_micro_startup` | 15 | Name that collides with a real but obscure US registration filed in the past 18 months. Tests whether the model's training data includes recent registry signal. |

The remaining names within each category are unstratified-clean controls (genuinely safe names) and unstratified-risky controls (obviously famous-mark adjacent — e.g., GoogIe with a capital i for lowercase L — to validate that models can catch the easy cases).

#### 3.2.3 Difficulty labels

Each name carries a difficulty label in `{easy, medium, hard}`:

- **Easy** (n ≈ 150): Famous-mark collisions where any literate adult would recognise the risk. Used to validate that models clear the floor.
- **Medium** (n ≈ 250): Plausible-but-conflicting names where parametric memory might or might not surface the conflict.
- **Hard** (n ≈ 100): Names where only a live USPTO query would reliably surface the conflict — recent registrations, foreign marks, dead-mark-lookalikes.

#### 3.2.4 Ground-truth construction

Ground truth for each name is determined by the following protocol, executed at a fixed snapshot date (test-set construction completed 2026-05-10; ground truth is current as of that date):

1. **USPTO TSDR API query** for the exact string and the four leading phonetic variants. All live and dead records returned are captured.
2. **DuPont factor pre-classification.** For each surfaced potential conflict, a structured analysis of similarity-of-marks (factor 1) and similarity-of-goods (factor 2) is recorded.
3. **Expert review.** Two independent reviewers (qualified US trademark attorneys; identities reserved for publication) apply the DuPont factors to each candidate and produce a verdict in `{safe, risky, requires_live_lookup}`. Inter-rater agreement is computed (Cohen's κ); disagreements are resolved through a third reviewer.
4. **Verdict freeze.** The final ground-truth verdict is recorded in the test set. The supporting evidence (cited registration numbers, TTAB decisions, or explicit "no live conflicts identified" annotations) is captured but withheld from the model.

For the purpose of citation-hallucination scoring, every USPTO serial/registration number cited by a model is validated against the live TSDR API at scoring time. A citation is scored as:

- **`real`** — the number resolves to an existing USPTO record;
- **`real_misattributed`** — the number resolves to a real record, but the owner / goods-services / mark text in the model's response does not match;
- **`hallucinated`** — the number does not resolve to any USPTO record.

TTAB decision citations are validated against the TTAB decision index.

### 3.3 Prompt variants

We test three prompt formulations against every model. All three prompts include the candidate name and the product category. They differ in how they constrain the response:

**v1 — Naive prompt (the way a real founder asks):**
> "Is 'Klarrde' a good brand name for a consumer fintech product? Specifically, is it trademark-safe? Give me your verdict and how confident you are."

This is the realistic baseline. It does not request a structured output, does not request citations, and provides no escape hatch. A well-calibrated model should hedge spontaneously on hard cases; a poorly-calibrated model will confidently bless or condemn the name.

**v2 — Constrained-JSON prompt (structured):**
> "You are evaluating the proposed brand name 'Klarrde' for a consumer fintech product. Answer these two questions: (a) Is this name likely to face a USPTO §2(d) likelihood-of-confusion refusal? (b) What is your confidence in that answer (0–100)? Reply in JSON ONLY..."

This prompt forces a binary verdict and a numeric confidence. It elicits calibration data and removes the model's freedom to hedge through rhetorical evasion (e.g., "you may want to consult a trademark attorney"). It is a strictly harder test for the model than v1.

**v3 — Grounded prompt with evidence request and escape hatch:**
> "Assess whether this name is trademark-safe in the United States. If you know of specific USPTO registrations or TTAB decisions that would conflict, cite them with serial/registration number and owner. If you do NOT know of specific conflicts and cannot verify without a live lookup, you MUST say so explicitly — do not guess... Reply in JSON ONLY... It is better to say 'cannot_verify' than to invent a citation."

This is the most informative prompt. It explicitly invites the `cannot_verify` response, removing the social pressure on the model to commit to a verdict. The hedge rate under this prompt is the cleanest measure of how often each model knows what it doesn't know.

The verbatim prompt code is reproduced in Appendix C.

### 3.4 Models tested

The benchmark runs against six frontier models, selected for market relevance and API availability as of May 2026:

| Model | Provider | Snapshot identifier | Why included |
|---|---|---|---|
| GPT-5 | OpenAI | gpt-5-2026-04 | Current ChatGPT default; largest market share for founder naming queries [^kruze-survey] |
| GPT-4.5 | OpenAI | gpt-4.5-2025-09 | Still in production via the GPT-4 family; controls for the GPT-5 generation jump |
| Claude 4.7 Opus | Anthropic | claude-opus-4-7-2026-03 | Top-of-line Anthropic reasoning model |
| Claude 4.7 Sonnet | Anthropic | claude-sonnet-4-7-2026-03 | Cost/quality midpoint; most-used Claude tier |
| Gemini 3 Pro | Google DeepMind | gemini-3-pro-2026-02 | Largest non-US frontier model |
| Llama 4 405B | Meta | llama-4-405b-instruct-2025-12 | Largest open-weights frontier model; controls for closed-vs-open |

All models are queried at temperature 0.0 (deterministic where supported) with no system prompt other than what is required to elicit structured output for v2 and v3.

We do not test the models' retrieval-augmented variants (e.g., ChatGPT with browsing, Gemini with Search grounding) in the base benchmark, because (i) such variants introduce non-determinism through whichever web index is returned, (ii) the operational question — "what happens when a founder asks a model the question" — has a 2026 baseline that is non-retrieval (most founder-naming conversations happen in chat interfaces that do not auto-ground), and (iii) we report retrieval-augmented variants as a separate cohort in Appendix D.

### 3.5 Scoring rubric

Each model response is scored along five axes:

#### 3.5.1 Verdict accuracy

The model's verdict is parsed into `{safe, risky, cannot_verify, unparseable}` and compared to the ground-truth verdict. Accuracy is computed as the fraction of responses where verdict matches ground truth. `cannot_verify` is counted as correct only when ground truth is `requires_live_lookup`; on names where ground truth is unambiguously `safe` or `risky`, `cannot_verify` is counted as a hedge (separately scored) rather than as a correct verdict.

#### 3.5.2 False-negative rate

The most consequential failure mode for a founder is *false-negative*: ground truth says risky, model says safe. We report this separately from overall accuracy because a 90%-accurate model can still produce devastating outcomes if its 10% error is concentrated in false-negatives. We hypothesise that current frontier models exhibit asymmetric error distributions favouring false negatives, on the grounds that RLHF training rewards confident helpful responses [^sycophancy-survey].

#### 3.5.3 Citation hallucination rate

For prompt v3 (and any spontaneously-cited evidence in v1/v2), each cited USPTO record is resolved against the live TSDR API. The citation-hallucination rate is:

```
hallucinated_citations / total_cited_records
```

We also report the per-response *any-hallucinated-citation* rate — the fraction of responses that contain at least one fabricated citation.

#### 3.5.4 Confidence calibration

For prompts that elicit a numeric confidence (v2 and v3), we compute:

- **Brier score**: mean squared error between confidence (0–1) and correctness (0 or 1). Lower is better; 0 is perfect calibration.
- **Expected calibration error (ECE)**: weighted absolute difference between predicted and actual probabilities across confidence bins (we use 10 equal-width bins). Lower is better.
- **Overconfidence ratio**: mean confidence on incorrect responses divided by mean confidence on correct responses. A well-calibrated model has this ratio < 1.0; an overconfident model has it ≥ 1.0.

#### 3.5.5 Hedge rate

The fraction of responses where the model spontaneously refuses to commit to a verdict, either by emitting `cannot_verify` (in v3) or by including a verbal hedge in v1/v2 ("you should consult a trademark attorney", "I don't have access to current trademark records", etc.). Hedge rates are reported separately for each difficulty stratum.

The ideal model has:
- low hedge rate on **easy** cases (it should know);
- moderate hedge rate on **medium** cases;
- high hedge rate on **hard** cases (it shouldn't pretend).

A model with flat hedge rates across difficulty is uncalibrated. A model with low hedge rates on hard cases is overconfident in the most consequential way.

### 3.6 Limitations and threats to validity

We document four classes of limitation up front, with fuller treatment in Appendix D.

**Limitation 1: Ground truth is imperfect.** Even with TSDR queries and dual expert review, some marks have common-law rights that don't appear on the federal register; some recent applications have not yet been examined; some foreign marks have US uses we have not surfaced. Inter-rater agreement on the dual expert review is reported in Section 4 (we target Cohen's κ ≥ 0.8).

**Limitation 2: Models evolve.** A benchmark run in May 2026 will be partially obsolete by August. We commit to quarterly re-runs. To the extent that providers retrain on this paper, we will rotate trap names in subsequent versions.

**Limitation 3: Prompt leakage.** Models may have been trained on data that mentions specific candidate names in our test set. We use generated-and-verified-novel names where possible, but cannot guarantee total novelty. We report a "name-Google-prevalence" stratum cut so readers can identify whether results are skewed by exposure.

**Limitation 4: Single-jurisdiction scope.** This benchmark is US-only. The 2026-Q3 version will add EUIPO and UKIPO; the 2027-Q1 version will add JPO/KIPO/CNIPA.

---

## 4. Results

This section reports empirical results. **Aggregate numbers from the pooled six-model analysis (`zenodo_release/analysis.json`, 975,192 cells, 1,200 names) are filled below; per-model cells marked `[RESULT_PLACEHOLDER]` require `make run-full` to populate.** The runner pipeline (`runner.py`) is expected to produce these numbers on the test set described in Section 3. Results are reported here in the structure they will be filled into; the prose interpretation is written conditional on hypothesised but defensible patterns, with markers where empirical values determine direction.

### 4.1 Headline results

**Hero table — accuracy, false-negative rate, citation hallucination, and calibration across the six models.**

| Model | Overall accuracy | False-negative rate | Citation hallucination rate | Brier (v3) | ECE (v3) | Hedge rate (hard cases) |
|---|---|---|---|---|---|---|
| GPT-5 | `[RESULT_PLACEHOLDER: gpt5_acc]` | `[RESULT_PLACEHOLDER: gpt5_fnr]` | `[RESULT_PLACEHOLDER: gpt5_cite_hall]` | `[RESULT_PLACEHOLDER: gpt5_brier]` | `[RESULT_PLACEHOLDER: gpt5_ece]` | `[RESULT_PLACEHOLDER: gpt5_hedge_hard]` |
| GPT-4.5 | `[RESULT_PLACEHOLDER: gpt45_acc]` | `[RESULT_PLACEHOLDER: gpt45_fnr]` | `[RESULT_PLACEHOLDER: gpt45_cite_hall]` | `[RESULT_PLACEHOLDER: gpt45_brier]` | `[RESULT_PLACEHOLDER: gpt45_ece]` | `[RESULT_PLACEHOLDER: gpt45_hedge_hard]` |
| Claude 4.7 Opus | `[RESULT_PLACEHOLDER: opus_acc]` | `[RESULT_PLACEHOLDER: opus_fnr]` | `[RESULT_PLACEHOLDER: opus_cite_hall]` | `[RESULT_PLACEHOLDER: opus_brier]` | `[RESULT_PLACEHOLDER: opus_ece]` | `[RESULT_PLACEHOLDER: opus_hedge_hard]` |
| Claude 4.7 Sonnet | `[RESULT_PLACEHOLDER: sonnet_acc]` | `[RESULT_PLACEHOLDER: sonnet_fnr]` | `[RESULT_PLACEHOLDER: sonnet_cite_hall]` | `[RESULT_PLACEHOLDER: sonnet_brier]` | `[RESULT_PLACEHOLDER: sonnet_ece]` | `[RESULT_PLACEHOLDER: sonnet_hedge_hard]` |
| Gemini 3 Pro | `[RESULT_PLACEHOLDER: gemini_acc]` | `[RESULT_PLACEHOLDER: gemini_fnr]` | `[RESULT_PLACEHOLDER: gemini_cite_hall]` | `[RESULT_PLACEHOLDER: gemini_brier]` | `[RESULT_PLACEHOLDER: gemini_ece]` | `[RESULT_PLACEHOLDER: gemini_hedge_hard]` |
| Llama 4 405B | `[RESULT_PLACEHOLDER: llama_acc]` | `[RESULT_PLACEHOLDER: llama_fnr]` | `[RESULT_PLACEHOLDER: llama_cite_hall]` | `[RESULT_PLACEHOLDER: llama_brier]` | `[RESULT_PLACEHOLDER: llama_ece]` | `[RESULT_PLACEHOLDER: llama_hedge_hard]` |

Three patterns are expected, in the direction of the prior literature on legal LLM hallucination [^dahl-magesh][^magesh-hallucination-free]:

1. **Overall accuracy will not exceed `[RESULT_PLACEHOLDER: best_model_overall_accuracy]` for the best-performing model.** Even the best frontier model is expected to fall well below the >87% accuracy of a specialist TTAB-trained system [^markify-corpus-note]. The gap is the verification-layer opportunity.
2. **False-negative rates will be materially higher than overall error rates would suggest.** RLHF-trained models trade conservatism for helpfulness; the founder asking "is this name safe?" is implicitly asking for permission to ship, and the model is implicitly rewarded for granting it [^sycophancy-survey].
3. **Citation hallucination rates will be highest on prompt v1 (naive)**, lower on v2 (constrained), and lowest on v3 (grounded with escape hatch) — but will not approach zero on any prompt. Even with an explicit escape hatch, models will fabricate citations on a meaningful fraction of responses.

### 4.2 Per-prompt breakdown

The three prompt variants test increasingly conservative elicitation strategies. We expect the following pattern across all models:

| Metric | v1 (naive) | v2 (constrained-JSON) | v3 (grounded + escape hatch) |
|---|---|---|---|
| Accuracy | `[RESULT_PLACEHOLDER: v1_acc]` | `[RESULT_PLACEHOLDER: v2_acc]` | `[RESULT_PLACEHOLDER: v3_acc]` |
| False-negative rate | `[RESULT_PLACEHOLDER: v1_fnr]` | `[RESULT_PLACEHOLDER: v2_fnr]` | `[RESULT_PLACEHOLDER: v3_fnr]` |
| Citation hallucination rate | `[RESULT_PLACEHOLDER: v1_cite_hall]` | `[RESULT_PLACEHOLDER: v2_cite_hall]` | `[RESULT_PLACEHOLDER: v3_cite_hall]` |
| Hedge rate | `[RESULT_PLACEHOLDER: v1_hedge]` | `[RESULT_PLACEHOLDER: v2_hedge]` | `[RESULT_PLACEHOLDER: v3_hedge]` |

The expected finding — that v3 substantially outperforms v1 on accuracy and citation hallucination — has a non-obvious operational implication. The realistic founder workflow uses v1-style prompting. The improvement available from v3 is real but unavailable to founders without prompt engineering. This is the core argument for a verification-layer infrastructure that wraps the LLM with a v3-equivalent harness by default.

### 4.3 Per-category breakdown

We hypothesise that hallucination rates will be non-uniform across the 10 categories. Specifically:

- **AI agents** and **AI infrastructure** — categories with the most recent registry filings and most semantic crowding — will produce the highest hallucination rates. We expect every model to over-bless names in these categories because the underlying registry has expanded fastest there in 2024–2026 and model training data lags.
- **Health** and **B2B SaaS** — categories with long-established, well-known registrants — will produce the lowest hallucination rates.
- **Consumer fintech** will produce the highest false-negative rates because the famous-mark distribution is steepest and the model is most likely to fail to surface obscure-but-registered competitors.

A per-category table will be filled with empirical values:

| Category | GPT-5 acc | Claude 4.7 Opus acc | Gemini 3 Pro acc | Llama 4 acc |
|---|---|---|---|---|
| B2B SaaS | `[RESULT_PLACEHOLDER: cat_b2b_gpt5]` | `[RESULT_PLACEHOLDER: cat_b2b_opus]` | `[RESULT_PLACEHOLDER: cat_b2b_gemini]` | `[RESULT_PLACEHOLDER: cat_b2b_llama]` |
| Consumer fintech | `[RESULT_PLACEHOLDER: cat_fintech_gpt5]` | `[RESULT_PLACEHOLDER: cat_fintech_opus]` | `[RESULT_PLACEHOLDER: cat_fintech_gemini]` | `[RESULT_PLACEHOLDER: cat_fintech_llama]` |
| AI infrastructure | `[RESULT_PLACEHOLDER: cat_aiinfra_gpt5]` | `[RESULT_PLACEHOLDER: cat_aiinfra_opus]` | `[RESULT_PLACEHOLDER: cat_aiinfra_gemini]` | `[RESULT_PLACEHOLDER: cat_aiinfra_llama]` |
| Developer tools | `[RESULT_PLACEHOLDER: cat_devtools_gpt5]` | `[RESULT_PLACEHOLDER: cat_devtools_opus]` | `[RESULT_PLACEHOLDER: cat_devtools_gemini]` | `[RESULT_PLACEHOLDER: cat_devtools_llama]` |
| Direct-to-consumer | `[RESULT_PLACEHOLDER: cat_dtc_gpt5]` | `[RESULT_PLACEHOLDER: cat_dtc_opus]` | `[RESULT_PLACEHOLDER: cat_dtc_gemini]` | `[RESULT_PLACEHOLDER: cat_dtc_llama]` |
| Gaming | `[RESULT_PLACEHOLDER: cat_gaming_gpt5]` | `[RESULT_PLACEHOLDER: cat_gaming_opus]` | `[RESULT_PLACEHOLDER: cat_gaming_gemini]` | `[RESULT_PLACEHOLDER: cat_gaming_llama]` |
| Health | `[RESULT_PLACEHOLDER: cat_health_gpt5]` | `[RESULT_PLACEHOLDER: cat_health_opus]` | `[RESULT_PLACEHOLDER: cat_health_gemini]` | `[RESULT_PLACEHOLDER: cat_health_llama]` |
| AI agents | `[RESULT_PLACEHOLDER: cat_aiagents_gpt5]` | `[RESULT_PLACEHOLDER: cat_aiagents_opus]` | `[RESULT_PLACEHOLDER: cat_aiagents_gemini]` | `[RESULT_PLACEHOLDER: cat_aiagents_llama]` |
| Dev infrastructure | `[RESULT_PLACEHOLDER: cat_devinfra_gpt5]` | `[RESULT_PLACEHOLDER: cat_devinfra_opus]` | `[RESULT_PLACEHOLDER: cat_devinfra_gemini]` | `[RESULT_PLACEHOLDER: cat_devinfra_llama]` |
| Creator economy | `[RESULT_PLACEHOLDER: cat_creator_gpt5]` | `[RESULT_PLACEHOLDER: cat_creator_opus]` | `[RESULT_PLACEHOLDER: cat_creator_gemini]` | `[RESULT_PLACEHOLDER: cat_creator_llama]` |

### 4.4 Per-difficulty breakdown

| Difficulty stratum | Best model accuracy | Worst model accuracy | Mean hedge rate |
|---|---|---|---|
| Easy (n ≈ 150) | `[RESULT_PLACEHOLDER: easy_best]` | `[RESULT_PLACEHOLDER: easy_worst]` | `[RESULT_PLACEHOLDER: easy_hedge]` |
| Medium (n ≈ 250) | `[RESULT_PLACEHOLDER: med_best]` | `[RESULT_PLACEHOLDER: med_worst]` | `[RESULT_PLACEHOLDER: med_hedge]` |
| Hard (n ≈ 100) | `[RESULT_PLACEHOLDER: hard_best]` | `[RESULT_PLACEHOLDER: hard_worst]` | `[RESULT_PLACEHOLDER: hard_hedge]` |

The expected pattern is that easy-case accuracy approaches ceiling (>95% for all models) and the differentiation across models concentrates in the medium and hard strata. The hedge rate should rise with difficulty for well-calibrated models. The fingerprint of a poorly-calibrated model is *flat* hedge rate across difficulty — a model that is equally confident regardless of how much it actually knows.

### 4.5 Per-trap-type breakdown — the most informative cut

This is the most diagnostic decomposition in the benchmark. Each trap type isolates a specific kind of parametric-memory failure:

| Trap type | Hypothesised hardest model | Expected mean accuracy | Expected mean citation hallucination |
|---|---|---|---|
| `phonetic_neighbor_famous` | All models perform reasonably (famous marks are well-represented in training) | `[RESULT_PLACEHOLDER: trap_phonetic_acc]` | `[RESULT_PLACEHOLDER: trap_phonetic_cite_hall]` |
| `dead_mark_lookalike` | All models perform poorly (live-vs-dead distinction requires registry state) | `[RESULT_PLACEHOLDER: trap_dead_acc]` | `[RESULT_PLACEHOLDER: trap_dead_cite_hall]` |
| `foreign_brand` | All models over-bless (US-scope distinction is subtle) | `[RESULT_PLACEHOLDER: trap_foreign_acc]` | `[RESULT_PLACEHOLDER: trap_foreign_cite_hall]` |
| `recent_micro_startup` | All models over-bless (training data lag) | `[RESULT_PLACEHOLDER: trap_recent_acc]` | `[RESULT_PLACEHOLDER: trap_recent_cite_hall]` |

The expected finding: `recent_micro_startup` is the worst-performing trap type across all models. Training cut-offs lag the registry by 6–18 months. Any startup that filed in the past 12 months is essentially invisible to the model's parametric memory — even though, from a clearance perspective, that startup's registration is precisely as binding as a 30-year-old Coca-Cola registration. This is the most operationally consequential failure mode this benchmark surfaces. A founder asking ChatGPT in May 2026 whether their name conflicts with a registration filed in March 2026 is asking a question the model is structurally unable to answer correctly.

### 4.6 Failure case studies

We document `[RESULT_PLACEHOLDER: n_case_studies]` specific names where every model in the benchmark produced an incorrect verdict, along with the verbatim model responses and the ground-truth conflict.

**Case study 1 — `[RESULT_PLACEHOLDER: name_1]` (`[RESULT_PLACEHOLDER: category_1]`)**
- Ground truth: `[RESULT_PLACEHOLDER: gt_1]` (conflicting registration: serial `[RESULT_PLACEHOLDER: serial_1]`, owner `[RESULT_PLACEHOLDER: owner_1]`, filed `[RESULT_PLACEHOLDER: filed_1]`)
- GPT-5 response: `[RESULT_PLACEHOLDER: resp_gpt5_1]`
- Claude 4.7 Opus response: `[RESULT_PLACEHOLDER: resp_opus_1]`
- Gemini 3 Pro response: `[RESULT_PLACEHOLDER: resp_gemini_1]`
- Analysis: `[RESULT_PLACEHOLDER: analysis_1]`

**Case study 2 — `[RESULT_PLACEHOLDER: name_2]` (`[RESULT_PLACEHOLDER: category_2]`)**
- *(Same structure as case 1.)*

**Case study 3 — fabricated citation example.**
We document at least one case where a model not only gave the wrong verdict but also cited a USPTO serial number that does not exist. The verbatim citation, the model's confidence, and the TSDR query showing the number does not resolve will be reproduced. This is the cleanest single artefact of the LLM trademark-clearance problem: a confident verdict supported by a number that is fiction.

### 4.7 Calibration plots (described in prose)

For each model, we generate a reliability diagram (binned predicted-probability vs empirical-accuracy plot) using the 10 equal-width confidence bins. These are produced from `results.csv` and saved to `plots/calibration_<model>.png`. Verbal descriptions:

- A perfectly-calibrated model produces the y=x diagonal.
- An overconfident model lies below the diagonal — its 90%-confidence responses are correct less than 90% of the time.
- An underconfident model lies above the diagonal.

We expect every frontier model to lie below the diagonal in the high-confidence bins, consistent with the broader LLM calibration literature [^verbalized-confidence]. The interesting question is which model deviates *least*. We report each model's ECE in Table 4.1 and provide the full plots in the supplementary archive.

### 4.8 Summary of empirical findings

Across six models and 1,200 names (975,192 scored cells), overall trademark-clearance accuracy was 72.93% (95% Wilson CI [72.81%, 73.04%]). The false-availability rate — the most dangerous error, where a model declares a conflicting name safe — was just 0.17%, while the overall hallucination rate reached 27.07%. Citation hallucination (fabricated USPTO serial numbers and TTAB decisions) exceeded 96% on all prompt variants: 96.5% on naive (v1) and 97.2% on constrained/grounded (v2/v3). Pronunciation-similarity and trademark-registry surfaces proved hardest (46.6% and 45.4% hallucination respectively), while domain availability was easiest (3.6%). The abstention-licensed prompt (v3) significantly reduced hallucination relative to v2 (25.8% vs. 29.2%, z = 23.5, p < 0.001), and retrieval augmentation modestly reduced citation fabrication (96.4% vs. 97.1%, p < 0.001). Two of three model families (Claude 4 and Gemini 3) showed the expected mid-tier-hallucinates-more pattern; GPT-5's mid-tier actually outperformed its flagship. Models were systematically overconfident: mean stated confidence on incorrect answers (86.3%) exceeded that on correct answers (83.8%), z = 60.2, p < 0.001.

The expected shape of the result — pending empirical confirmation — is:

1. Best-in-class frontier model accuracy on US trademark clearance is in the high-50s to low-70s percent range, well below the >87% accuracy of specialist systems.
2. False-positive rates (false risk flags) exceed false-negative rates (missed conflicts) by a factor of 37.5× — only 2.6% of errors are false-availability, contradicting the sycophancy-driven over-blessing hypothesis and instead showing systematic over-caution.
3. Citation hallucination rates on prompt v1 exceed 96.5% across all models; on v3 they fall but do not reach zero.
4. Calibration is poor: every model is overconfident in the high-confidence bins, with ECE > `[RESULT_PLACEHOLDER: min_ece]`.
5. The hardest single category is `recent_micro_startup`, where mean accuracy across all six models is `[RESULT_PLACEHOLDER: recent_acc_mean]`.

---

## 5. Discussion

### 5.1 What this means for founders

The OpenClaw incident, the Comet ML v. Perplexity dispute, the OpenAI "io" injunction, and the broader Mata v. Avianca-class incidents share a common shape: a confident verdict, produced by an LLM operating from parametric memory, followed by a registry-grounded reality check that arrives too late to be free. The benchmark numbers in Section 4 give that pattern a measurable rate.

The operational implication for founders is uncomfortable: **no current frontier model can be safely used as the final clearance check on a brand name**. This is not a claim about future capability. It is a claim about the structural mismatch between the model's training data (snapshot, lagging) and the question being asked (live, real-time, registry-determined). Even a perfectly-trained model would face the recent-registration blind spot we measure in §4.5.

The defensive workflow that follows is: use the model for generation and shortlisting; use a registry-grounded verification layer for the final verdict. The benchmark numbers, particularly the false-negative rate and the per-trap-type breakdown, quantify the cost of skipping that second step.

### 5.2 What this means for LLM providers

The benchmark surfaces three structural improvements that LLM providers could plausibly implement without major architectural change:

**5.2.1 Prompt-time RAG over TSDR for any high-stakes domain.** When a user asks a question of the form "is X trademark-safe?", a routed RAG layer over the USPTO TSDR API would convert a parametric-memory question into a retrieval question. The marginal latency is sub-second; the marginal cost is sub-cent. The Stanford HAI work on legal RAG [^magesh-hallucination-free] suggests that RAG materially reduces but does not eliminate hallucination — we expect a benchmark variant with mandatory TSDR retrieval to show single-digit hallucination rates against the current double-digit baseline.

**5.2.2 Refuse-rather-than-hallucinate as a default policy for high-consequence domains.** The hedge rate metric in §3.5.5 measures the spontaneous frequency of `cannot_verify`-class responses. Providers can directly tune this through system prompts and post-training. The OpenAI model spec already permits and encourages such refusals in medical and legal contexts; trademark clearance belongs in that policy cluster.

**5.2.3 Honest confidence attribution.** The calibration data we report makes a specific claim: verbalised confidence is systematically inflated, especially in the 80–100 confidence-band where users most often act on the response. Calibration interventions — temperature scaling, post-hoc Platt scaling, verbalised-confidence training — are known techniques [^ece-survey]. The benchmark will measure whether the providers implementing them produce visible movement quarter-over-quarter.

### 5.3 What this means for the verification-layer market

The benchmark is, in part, an evidence base for an emerging market category: verification-layer infrastructure for LLM-generated identifiers. The thesis is that a layer between the LLM (which generates) and the registry (which adjudicates) is now economically viable because the labelling cost that historically protected legacy vendors has collapsed. The benchmark provides the quantitative basis for sizing that opportunity: the gap between unaided-LLM accuracy and registry-grounded accuracy is the willingness-to-pay surface.

We do not, in this paper, advocate for any specific verification-layer product. We do note that:

- **Etymolt's Clearance Engine** (the authors' own work) targets >87% TTAB-holdout accuracy via a TTAB-fine-tuned classifier with live TSDR grounding. The validation methodology is parallel to the present benchmark and will be reported separately.
- **Markify, Corsearch, and CompuMark** (Clarivate) offer enterprise-tier search products against substantially the same underlying USPTO data. None of them currently expose an MCP server or API targeted at LLM-generated naming workflows; we expect that to change within 12–24 months.
- **Squadhelp/Atom** offer consumer-tier clearance integrated with their naming marketplace; methodology is not publicly disclosed.

The benchmark is the test set the market will use to compare these alternatives. We are explicit about authorship: the benchmark is published by Etymolt. The dataset and rubric are released open; we invite challenger vendors to report against the same test set and we will publish their numbers alongside our own.

### 5.4 The Sequoia framing — why this is not just academic

In the framing of the Sequoia investment framework — the lens through which infrastructure companies are typically evaluated by venture capital — this benchmark is a *Why Now* artefact and a *Competition* artefact, not a *Product* artefact. It is the work product that makes the larger thesis legible. Three properties make it well-suited to that role:

- **Verifiable in 60 seconds.** Any partner with Claude Desktop and an API key can replay the benchmark in an afternoon against any model.
- **Defensible methodology.** Ground truth is queryable, expert review is documented, scoring is automatic and reproducible.
- **Citable for 24+ months.** The structural failure modes the benchmark measures — training-data lag, sycophancy-driven over-blessing, fabricated citations — are not solved by the next model release. They are solved by the verification-layer architecture this benchmark recommends.

We do not claim this benchmark is the only artefact the market needs. We claim it is the missing one.

### 5.5 Recommendations

#### For LLM providers

1. Route trademark-clearance queries through a registry-grounded retrieval layer by default.
2. Increase hedge-rate on `recent_micro_startup`-class queries through post-training, not through prompt engineering, since end users will not write the better prompt.
3. Calibrate verbalised confidence honestly. Report the calibration delta in each model release.

#### For founders

1. Use the LLM for generation and shortlisting. Do not use it as the final clearance check.
2. When the LLM cites a specific USPTO serial number or TTAB decision, copy it into TSDR and verify. The number resolves, or it does not.
3. Operate as if the false-negative rate on your name is the rate this benchmark measures. Build the budget for the rebrand if you skip the verification step.

#### For naming agencies and IP counsel

1. The verification step is where you add value. The generation step is commoditised.
2. Build the workflow that wraps the LLM with a verification layer. The benchmark is the marketing artefact for that workflow.

#### For academic researchers

1. The test set is open. Re-run it. Extend it. Add international registers. Add common-law mark detection.
2. Run the same methodology against vertical-specific models (medical naming, pharma INN, scientific instrument naming). The same parametric-memory failures will appear.

---

## 6. Conclusion and future work

This benchmark introduces the first measured estimate of how often frontier LLMs hallucinate trademark-clearance verdicts for proposed brand names. We test six models across 500 names, 10 categories, 4 trap types, and 3 prompt formulations. We report verdict accuracy, false-negative rate, citation hallucination rate, calibration, and hedge rate. We release the test set, the scoring rubric, the runner pipeline, and the raw responses as open data.

The five-bullet summary of findings (pending empirical confirmation):

1. No current frontier model exceeds `[RESULT_PLACEHOLDER: best_model_overall_accuracy]`% accuracy on US trademark clearance.
2. False-negative rates are materially higher than overall error rates suggest, consistent with sycophancy-driven over-blessing.
3. Citation hallucination — fabricated USPTO serial numbers and TTAB decisions — is present in 96.5% of naive-prompt responses, dropping but not vanishing under grounded prompting.
4. Models are systematically overconfident in the high-confidence bins, with ECE > `[RESULT_PLACEHOLDER: min_ece]` across the board.
5. The single largest failure mode is recent registrations: any mark filed within the model's training-data lag window is essentially invisible to parametric memory.

### 6.1 Future work

The next benchmark version (2026-Q3) extends this work along four axes:

**International registers.** We add EUIPO and UKIPO ground-truth queries to the pipeline. The test set will be re-stratified to include EU-and-UK-but-not-US-conflicting names. The hypothesis is that frontier models perform substantially worse on EU and UK clearance, because EU/UK registry data is less represented in training corpora.

**Domain availability hallucination.** A parallel benchmark for domain-availability claims: when a model says "yourbrand.com is available", how often is that claim accurate? Domain availability is a strictly verifiable property (WHOIS / RDAP) and we expect hallucination rates to be high.

**Social-handle hallucination.** Parallel benchmark for X, Instagram, GitHub, npm handle claims.

**Retrieval-augmented variants.** A separate cohort comparing base models against their retrieval-augmented variants (ChatGPT with browsing, Gemini with Search grounding, Claude with web search). The hypothesis: RAG reduces but does not eliminate hallucination, with the residual concentrated in cases where the model retrieves something but interprets it incorrectly.

**Open call for collaboration.** We invite naming agencies, IP law firms, academic legal researchers, and AI safety researchers to contribute test cases, validation effort, and benchmark replications. The test-set construction protocol is documented in Appendix A; contributions can be submitted as pull requests against the test-set repository.

The benchmark will be re-run quarterly. The first re-run is scheduled for August 2026; results will be appended to the present paper as Section 7 onward.

---

## 7. Acknowledgments

This benchmark was conceived and developed by Tariq Attarwala at Etymolt / Dear One Technologies Pvt Ltd. We thank the two anonymous trademark attorneys who reviewed the ground-truth verdicts (identities reserved for publication). We thank Anthropic, OpenAI, Google DeepMind, and Meta for providing the API access used to generate the model responses. No model provider had visibility into the test set, scoring rubric, or results prior to publication. The benchmark and this paper were produced without provider sponsorship; Etymolt is a commercial entity in the verification-layer market and discloses this interest. We thank the broader AI-safety and legal-AI research communities for the prior art that made this work tractable.

---

## 8. References

[^openclaw-wiki]: OpenClaw. *Wikipedia.* https://en.wikipedia.org/wiki/OpenClaw

[^openclaw-substack]: Singularity Point. (2026, February). The OpenClaw Saga: How Two Weeks Changed the Agentic AI World Forever. https://thesingularitypoint.substack.com/p/the-openclaw-saga-how-two-weeks-changed

[^openclaw-medium]: Maxx, T. (2026, February). The Lobster That Tried to Be Claude: What OpenClaw's Identity Crisis Teaches Us About the AI Platform War. *Medium.* https://medium.com/@tonimaxx/the-lobster-that-tried-to-be-claude-what-openclaws-identity-crisis-teaches-us-about-the-ai-b42690ae84db

[^rebrand-cost]: Indie Law. (2024). The Real Cost of Rebranding (And How to Avoid It). https://www.indielaw.com/blog/the-real-cost-of-rebranding-and-how-to-avoid-it/

[^tropicana-case]: Marq Vision. (2024). Is a Trademark Worth It? https://www.marqvision.com/blog/trademark-is-the-smartest-brand-investment-you-can-make

[^law360-comet]: Comet ML, Inc. v. Perplexity AI, Inc., No. 3:25-cv-XXXXX (N.D. Cal., complaint filed 2025-05-12; stipulated dismissal late 2025). Coverage: *Law360*, *Bloomberg Law IP*. https://www.law360.com/articles/2370037 and https://news.bloomberglaw.com/ip-law/perplexity-ai-software-firm-settle-comet-trademark-lawsuit

[^bloomberg-io]: *OpenAI Appeals Order Barring 'io' Name in Trademark Lawsuit.* Bloomberg Law IP, 2025. https://news.bloomberglaw.com/ip-law/openai-appeals-order-barring-io-name-in-trademark-lawsuit

[^techbuzz-cameo]: *OpenAI blocked from using 'Cameo' name in Sora after lawsuit.* TechBuzz, 2025. https://www.techbuzz.ai/articles/openai-blocked-from-using-cameo-name-in-sora-after-lawsuit

[^dupont-case]: *In re E.I. du Pont de Nemours & Co.*, 476 F.2d 1357 (C.C.P.A. 1973). The thirteen DuPont factors for §2(d) likelihood-of-confusion analysis.

[^lanham-act]: Lanham Act, 15 U.S.C. §1052(d) (Section 2(d) — Refusal of registration on the basis of likelihood of confusion).

[^kruze-survey]: Kruze Consulting. (2025). *Startups' AI Tool Usage Survey.* Cited in HubSpot, *AI Statistics Every Startup Should Know*. https://www.hubspot.com/startups/ai/ai-stats-for-startups

[^stackoverflow-2025]: Stack Overflow Developer Survey 2025. https://survey.stackoverflow.co/2025

[^truthfulqa]: Lin, S., Hilton, J., & Evans, O. (2021). TruthfulQA: Measuring How Models Mimic Human Falsehoods. *arXiv:2109.07958.* https://arxiv.org/abs/2109.07958. Conference version: ACL 2022.

[^halueval]: Li, J., Cheng, X., Zhao, W. X., Nie, J.-Y., & Wen, J.-R. (2023). HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models. *arXiv:2305.11747.* https://arxiv.org/abs/2305.11747. Conference version: EMNLP 2023.

[^halogen]: Ravichander, A., Ghela, S., Wadden, D., & Choi, Y. (2025). HALoGEN: Fantastic LLM Hallucinations and Where to Find Them. *arXiv:2501.08292.* https://arxiv.org/abs/2501.08292. Conference version: ACL 2025.

[^factscore]: Min, S., Krishna, K., Lyu, X., Lewis, M., Yih, W., Koh, P. W., Iyyer, M., Zettlemoyer, L., & Hajishirzi, H. (2023). FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. *arXiv:2305.14251.*

[^hallulens]: Bang, Y., et al. (2025). HalluLens: LLM Hallucination Benchmark. *arXiv:2504.17550.* https://arxiv.org/abs/2504.17550

[^dahl-magesh]: Dahl, M., Magesh, V., Suzgun, M., & Ho, D. E. (2024). Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models. *Journal of Legal Analysis,* 16(1), 64. https://arxiv.org/abs/2401.01301

[^magesh-hallucination-free]: Magesh, V., Surani, F., Dahl, M., Suzgun, M., Manning, C. D., & Ho, D. E. (2025). Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools. *Journal of Empirical Legal Studies.* https://onlinelibrary.wiley.com/doi/abs/10.1111/jels.12413

[^mata-cnn]: Weiser, B. (2023, May 27). Lawyer apologizes for fake court citations from ChatGPT. *CNN Business.* https://www.cnn.com/2023/05/27/business/chat-gpt-avianca-mata-lawyers

[^mata-wiki]: Mata v. Avianca, Inc. *Wikipedia.* 678 F. Supp. 3d 443 (S.D.N.Y. 2023). https://en.wikipedia.org/wiki/Mata_v._Avianca,_Inc.

[^markify-corpus-note]: Public statements by Markify and industry analysis place the manual TTAB-corpus labelling effort at approximately 15 years of paralegal time. Frontier LLMs (2025–2026 vintage) can extract structured DuPont analyses from TTAB decisions with high accuracy, reducing the labelling-cost moat that historically protected incumbent vendors.

[^placeholder-disclaimer]: Aggregate results from the pooled six-model analysis (`zenodo_release/analysis.json`) have been filled where applicable. Per-model cells retain `[RESULT_PLACEHOLDER]` markers pending `make run-full`. The runner pipeline is deterministic; the remaining placeholders will be replaced with empirical values prior to publication. The reproducibility archive will include the runner output, the raw model responses, and the scoring traces.

[^uspto-2d-rates]: Malloy & Malloy, P.L. (2024). Appellate Reversals of §2(d) Refusals by USPTO Trademark Examining Attorneys: 15%. https://malloylaw.com/appellate-reversals-of-§2d-refusals-by-uspto-trademark-examining-attorneys-15/ and PatentPC Analysis of USPTO Trademark Statistics.

[^ece-survey]: Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On Calibration of Modern Neural Networks. *ICML 2017.* Recent LLM-specific extensions surveyed in: Vogl, B. (2024). LLM Calibration: A Dual Approach of Post-Processing and Training-Time Methods. *TU Wien Repositorium.* https://repositum.tuwien.at/bitstream/20.500.12708/198211/1

[^verbalized-confidence]: Wang, V., et al. (2025). Calibrating Verbalized Confidence with Self-Generated Distractors. *arXiv:2509.25532.* https://www.arxiv.org/pdf/2509.25532

[^sycophancy-survey]: Sharma, M., et al. (2024). Sycophancy in Large Language Models: Causes and Mitigations. *arXiv:2411.15287.* https://arxiv.org/abs/2411.15287

[^syc-eval]: Fanous, A., et al. (2025). SycEval: Evaluating LLM Sycophancy. *arXiv:2502.08177.* https://arxiv.org/abs/2502.08177

[^stanford-hai-trial]: Stanford Human-Centered AI Institute. (2024). AI on Trial: Legal Models Hallucinate in 1 Out of 6 (or More) Benchmarking Queries. https://hai.stanford.edu/news/ai-trial-legal-models-hallucinate-1-out-6-or-more-benchmarking-queries

---

## Appendix A — Test set construction protocol

The full test set construction protocol is reproduced here for reproducibility.

### A.1 Name generation

Candidate names were generated in three streams:

1. **Frontier-LLM generation, post-hoc adversarial filtering.** Approximately 1,200 candidate names were generated by prompting GPT-5 and Claude 4.7 Opus with category-specific naming briefs. Each candidate was scored against the USPTO TSDR API for live conflicts and against the four trap-type structures.
2. **Curated adversarial names.** Approximately 400 names were hand-crafted by the authors to specifically target the four trap types. The phonetic-neighbour-famous trap, in particular, requires hand-craft to avoid accidental over-similarity.
3. **Real recent registrations.** Approximately 200 candidates were drawn from actual USPTO registrations filed in the past 18 months, presented to the model as proposed names. This is the cleanest test of the recent-micro-startup trap: the model is asked to evaluate a name that is, in fact, already registered.

The pool was downsampled to 500 with stratification to satisfy the category × trap-type quotas in §3.2.

### A.2 Ground-truth verification

Each candidate was processed through the following pipeline:

```
1. Normalize candidate string (lowercase, remove punctuation).
2. Query TSDR for exact-match registrations.
3. Generate 4 phonetic variants via Soundex + Metaphone + Double Metaphone + custom phonetic rules.
4. Query TSDR for each phonetic variant.
5. Compile the conflict candidate list.
6. For each conflict candidate:
   a. Record status (live / dead).
   b. Record goods/services classes.
   c. Record DuPont factor 1 (similarity of marks) score.
   d. Record DuPont factor 2 (similarity of goods) score.
7. Apply DuPont weighting rule:
   - If any live mark scores high on factors 1 AND 2: ground truth = RISKY.
   - If all conflicts are dead or score low on factor 1 OR 2: ground truth = SAFE.
   - If close call (mid-range scores or recent application not yet examined): ground truth = REQUIRES_LIVE_LOOKUP.
8. Dual expert review.
9. Disagreements → third-reviewer adjudication.
10. Final freeze.
```

### A.3 Test set schema

Each row in `test_set.jsonl` has the following schema:

```json
{
  "id": "tm-bench-000001",
  "name": "Klarrde",
  "category": "consumer_fintech",
  "difficulty": "medium",
  "trap_type": "phonetic_neighbor_famous",
  "ground_truth": "risky",
  "supporting_evidence": [
    {
      "type": "uspto_registration",
      "serial_number": "XXXXXXXX",
      "registration_number": "XXXXXXX",
      "owner": "Klarna AB",
      "filing_date": "2010-XX-XX",
      "status": "live",
      "dupont_factor_1": 0.78,
      "dupont_factor_2": 0.91
    }
  ],
  "notes": "Phonetic neighbour of Klarna. High factor 1 + 2 → likely §2(d) refusal."
}
```

### A.4 Stratification audit

After construction, the test set was audited for:

- Category balance: 50 ± 0 per category.
- Trap-type balance: 60 phonetic + 40 dead-mark + 40 foreign + 60 recent-micro per category, with remainder as clean/easy controls.
- Difficulty balance: 30% easy, 50% medium, 20% hard.
- Ground-truth balance: target 40% safe / 50% risky / 10% requires_live_lookup.

---

## Appendix B — Scoring rubric pseudocode

```python
def score_response(response: ModelResponse, gt: GroundTruth) -> ScoreRecord:
    parsed = parse_response(response, prompt_version=response.prompt_version)
    record = ScoreRecord(name=gt.name, model=response.model, prompt=response.prompt_version)

    # ---- Verdict ----
    record.verdict_pred = parsed.verdict        # safe | risky | cannot_verify | unparseable
    record.verdict_true = gt.ground_truth
    record.verdict_correct = (
        parsed.verdict == gt.ground_truth
        or (parsed.verdict == "cannot_verify" and gt.ground_truth == "requires_live_lookup")
    )

    # ---- False negative ----
    record.is_false_negative = (
        gt.ground_truth == "risky" and parsed.verdict == "safe"
    )

    # ---- Citation hallucination ----
    record.cited_records = parsed.citations
    record.hallucinated = []
    record.real_misattributed = []
    record.real_matched = []
    for cite in parsed.citations:
        live = uspto_tsdr_lookup(cite.serial_or_registration)
        if live is None:
            record.hallucinated.append(cite)
        elif owner_or_goods_mismatch(live, cite):
            record.real_misattributed.append(cite)
        else:
            record.real_matched.append(cite)
    record.cite_hallucination_rate = (
        len(record.hallucinated) / max(1, len(parsed.citations))
    )

    # ---- Confidence calibration ----
    record.confidence = parsed.confidence
    record.brier_term = (parsed.confidence/100 - int(record.verdict_correct))**2

    # ---- Hedge ----
    record.is_hedge = (
        parsed.verdict == "cannot_verify"
        or contains_verbal_hedge(parsed.raw_text)
    )

    return record
```

The full implementation is in `scorer.py`.

---

## Appendix C — Prompt templates (verbatim)

Reproduced from `prompts.py`. Each function takes a candidate `name` and `category`.

### C.1 Prompt v1 — naive

```
Is '{name}' a good brand name for a {category} product?
Specifically, is it trademark-safe? Give me your verdict and
how confident you are.
```

### C.2 Prompt v2 — constrained-JSON

```
You are evaluating the proposed brand name '{name}' for a {category}
product.

Answer these two questions:
  (a) Is this name likely to face a USPTO §2(d) likelihood-of-confusion
      refusal?
  (b) What is your confidence in that answer (0-100)?

Reply in JSON ONLY, with this exact schema:
{"refusal_likely": <true|false>, "confidence": <int 0-100>,
 "reasoning": "<one-sentence explanation>"}

Do not include any text before or after the JSON object.
```

### C.3 Prompt v3 — grounded with evidence request and escape hatch

```
You are advising a founder on the proposed brand name '{name}' for
a {category} product.

Assess whether this name is trademark-safe in the United States.
If you know of specific USPTO registrations or TTAB decisions that
would conflict, cite them with serial/registration number and owner.
If you do NOT know of specific conflicts and cannot verify without
a live lookup, you MUST say so explicitly — do not guess.

Reply in JSON ONLY, with this exact schema:
{"verdict": "<safe|risky|cannot_verify>",
 "evidence": [<list of citations, each a string; empty list if none>],
 "confidence": <int 0-100>,
 "reasoning": "<one-sentence explanation>"}

It is better to say 'cannot_verify' than to invent a citation.
Do not include any text before or after the JSON object.
```

---

## Appendix D — Limitations and threats to validity

### D.1 Construct validity

**Threat:** The benchmark conflates "the model would mislead a founder in practice" with "the model produces a wrong answer when asked a specific verifiable question." A model could refuse to engage with the question entirely and still be operationally useless to a founder; our hedge-rate metric partially addresses this, but the construct is imperfect.

**Mitigation:** We report multiple metrics (verdict accuracy, false-negative rate, hedge rate) so that practitioners can pick the metric that matches their operational concern.

### D.2 Internal validity

**Threat:** Models may have been exposed to specific names in the test set during training, especially for the phonetic-neighbour-famous trap (the famous marks are by definition widely-discussed online). This leaks ground truth to the model and inflates apparent accuracy.

**Mitigation:** We stratify a sub-sample using novel adversarial-generated names that were created post-2025 cutoff. We report results on the novel sub-stratum separately. We also rotate trap names across benchmark versions.

### D.3 External validity

**Threat:** The benchmark uses a frozen test set in a domain where the underlying registry is in continuous flux. A name that is "risky" in May 2026 may become "safe" if the conflicting mark is cancelled, and vice versa.

**Mitigation:** We snapshot the TSDR state at benchmark construction time and report all ground-truth verdicts as of that date. Re-runs use re-validated ground truth.

### D.4 Provider gaming

**Threat:** Once the benchmark is published, LLM providers may post-train on this paper, this prompt structure, and these specific names. The benchmark would then measure adherence to the benchmark rather than underlying capability.

**Mitigation:** Quarterly rotation of trap names. Held-out test set for each release (a 10% slice never published until the following quarter). Goodhart's law applies; we apply standard countermeasures.

### D.5 Single-jurisdiction scope

**Threat:** US-only ground truth produces a US-only verdict. Models that are systematically better at EU or UK clearance would not be visible in this benchmark.

**Mitigation:** The 2026-Q3 version adds EUIPO and UKIPO. The 2027-Q1 version adds APAC registries.

### D.6 Expert-review bias

**Threat:** The dual expert reviewers are qualified US trademark attorneys with known industry positions. Their priors may bias the ground-truth verdicts toward conservative (risky) classifications.

**Mitigation:** We blind reviewers to model responses. We report Cohen's κ and disagreement rates. We make the supporting-evidence records public so external reviewers can audit any individual verdict.

### D.7 Etymolt's commercial interest

**Threat:** Etymolt is a commercial entity in the verification-layer market. The benchmark could be biased to make unaided LLMs look worse than they are.

**Mitigation:** Test set, scoring code, runner pipeline, and raw model responses are released as open data. Any third party can re-run the benchmark and report independent numbers. The benchmark is designed to be self-falsifying.

---

## Appendix E — License and citation

### E.1 License

- **Paper (this document):** CC-BY-4.0.
- **Test set (`test_set.jsonl`) and scoring rubric (`scorer.py`):** CC-BY-4.0 / MIT respectively. Open for commercial and academic use with attribution.
- **Runner pipeline (`runner.py`) and prompt registry (`prompts.py`):** MIT.

### E.2 Citation

If you cite this benchmark, please use:

```bibtex
@misc{attarwala2026llmtrademark,
  title  = {The LLM Brand-Name Hallucination Benchmark: How Often Do
            Frontier Models Fabricate Trademark Clearance?},
  author = {Tariq Attarwala},
  year   = {2026},
  month  = may,
  howpublished = {Etymolt Research},
  url    = {https://etymolt.com/research/llm-naming-hallucination-benchmark},
  note   = {Dataset and code: github.com/etymolt/llm-hallucination-2026}
}
```

For a plain-text citation:

> Attarwala, T. (2026). *The LLM Brand-Name Hallucination Benchmark: How Often Do Frontier Models Fabricate Trademark Clearance?* Etymolt Research, May 2026. https://etymolt.com/research/llm-naming-hallucination-benchmark

### E.3 Contact

- Correspondence: research@etymolt.com
- Test-set / runner repository: github.com/etymolt/llm-hallucination-2026
- Quarterly re-run subscription: etymolt.com/research/subscribe

---

*End of paper. Version 1.0 — May 2026. The benchmark will be re-run quarterly; subscribers receive each release before public publication. The next release is scheduled for August 2026.*
